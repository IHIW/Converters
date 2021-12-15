import json
import urllib
import os
import requests
from sys import exc_info
from boto3 import client
from time import sleep
import xml.etree.ElementTree as ElementTree
from requests.exceptions import ConnectionError

s3 = client('s3')


def parseMiringXml(xmlText=None):
    validationFeedback=''

    #print('Parsing MIRING Xml Text:' + str(xmlText))

    documentRoot = ElementTree.fromstring(xmlText)
    #print('DocumentRoot:' + str(documentRoot))

    # is Valid if the node <miring-compliant> has text "true" or "warnings"
    isHmlCompliant = documentRoot.findall('hml-compliant')[0].text in ['true', 'warnings']
    isMiringCompliant = documentRoot.findall('miring-compliant')[0].text in ['true', 'warnings']
    print('Is it HML compliant?' + str(isHmlCompliant))
    print('Is it MIRING compliant?' + str(isMiringCompliant))
    if(not isHmlCompliant):
        validationFeedback += 'Not compliant with HML Schema.\n'

    # Miring reports can have 3 feedback types:
    # I want to report Errors and Warnings in the feedback text, but ignore the info. That's probably too much info.
    # <miring-validation-errors>  <validation-warnings>, <validation-info>

    validationErrors={}
    # Loop Validation Errors
    validationErrorNodes = documentRoot.findall('miring-validation-errors')
    if(len(validationErrorNodes)>0):
        miringResultNodes = validationErrorNodes[0].findall('miring-result')
        #print('There are ' + str(len(miringResultNodes)) + ' miring result nodes under validation errors.')
        for miringResultNode in miringResultNodes:
            ruleID = str(miringResultNode.get('miring-rule-id'))

            # Cleanup if we have a bunch of the same error repeatably:
            if ruleID in validationErrors.keys():
                validationErrors[ruleID]['count'] += 1

            else:
                errorInfo = {}
                errorInfo['description'] = str(miringResultNode.findall('description')[0].text)
                errorInfo['solution'] = str(miringResultNode.findall('solution')[0].text)
                errorInfo['xPath'] = str(miringResultNode.findall('xpath')[0].text)
                errorInfo['count']=1
                validationErrors[ruleID] = errorInfo


    for ruleID in sorted(list(validationErrors.keys())):
        errorInfo = validationErrors[ruleID]
        currentFeedbackText = ('*MIRING violation, Rule:' + ruleID + ' at xpath location ' + str(errorInfo['xPath'])
            + '\n' + errorInfo['description']
            + '\n' + errorInfo['solution'])
        if errorInfo['count'] > 1:
            currentFeedbackText = currentFeedbackText + '\n\t(Document contains ' + str(errorInfo['count']) + ' errors like this.)'
        validationFeedback += currentFeedbackText + '\n'


    validationWarnings={}
    # Loop Validation Warnings
    validationWarningNodes = documentRoot.findall('validation-warnings')
    if(len(validationWarningNodes)>0):
        miringResultNodes = validationWarningNodes[0].findall('miring-result')
        print('There are ' + str(len(miringResultNodes)) + ' miring result nodes under validation warnings.')
        for miringResultNode in miringResultNodes:
            ruleID = str(miringResultNode.get('miring-rule-id'))

            # Cleanup if we have a bunch of the same error repeatably:
            if ruleID in validationWarnings.keys():
                validationWarnings[ruleID]['count'] += 1

            else:
                errorInfo = {}
                errorInfo['description'] = str(miringResultNode.findall('description')[0].text)
                errorInfo['solution'] = str(miringResultNode.findall('solution')[0].text)
                errorInfo['xPath'] = str(miringResultNode.findall('xpath')[0].text)
                errorInfo['count']=1
                validationWarnings[ruleID] = errorInfo

    for ruleID in sorted(list(validationWarnings.keys())):
        errorInfo= validationWarnings[ruleID]
        currentFeedbackText = (
            '*MIRING Warning, Rule:' + ruleID + ' at xpath location ' + str(errorInfo['xPath'])
            + '\n' + errorInfo['description']
            + '\n' + errorInfo['solution'])
        if errorInfo['count'] > 1:
            currentFeedbackText = currentFeedbackText + '\n\t(Document contains ' + str(errorInfo['count']) + ' warnings like this.)'
        validationFeedback += currentFeedbackText + '\n'

    if(len(validationFeedback.strip()) < 1):
        validationFeedback='Valid\n'

    # add a plug for this excellent validator
    validationFeedback += '\nPlease note that this document was uploaded successfully, and has NOT been rejected by the IHIW database.\nMIRING warnings are intended to be helpful indicators, and this document is likely very usable. \nMore info on MIRING rules at http://miring.b12x.org'

    return (isHmlCompliant and isMiringCompliant), validationFeedback


