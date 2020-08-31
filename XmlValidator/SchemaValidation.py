from boto3 import client
s3 = client('s3')
from pip._vendor.html5lib.treebuilders import etree
from sys import exc_info
import json
import urllib
import os

try:
    from Common.IhiwRestAccess import getUrl, getToken, setValidationStatus, getUploadByFilename
except Exception:
    from Common.IhiwRestAccess import getUrl, getToken, setValidationStatus, getUploadByFilename

def schema_validation_handler(event, context):
    print('I found the schema validation handler.')
    print('This is the event that was passed in:' + str(event))
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
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

        # Get the FileType from the upload object
        csvUploadObject = getUploadByFilename(token=token, url=url, fileName=xmlKey)
        if(csvUploadObject is None or 'type' not in csvUploadObject.keys() or csvUploadObject['type'] is None):
            print('Could not find the Upload object for upload ' + str(xmlKey) + '\nI will not validate it by schema.' )
            return None
        fileType = csvUploadObject['type']

        validationResults = None
        if(fileType == 'HML'):
            print('I will Validate Schema for this HML file:' + str(xmlKey))
            schemaText = getSchemaText(schemaFileName='hml-1.0.1.xsd')
            validationResults = validateAgainstSchema(schemaText=schemaText, xmlText=xmlText)
            print('ValidationResults:' + str(validationResults))
            setValidationStatus(uploadFileName=xmlKey, isValid=(validationResults == 'Valid'), validationFeedback=validationResults, url=url, token=token, validatorType='SCHEMA')
        elif(fileType == 'HAML'):
            if(fileExtension=='CSV'):
                print('File ' + str(xmlKey) + ' is a .csv file, I will not perform schema validation.')
                return None
            elif(fileExtension=='HAML' or fileExtension=='XML'):
                schemaText = getSchemaText(schemaFileName='IHIW-haml_version_w0_3_3.xsd')
                validationResults = validateAgainstSchema(schemaText=schemaText, xmlText=xmlText)
                print('ValidationResults:' + str(validationResults))
                setValidationStatus(uploadFileName=xmlKey, isValid=(validationResults == 'Valid'), validationFeedback=validationResults, url=url, token=token, validatorType='SCHEMA')
            else:
                print('The file' + str(xmlKey) + ' is a HAML file but I dont understand the extension. I will not perform schema validation.')
                return None
        else:
            print('The file' + str(xmlKey) + ' is neither HML or HAML, I will not perform schema validation.')
            return None

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def getSchemaText(schemaFileName=None):
    # This assumes the schema files are in the current working directory. That is how they are bundled for AWS.
    print('Getting Schema Text from this local File:' + str(schemaFileName))
    schemaFile=open(os.path.join(os.getcwd(),schemaFileName), 'r')
    schemaText=schemaFile.read()
    print('I found this text:' + str(schemaText))
    return schemaText

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
