import json
import urllib
import os
import requests
from sys import exc_info
from boto3 import client
import xml.etree.ElementTree as ElementTree

try:
    import Common.IhiwRestAccess
except Exception as e:
    import IhiwRestAccess

s3 = client('s3')

def parseNmdpXml(xmlText=None):
    validationFeedback=''

    print('Parsing NMDP Xml Text:' + str(xmlText))

    documentRoot = ElementTree.fromstring(xmlText)

    print('DocumentRoot:' + str(documentRoot))
    statusText = documentRoot.findall('status')[0].text

    isValid = statusText.upper()=='VALID'

    # Sometimes there is an error in the "message" node.
    messageNodes = documentRoot.findall('message')
    for messageNode in messageNodes:
        validationFeedback += messageNode.text+ '\n'

    validationErrorsNodes = documentRoot.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}errors')
    validationErrorNodes = validationErrorsNodes[0].findall('error')
    print('I found ' + str(len(validationErrorNodes)) + ' errors nodes.')


    for validationErrorNode in validationErrorNodes:
        lineNumber = str(validationErrorNode.get('line'))
        severity = str(validationErrorNode.get('severity'))
        description = str(validationErrorNode.text)

        currentFeedbackText = (severity + ': Line ' + str(lineNumber)
            + '\n' + description)

        validationFeedback += currentFeedbackText + '\n'

    if(len(validationFeedback.strip()) < 1):
        validationFeedback='Valid\n'

    return isValid, validationFeedback

def nmdp_validation_handler(event, context):
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
            print('Could not find the Upload object for upload ' + str(xmlKey) + '\nI will not validate by NMDP..' )
            return None
        fileType = hmlUploadObject['type']

        validationResults = None
        if(fileType == 'HML'):
            print(' Sending upload file ' + str(fileName) + ' to the NMDP validator.')

            #  Send message to Service
            xmlResponse = validateNmdpPortal(xmlText=xmlText,xmlBucket=bucket,xmlKey=xmlKey)

            print('Xml Response Text: ' + str(xmlResponse))
            #  Parse Xml response.
            isValid, validationFeedback = parseNmdpXml(xmlText=xmlResponse)

            #   5) Set validation status of the upload object.
            IhiwRestAccess.setValidationStatus(uploadFileName=xmlKey, isValid=isValid
                 , validationFeedback=validationFeedback, url=url, token=token, validatorType='NMDP')

            # It's not really necessary to return anything...but AWS likes to see if the lambda was successful.
            return {
                'statusCode': 200,
                'body': json.dumps('NMDP Validation performed successfully.')

            }
        else:
            print('This is not an HML file (file type=' + str(fileType) + ') I will not validate it by NMDP.')

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        if (xmlKey is not None):
            url = IhiwRestAccess.getUrl()
            token = IhiwRestAccess.getToken(url=url)
            validationStatus = 'Exception running NMDP Validation:' + str(e)
            print('I will try to set the status.')
            IhiwRestAccess.setValidationStatus(uploadFileName=xmlKey, isValid=False, validationFeedback=validationStatus, url=url,
                                token=token, validatorType='NMDP')
        else:
            print('Failed setting the upload status because I could not identify the name of the xml file.')
        return str(e)

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