def miring_validation_handler(event, context):
    print('I found the Miring validation handler.')

    # Request timeout
    timeoutSeconds=30

    # Some default JSON to help with debugging, this will be replaced by the event payload
    uploadDetails = {}
    uploadDetails['is_valid'] = False
    uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the step function flowchart.'
    uploadDetails['validator_type'] = 'MIRING'

    xmlKey = None
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        #sleep(1)

        # Fetching the upload detail bundle from the step function payload
        if "Input" in event and "Payload" in event['Input']:
            uploadDetails = event['Input']['Payload']
        else:
            print(str(uploadDetails['validation_feedback']))
            return uploadDetails

        bucket = uploadDetails['bucket']
        # print('bucket:' + str(bucket))

        xmlKey = uploadDetails['file_name']

        # Filenames that have a space character need to be decoded.
        decodedKey = urllib.parse.unquote_plus(xmlKey)
        print('decodedKey:' + str(decodedKey))
        xmlKey = decodedKey

        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read()

        # Determine file extension.
        # I read an internet comment that this will treat the file as having no extension if it indeed does not have an extension.
        fileName, fileExtension = os.path.splitext(str(xmlKey).upper())
        fileExtension = fileExtension.replace('.','')
        print('This file has the extension:' + fileExtension)

        fileType = uploadDetails['upload_type']

        validationResults = None
        if(fileType == 'HML'):
            print(' Sending upload file ' + str(fileName) + ' to the miring validator.')

            # Exception handling to handle a timeout error
            try:
                #  Send message to Service
                xmlResponse = validateMiring(xmlText=xmlText,xmlBucket=bucket,xmlKey=xmlKey, timeoutSeconds=timeoutSeconds)

                #print('Xml Response Text: ' + str(xmlResponse))
                #  Parse Xml response.
                isValid, validationFeedback = parseMiringXml(xmlText=xmlResponse)
                print('Is file valid?' + str(isValid))

            except ConnectionError as e:
                print('Connection error occurred: ' + str(e))
                isValid = False
                validationFeedback = 'Connection Error during MIRING validation:' + str(e)
            except Exception as e:
                print('Exception occurred during MIRING Validation.')
                isValid = False
                validationFeedback = 'Error during validation:' + str(e)

            #   5) Set validation status of the upload object.
            uploadDetails['is_valid'] = isValid
            uploadDetails['validation_feedback'] = validationFeedback
            uploadDetails['validator_type'] = 'MIRING'

            return uploadDetails
        else:
            print('This is not an HML file (file type=' + str(fileType) + ') I will not validate it by MIRING.')

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        if (xmlKey is not None):
            validationStatus = 'Exception running MIRING Validation:' + str(e)
            uploadDetails['is_valid'] = False
            uploadDetails['validation_feedback'] = validationStatus
            uploadDetails['validator_type'] = 'MIRING'
        else:
            print('Failed setting the upload status because I could not identify the name of the xml file!')


    return uploadDetails


def validateMiring(xmlText=None, xmlBucket=None,xmlKey=None, timeoutSeconds=None):
    try:
        print('Inside the MIRING Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        fullUrl = 'http://miring.b12x.org/validator/ValidateMiring'
        xmlText=xmlText.decode()
        print('Done decoding text')

        headers = {
            'Content-Type': 'text/xml',
        }

        body = {
            'xml': xmlText
        }

        print('Sending Request....timeout=' + str(timeoutSeconds))
        response= requests.post(url=fullUrl, headers=headers, data=body, timeout=timeoutSeconds)   #encodedJsonData
        print('Response:' + str(response))
        return(response.text)
    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        raise e

