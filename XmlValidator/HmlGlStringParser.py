import urllib
from sys import exc_info
from boto3 import client
from time import sleep
import xml.etree.ElementTree as ElementTree

try:
    import Common.IhiwRestAccess as IhiwRestAccess
    import Common.Validation as Validation
except Exception as e:
    import IhiwRestAccess
    import Validation

s3 = client('s3')

def hml_parser_handler(event, context):
    print('I am in the GLString Parser.')

    # Some default JSON to help with debugging, this will be replaced by the event payload
    uploadDetails = {}
    uploadDetails['is_valid'] = False
    uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the step function flowchart.'
    uploadDetails['validator_type'] = 'GLSTRING'

    # This is the AWS Lambda handler function.
    xmlKey = None
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        sleep(1)
        print('This is the event:' + str(event)[0:50])

        # Fetching the upload detail bundle from the step function payload
        if "Input" in event and "Payload" in event['Input']:
            uploadDetails = event['Input']['Payload']
            uploadDetails['validator_type'] = 'GLSTRING'
        else:
            print(str(uploadDetails['validation_feedback']))
            return uploadDetails

        bucket = uploadDetails['bucket']
        xmlKey = uploadDetails['file_name']
        fileType = uploadDetails['upload_type']

        # Filenames that have a space character need to be decoded.
        decodedKey = urllib.parse.unquote_plus(xmlKey)
        #print('decodedKey:' + str(decodedKey))
        xmlKey = decodedKey

        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read()

        if(fileType == 'HML'):
            print('This is an HML file, I will parse and validate it.')

            glStrings=[]
            documentRoot = ElementTree.fromstring(xmlText)

            for glStringNode in documentRoot.iter("*"):
                # print('Element Tag:' + str(element.tag))
                if (str(glStringNode.tag) == str('{http://schemas.nmdp.org/spec/hml/1.0.1}glstring')):

                    print('glStringNode:' + str(glStringNode))
                    glStringText = glStringNode.text

                    if(glStringText is not None and len(glStringText.strip())>1):
                        glStrings.append(glStringText.strip())
                        print('added glString:' + str(glStringText.strip()))
                else:
                    #print('Not glStringNode: ' + str(glStringNode))
                    pass

            uploadDetails['is_valid'], uploadDetails['validation_feedback'] = Validation.validateGlStrings(glStrings=glStrings)
            uploadDetails['validation_feedback'] = str(len(glStrings)) + ' GLSTRINGs found: ' +  uploadDetails['validation_feedback']

            return uploadDetails

        else:
            print('This is not an HML file (file type=' + str(fileType) + ') I will not parse it.')
            uploadDetails['is_valid'] = False
            uploadDetails['validation_feedback'] = ('This is not an HML file (file type=' + str(fileType) + ') I will not parse it.')

            return uploadDetails

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        uploadDetails['is_valid'] = False
        uploadDetails['validation_feedback'] = 'Exception Parsing HML file:' + str(e) + '\n' + str(exc_info())

        return uploadDetails

    return uploadDetails
