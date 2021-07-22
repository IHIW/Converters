from boto3 import client
s3 = client('s3')
from lxml import etree
from sys import exc_info
import urllib
import os
from time import sleep

def schema_validation_handler(event, context):
    print('I found the schema validation handler.')
    print('This is the event that was passed in:' + str(event))

    # Some default JSON to help with debugging, this will be replaced by the event payload
    uploadDetails = {}
    uploadDetails['is_valid'] = False
    uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the step function flowchart.'
    uploadDetails['validator_type'] = 'SCHEMA'

    xmlKey = None
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        # sleep(1)

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


        if(fileType == 'HML'):
            print('I will Validate Schema for this HML file:' + str(xmlKey))
            schemaText = getSchemaText(schemaFileName='hml-1.0.1.xsd')
            validationResults = validateAgainstSchema(schemaText=schemaText, xmlText=xmlText)
            print('ValidationResults:' + str(validationResults))

            uploadDetails['is_valid'] = (validationResults == 'Valid')
            uploadDetails['validation_feedback'] = validationResults
            uploadDetails['validator_type'] = 'SCHEMA'
        elif(fileType == 'HAML'):
            if(fileExtension=='CSV'):
                print('File ' + str(xmlKey) + ' is a .csv file, I will not perform schema validation.')
                return None
            elif(fileExtension=='HAML' or fileExtension=='XML'):
                schemaText = getSchemaText(schemaFileName='IHIW-haml_version_w0_3_3.xsd')
                validationResults = validateAgainstSchema(schemaText=schemaText, xmlText=xmlText)
                print('ValidationResults:' + str(validationResults))

                uploadDetails['is_valid'] = (validationResults == 'Valid')
                uploadDetails['validation_feedback'] = validationResults
                uploadDetails['validator_type'] = 'SCHEMA'

            else:
                print('The file' + str(xmlKey) + ' is a HAML file but I dont understand the extension. I will not perform schema validation.')
                return None
        else:
            print('The file' + str(xmlKey) + ' is neither HML or HAML, I will not perform schema validation.')
            return None



    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        if (xmlKey is not None):
            validationStatus = 'Exception running SCHEMA Validation:' + str(e)
            print('I will try to set the status.')

            uploadDetails['is_valid'] = False
            uploadDetails['validation_feedback'] = validationStatus
            uploadDetails['validator_type'] = 'SCHEMA'

        else:
            print('Failed setting the upload status because I could not identify the name of the xml file.')
        return str(e)

    return uploadDetails

def getSchemaText(schemaFileName=None):
    # This assumes the schema files are in the current working directory. That is how they are bundled for AWS.
    print('Getting Schema Text from this local File:' + str(schemaFileName))
    schemaFile=open(os.path.join(os.getcwd(),schemaFileName), 'r')
    schemaText=schemaFile.read()
    #print('I found this text:' + str(schemaText))
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
