import json
import urllib
import os
#import requests
from sys import exc_info
from boto3 import client


try:
    import Common.IhiwRestAccess as IhiwRestAccess
    import Common.Validation as Validation
    import Common.ParseXml as ParseXml
except Exception as e:
    import IhiwRestAccess
    import Validation
    import ParseXml

s3 = client('s3')






def hml_parser_handler(event, context):
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
            print('Could not find the Upload object for upload ' + str(xmlKey) + '\nI will not continue.' )
            return None
        fileType = hmlUploadObject['type']

        validationResults = None
        if(fileType == 'HML'):
            print('This is an HML file, I will parse and validate it.')

            hmlId, sampleIds, glStrings = ParseXml.parseXml(xmlText = xmlText)

            isGlStringsValid, glStringValidationFeedback = Validation.validateGlStrings(glStrings=glStrings)
            IhiwRestAccess.setValidationStatus(uploadFileName=xmlKey, isValid=isGlStringsValid
                 , validationFeedback=glStringValidationFeedback, url=url, token=token, validatorType='GLSTRING')


        else:
            print('This is not an HML file (file type=' + str(fileType) + ') I will not parse it.')

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        if (xmlKey is not None):
            url = IhiwRestAccess.getUrl()
            token = IhiwRestAccess.getToken(url=url)
            validationStatus = 'Exception Parsing HML file:' + str(e)
            print('I will try to set the status.')
            IhiwRestAccess.setValidationStatus(uploadFileName=xmlKey, isValid=False, validationFeedback=validationStatus, url=url,
                                token=token, validatorType='GLSTRING')
        else:
            print('!!!!Failed setting the upload status because I could not identify the name of the xml file.')
        return str(e)
