import json
import urllib
import yaml
import ast
import boto3
import requests
from sys import exc_info
from boto3 import client

from Common.IhiwRestAccess import getUrl, getToken, setValidationStatus

s3 = client('s3')


def miring_validation_handler(event, context):
    print('I found the schema validation handler.')
    # This is the AWS Lambda handler function.
    try:
        print('This is the event:' + str(event)[0:50])

        # Get the uploaded file.
        con = json.dumps(event['Records'][0])
        print('the content is: ', con)
        content = json.loads(con)
        bucket_name = event['Records'][0]['s3']['bucket']['name']
        file_key = event['Records'][0]['s3']['object']['key']
        xmlKey = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        xmlBucket = urllib.parse.unquote_plus(event['Records'][0]['s3']['bucket']['name'], encoding='utf-8')
        xmlFileObject = s3.get_object(Bucket=bucket_name, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read()



        url = getUrl()
        token = getToken(url=url)
        #validation steps
        #   0) Check that this is a file with the HML file type. Get the upload and check it, can't just check the name of the file

        #   1) Send message to Service
        xmlResponse =  validateMiring(xmlText=xmlText,xmlBucket=xmlBucket,xmlKey=xmlKey)

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

        body = {
            'xml': xmlText.decode()
        }

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

def setValidationStatus(uploadFileName=None, isValid=None, validationFeedback=None, validatorType=None, token=None, url=None):
    print('Setting upload validation status,\t' + 'uploadFileName=' + str(uploadFileName) + '\tvalidatorType=' + str(validatorType) + '\tisValid=' + str(isValid) + '\tvalidationFeedback=(' + str(validationFeedback) + ')\turl=' + str(url))
    if (uploadFileName is None or isValid is None or validationFeedback is None or validatorType is None):
        print('Missing data, cannot set validation status:'
              + '\tuploadFileName:' + str(uploadFileName)
              + '\tisValid:' + str(isValid)
              + '\tvalidationFeedback:'
              + str(validationFeedback)
              + '\tvalidatorType:' + str(validatorType))
        return False
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)
    if(validatorType is None):
        validatorType = 'UNKNOWN'
    if (validationFeedback is None or len(str(validationFeedback))==0):
        validationFeedback = 'No Feedback Provided.'
    try:
        print ('Setting ' + str(validatorType) + ' validation status ' + str(isValid) + ' for file ' + str(uploadFileName))

        fullUrl = str(url) + '/api/uploads/setvalidation'

        maxValidationLength=10000
        if(len(validationFeedback) > maxValidationLength):
            print('Warning, validator feedback length is greater than the maximum (' + str(maxValidationLength)
                  + ') so I will truncate the feedback to ' + str(maxValidationLength) + ' characters.')
            validationFeedback=validationFeedback[0:maxValidationLength]

        body = {
            'valid': isValid
            , 'validationFeedback': validationFeedback
            , 'validator': validatorType
            , 'upload': {
                'fileName': uploadFileName
            }
        }

        print('body:' + str(body))
        encodedJsonData = str(json.dumps(body)).encode('utf-8')
        updateRequest = requests.post(url=fullUrl, headers={'Content-Type':'application/json',
                                                            'Authorization': 'Bearer {}'.format('Bearer ' + token)}, data=encodedJsonData)
        print(' This is the response: ' + updateRequest.text[0:50])
        responseData  = updateRequest.text
        if(responseData is None or len(responseData) < 1):
            print('updateValidationStatus returned an empty response!')
            return False
        response=json.loads(responseData)
        print(*response.items(), sep='\n')
        # The response contains the saved data, if successful. If the response matches what we expect it was a success.
        # Probably need to make this more robust.
        #if(str(response['valid'])==str(isValid)  and str(response['validationFeedback'])==str(validationFeedback)):
        #    return True
        if(response['status'] ==402):
            return True
        else:
            print('Could not set validation status, response:\n' + str(response))
            return False
    except SyntaxError as e:
        print('Syntax error when parsing response from request:\n' + str(e) + '\n' + str(exc_info()))
        return False
    except urllib.error.HTTPError as e:
        print('HTTP error when setting validation status for upload file ' + str(uploadFileName) + ' : ' + str(e))
        return False
    except Exception as e:
        print('Error when updating validation status:\n' + str(e) + '\n' + str(exc_info()))
        return False


