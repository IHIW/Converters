import json
import urllib
import os
import requests
from sys import exc_info
from boto3 import client
import xml.etree.ElementTree as ElementTree
from time import sleep

s3 = client('s3')

def parseNmdpXml(xmlText=None):
    validationFeedback=''

    #print('Parsing NMDP Xml Text:' + str(xmlText))

    documentRoot = ElementTree.fromstring(xmlText)

    #print('DocumentRoot:' + str(documentRoot))
    statusText = documentRoot.findall('status')[0].text

    isValid = statusText.upper()=='VALID'

    # Sometimes there is an error in the "message" node.
    messageNodes = documentRoot.findall('message')
    for messageNode in messageNodes:
        validationFeedback += messageNode.text+ '\n'

    validationErrorsNodes = documentRoot.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}errors')
    validationErrorNodes = validationErrorsNodes[0].findall('error')
    print('I found ' + str(len(validationErrorNodes)) + ' errors nodes.')

    validationErrors = {}

    for validationErrorNode in validationErrorNodes:
        lineNumber = str(validationErrorNode.get('line'))
        severity = str(validationErrorNode.get('severity'))
        description = str(validationErrorNode.text)

        # There is an error code (ex. cvc-complex-type.2.4.a) in the beginning of the description.
        errorCode = description.split(':')[0]
        #print('ErrorCode:' + str(errorCode))

        if errorCode in validationErrors.keys():
            validationErrors[errorCode]['count'] += 1
        else:
            errorInfo = {}
            errorInfo['lineNumber'] = lineNumber
            errorInfo['severity'] = severity
            errorInfo['description'] = description
            errorInfo['count'] = 1
            validationErrors[errorCode] = errorInfo

    for ruleID in sorted(list(validationErrors.keys())):
        errorInfo= validationErrors[ruleID]
        currentFeedbackText = ('*' + errorInfo['severity'] + ': Line ' + str(errorInfo['lineNumber']) + '\n' + errorInfo['description'])
        if errorInfo['count'] > 1:
            currentFeedbackText = currentFeedbackText + '\n\t(Document contains ' + str(errorInfo['count']) + ' errors like this.)'

        validationFeedback += currentFeedbackText + '\n'


    if(len(validationFeedback.strip()) < 1):
        validationFeedback='Valid\n'

    return isValid, validationFeedback

def nmdp_validation_handler(event, context):
    print('I found the nmdp validation handler.')
    # This is the AWS Lambda handler function.
    # Some default JSON to help with debugging, this will be replaced by the event payload
    uploadDetails = {}
    uploadDetails['is_valid'] = False
    uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the step function flowchart.'
    uploadDetails['validator_type'] = 'SCHEMA'

    xmlKey = None
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        #sleep(1)
        #print('This is the event:' + str(event)[0:50])

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
            print(' Sending upload file ' + str(fileName) + ' to the NMDP validator.')

            #  Send message to Service
            xmlResponse = validateNmdpPortal(xmlText=xmlText,xmlBucket=bucket,xmlKey=xmlKey)

            print('Xml Response Text: ' + str(xmlResponse))
            #  Parse Xml response.
            isValid, validationFeedback = parseNmdpXml(xmlText=xmlResponse)

            #   Set validation status of the upload object.
            uploadDetails['is_valid'] = isValid
            uploadDetails['validation_feedback'] = validationFeedback
            uploadDetails['validator_type'] = 'NMDP'

            return uploadDetails
        else:
            print('This is not an HML file (file type=' + str(fileType) + ') I will not validate it by NMDP.')

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        if (xmlKey is not None):
            validationStatus = 'Exception running NMDP Validation:' + str(e)
            uploadDetails['is_valid'] = False
            uploadDetails['validation_feedback'] = validationStatus
            uploadDetails['validator_type'] = 'NMDP'
        else:
            print('Failed setting the upload status because I could not identify the name of the xml file!')

    return uploadDetails

def validateNmdpPortal(xmlText=None, xmlBucket=None,xmlKey=None):
    try:
        print('Inside the NMPD Portal Validator, i was given xml text that looks like: ' + str(xmlText)[0:50])
        baseurl = 'https://qa-api.nmdp.org/hml_gw/v1/validate'
        headers = {
            'Content-Type': 'text/xml',
        }

        #print('I am passing this xmlText:' + str(xmlText))
        response = requests.post(url=baseurl, headers=headers, data=xmlText)
        print('I found this response:' + str(response.text))
        return(response.text)

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))
