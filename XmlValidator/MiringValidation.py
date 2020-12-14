import json
import urllib
import os
import requests
from sys import exc_info
from boto3 import client
import xml.etree.ElementTree as ElementTree

try:
    import IhiwRestAccess
except Exception:
    import Common.IhiwRestAccess

s3 = client('s3')


def parseMiringXml(xmlText=None):
    validationFeedback=''

    print('Parsing MIRING Xml Text:' + str(xmlText))

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

    # Loop Validation Errors
    validationErrorNodes = documentRoot.findall('miring-validation-errors')
    if(len(validationErrorNodes)>0):
        miringResultNodes = validationErrorNodes[0].findall('miring-result')
        #print('There are ' + str(len(miringResultNodes)) + ' miring result nodes under validation errors.')
        for miringResultNode in miringResultNodes:
            ruleID = str(miringResultNode.get('miring-rule-id'))
            description = str(miringResultNode.findall('description')[0].text)
            solution = str(miringResultNode.findall('solution')[0].text)
            xPath = str(miringResultNode.findall('xpath')[0].text)
            currentFeedbackText = ('MIRING violation, Rule:' + ruleID + ' at xpath location ' + str(xPath)
                + '\n' + description
                + '\n' + solution)

            validationFeedback += currentFeedbackText + '\n'

    # Loop Validation Warnings
    validationWarningNodes = documentRoot.findall('validation-warnings')
    if(len(validationWarningNodes)>0):
        miringResultNodes = validationWarningNodes[0].findall('miring-result')
        print('There are ' + str(len(miringResultNodes)) + ' miring result nodes under validation warnings.')
        for miringResultNode in miringResultNodes:
            ruleID = str(miringResultNode.get('miring-rule-id'))
            description = str(miringResultNode.findall('description')[0].text)
            solution = str(miringResultNode.findall('solution')[0].text)
            xPath = str(miringResultNode.findall('xpath')[0].text)
            currentFeedbackText = ('MIRING Warning, Rule:' + ruleID + ' at xpath location ' + str(xPath)
                + '\n' + description
                + '\n' + solution)

            validationFeedback += currentFeedbackText + '\n'
    if(len(validationFeedback.strip()) < 1):
        validationFeedback='Valid\n'

    # add a plug for this excellent validator
    validationFeedback += 'More info on MIRING rules at http://miring.b12x.org'

    return (isHmlCompliant and isMiringCompliant), validationFeedback


def miring_validation_handler(event, context):
    print('I found the schema validation handler.')
    # This is the AWS Lambda handler function.
    xmlKey = None
    try:
        print('This is the event:' + str(event)[0:50])

        content = json.loads(event['Records'][0]['Sns']['Message'])

        bucket = content['Records'][0]['s3']['bucket']['name']
        xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read()

        # Determine file extension.
        # I read an internet comment that this will treat the file as having no extension if it indeed does not have an extension.
        fileName, fileExtension = os.path.splitext(str(xmlKey).upper())
        fileExtension = fileExtension.replace('.','')
        print('This file has the extension:' + fileExtension)

        # Get access stuff from the REST Endpoints
        url = IhiwRestAccess.getUrl()
        token = IhiwRestAccess.getToken(url=url)

        hmlUploadObject = IhiwRestAccess.getUploadByFilename(token=token, url=url, fileName=xmlKey)
        if(hmlUploadObject is None or 'type' not in hmlUploadObject.keys() or hmlUploadObject['type'] is None):
            print('Could not find the Upload object for upload ' + str(xmlKey) + '\nI will not validate by MIRING..' )
            return None
        fileType = hmlUploadObject['type']

        validationResults = None
        if(fileType == 'HML'):
            print(' Sending upload file ' + str(fileName) + ' to the miring validator.')

            #  Send message to Service
            xmlResponse = validateMiring(xmlText=xmlText,xmlBucket=bucket,xmlKey=xmlKey)

            print('Xml Response Text: ' + str(xmlResponse))
            #  Parse Xml response.
            isValid, validationFeedback = parseMiringXml(xmlText=xmlResponse)

            #   5) Set validation status of the upload object.
            IhiwRestAccess.setValidationStatus(uploadFileName=xmlKey, isValid=isValid
                 , validationFeedback=validationFeedback, url=url, token=token, validatorType='MIRING')

            # It's not really necessary to return anything...but AWS likes to see if the lambda was successful.
            return {
                'statusCode': 200,
                'body': json.dumps('MIRING Validation performed successfully.')

            }
        else:
            print('This is not an HML file (file type=' + str(fileType) + ') I will not validate it by MIRING.')

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        if (xmlKey is not None):
            url = IhiwRestAccess.getUrl()
            token = IhiwRestAccess.getToken(url=url)
            validationStatus = 'Exception running MIRING Validation:' + str(e)
            print('I will try to set the status.')
            IhiwRestAccess.setValidationStatus(uploadFileName=xmlKey, isValid=False, validationFeedback=validationStatus, url=url,
                                token=token, validatorType='MIRING')
        else:
            print('Failed setting the upload status because I could not identify the name of the xml file.')
        return str(e)


def validateMiring(xmlText=None, xmlBucket=None,xmlKey=None):
    try:
        print('Inside the MIRING Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        fullUrl = 'http://miring.b12x.org/validator/ValidateMiring'

        headers = {
            'Content-Type': 'text/xml',
        }

        body = {
            'xml': xmlText.decode()
        }

        response= requests.post(url=fullUrl, headers=headers, data=body)   #encodedJsonData
        return(response.text)
    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))

