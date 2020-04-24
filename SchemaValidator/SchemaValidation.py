from boto3 import client
s3 = client('s3')
from lxml import etree
from sys import exc_info
import json
import urllib
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
        xmlText = xmlFileObject["Body"].read()

        # Get the Schema file
        schemaKey = 'schema/hml-1.0.1.xsd'
        schemaFileObject = s3.get_object(Bucket=bucket, Key=schemaKey)
        schemaText = schemaFileObject["Body"].read()

        # Perform the validation.
        validationResults = validateAgainstSchema(schemaText=schemaText, xmlText=xmlText)
        print('ValidationResults:' + str(validationResults))

        # Request the management app to update the validation status for this file.
        url = getUrl()
        token=getToken(url=url)

        setValidationStatus(uploadFileName=xmlKey, isValid=(validationResults=='Valid'), validationFeedback=validationResults, url=url, token=token, validatorType='SCHEMA')

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


def validateAgainstSchema(schemaText=None, xmlText=None):
    try:
        # Validate XML against Schema.
        schemaTree = etree.XMLSchema(etree.XML(schemaText))
        xmlParser = etree.XMLParser(schema=schemaTree)
        try:
            xmlTree = etree.fromstring(xmlText, xmlParser)
            # If we get this far, the XML has validated successfully.
            return ('Valid')
        except etree.XMLSyntaxError as err:
            return ('Invalid:\t' + str(err))

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))
