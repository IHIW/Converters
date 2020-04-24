from boto3 import client
s3 = client('s3')
import urllib
import json
from sys import exc_info

from SchemaValidation import validateAgainstSchema
from MiringValidation import validateMiring
from NmdpPortalValidation import validateNmdpPortal
from ValidationCommon import getUrl, getToken, setValidationStatus


def schema_validation_handler(event, context):
    print('I found the schema validation handler.')
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        content = json.loads(event['Records'][0]['Sns']['Message'])

        bucket = content['Records'][0]['s3']['bucket']['name']
        xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read().decode()

        # Get the Schema file
        schemaKey = 'schema/hml-1.0.1.xsd'
        schemaFileObject = s3.get_object(Bucket=bucket, Key=schemaKey)
        schemaText = schemaFileObject["Body"].read().decode()

        # Perform the validation.
        validationResults = validateAgainstSchema(schemaText=schemaText, xmlText=xmlText)
        print('ValidationResults:' + str(validationResults))

        # Request the management app to update the validation status for this file.
        url = getUrl()
        token=getToken(url=url)

        setValidationStatus(uploadFileName=xmlKey, isValid=(validationResults=='Valid'), validationFeedback=validationResults, url=url, token=token)

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def miring_validation_handler(event, context):
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        content = json.loads(event['Records'][0]['Sns']['Message'])

        bucket = content['Records'][0]['s3']['bucket']['name']
        xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read().decode()


        # Perform the validation.
        validationResults = validateMiring(xmlText=xmlText)

        print('results of miring validation:' + str(validationResults))

        # Request the management app to update the validation status for this file.
        #url = getUrl()
        #token=getToken(url=url)

        #setValidationStatus(uploadFileName=xmlKey, isValid=(validationResults=='Valid'), validationFeedback=validationResults, url=url, token=token)

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)