import json
import urllib
import yaml
import ast
import os
import boto3
import requests
from sys import exc_info
from boto3 import client

from IhiwRestAccess import getUrl, getToken, setValidationStatus

s3 = client('s3')


def miring_validation_handler(event, context):
    print('I found the schema validation handler.')
    # This is the AWS Lambda handler function.
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
        url = getUrl()
        token = getToken(url=url)
        #validation steps
        #   0) Check that this is a file with the HML file type. Get the upload and check it, can't just check the name of the file

        #   1) Send message to Service
        xmlResponse =  validateMiring(xmlText=xmlText,xmlBucket=bucket,xmlKey=xmlKey)

        #   2) Interpret the response? Parse the xml response somehow.

        #   3) Determine if file is valid or not~

        isValid = False

        print('Assuming not valid. ~~~~My text is~~~~~: ' + str(xmlResponse))

        #   4) Create a feedback text
        feedbackText = 'Logic needed to create a nice feedback text'

        #   5) Set validation status of the upload object.
        setValidationStatus(uploadFileName=xmlKey, isValid=isValid
                            , validationFeedback=feedbackText, url=url, token=token, validatorType='Miring')

        # It's not really necessary to return anything...but AWS likes to see if the lambda was successful.
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda, we ran the validation handler successfully.')

        }

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


def validateMiring(xmlText=None, xmlBucket=None,xmlKey=None):
    # TODO: there's nothing here yet. send a message to miring.b12x.org and get a response.
    try:
        print('Inside the MIRING Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])

        #$ curl -X POST --data-urlencode 'xml[]=<hml>...</hml>' http://miring.b12x.org/validator/ValidateMiring/

        fullUrl = 'http://miring.b12x.org/validator/ValidateMiring'

        headers = {
            'Content-Type': 'text/xml',
        }

        body = 'xml[]='+xmlText.decode()
        #body = {
        #    'xml[]': xmlText.decode()
        #}

        bucketname = str(xmlBucket)
        filename = str(xmlKey)
        s3 = boto3.resource('s3')
        data = s3.Object(bucketname, filename).get()['Body'].read()
        jsonDump = json.dumps(body)
        encodedJsonData = str(jsonDump).encode('utf-8')
        response= requests.post(url=fullUrl, headers=headers, data=data)   #encodedJsonData
        return('Miring validation Results are the following: ' + response.text)
    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))

