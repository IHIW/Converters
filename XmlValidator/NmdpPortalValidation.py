import json
import urllib
from sys import exc_info
from boto3 import client

from Common.IhiwRestAccess import getUrl, getToken, setValidationStatus

s3 = client('s3')


def nmdp_validation_handler(event, context):
    print('I found the schema validation handler.')
    print('This is the event that was passed in:' + str(event))
    # This is the AWS Lambda handler function.
    try:
        print('This is bens message in the handler!!!!!!')
        print('This is the event:' + str(event))

        # Get the uploaded file.
        content = json.loads(event['Records'][0]['Sns']['Message'])
        bucket = content['Records'][0]['s3']['bucket']['name']
        print('I just found this bucket name:' + str(bucket))
        xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        print('I found the XML Key:' + str(xmlKey))
        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read()
        print('I found this xml text:' + str(xmlText))


        url = getUrl()
        token = getToken(url=url)
        # TODO: I should do the validation here.
        #   0) Check that this is a file with the HML file type. Get the upload and check it, can't just check the name of the file

        #   1) Send message to Service
        xmlResponse =  validateNmdpPortal(xmlText=xmlText)

        #   2) Interpret the response? Parse the xml response somehow.

        #   3) Determine if file is valid or not
        isValid = False

        #   4) Create a feedback text
        feedbackText = 'Nmdp Validator should be implemented first, I dont have feedback yet.'

        #   5) Set validation status of the upload object.
        setValidationStatus(uploadFileName=xmlKey, isValid=isValid
            , validationFeedback=feedbackText, url=url, token=token, validatorType='NMDP')

        # It's not really necessary to return anything...but AWS likes to see if the lambda was successful.
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda, we ran the validation handler successfully.')

        }

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def validateNmdpPortal(xmlText=None):
    # TODO: there's nothing here yet. send a message to the NMDP portal and parse response
    try:
        print('Inside the NMPD Portal Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        return('NMPD validation Results')

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))

