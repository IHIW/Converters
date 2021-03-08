import boto3
import urllib
from ihiw_converter import Converter
from IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadIfExists

import json
from time import sleep
import io

from Common.IhiwRestAccess import getUploadsByParentId, deleteUpload

''' <summary>
    /// Handler was converted to Python by Teresa Tavella
    /// University of Bologna
    /// https://github.com/TessaTi/IHIW_Converter_py
 '''

def csv_to_haml_lambda_handler(event, context):
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        sleep(1)

        content = json.loads(event['Records'][0]['Sns']['Message'])
        print('Content:' + str(content))
        bucket = content['Records'][0]['s3']['bucket']['name']

        print('bucket:' + str(bucket))
        csvKey = content['Records'][0]['s3']['object']['key']

        # Filenames that have a space character need to be decoded.
        decodedKey = urllib.parse.unquote_plus(csvKey)
        print('decodedCsvKey:' + str(decodedKey))
        csvKey = decodedKey

        if not (str(csvKey[len(csvKey)-4:len(csvKey)]).lower() in ['.csv','.tsv']):
            print('Upload ' + str(csvKey) + ' is not a .csv file. I will not convert it to HAML.')
            return None

        # Login token for rest methods...
        print('Getting a login token and URL...')
        (user, password) = getCredentials(configFileName='validation_config.yml')
        url = getUrl(configFileName='validation_config.yml')
        token = getToken(user=user, password=password, url=url)

        # Wrapper, exception handling
        try:
            csvUploadObject = getUploadIfExists(token=token, url=url, fileName=csvKey)
            if(csvUploadObject is None or 'type' not in csvUploadObject.keys() or csvUploadObject['type'] is None):
                print('Could not find the Upload object for upload ' + str(csvKey) + '\nI will not convert it to HAML.' )
                return None
            elif (csvUploadObject['type'] != 'ANTIBODY_CSV'):
                print('The upload ' + str(csvKey) + ' is type ' + csvUploadObject['type'] + '. I will not convert it to HAML.')
                return None

            s3 = boto3.client('s3')

            # Get the CSV object from S3
            csvFileObject = s3.get_object(Bucket=bucket, Key=csvKey)
            print('csvFileObject:' + str(csvFileObject))
            #csvText = csvFileObject["Body"].read().decode()
            #print('csvFileText:' + str(csvText))
            s3ObjectBytestream = io.BytesIO(csvFileObject['Body'].read())
            print('s3 object:' + str(s3ObjectBytestream))

            manufacturer=''
            xmlOutput = (csvKey.replace('ANTIBODY_CSV','HAML') + '.haml')
            print('outputfilename:' + str(xmlOutput))
            #xmlFileObject = event['s3']['Keyxml']

            # Pass None to the xml output file, so it doesn't write it.
            converter = Converter(s3ObjectBytestream,manufacturer,None)
            converter.convert()

            print('I found this validation feedback from the conversion:' + str(converter.validationFeedback))

            # Somehow check if the convert was successful.
            if(converter.xmlText is not None and len(converter.xmlText) > 0):
                try:

                    #print('Looking for children of this upload object..')
                    parentId = csvUploadObject['id']
                    childUploads = getUploadsByParentId(token=token,url=url,parentId=parentId)
                    for childUpload in childUploads:
                        if(childUpload['type'] == 'HAML'):
                            childUploadFileName = childUpload['fileName']
                            childUploadId = childUpload['id']
                            print('Found a child HAML file, I will delete this one:' + str(childUploadFileName))
                            deleteResponse = deleteUpload(token=token,url=url, uploadId=childUploadId)
                            print('Found this reponse from deleting the child:' + str(deleteResponse))
                except Exception as e:
                    print('Warning! Could not delete the previous child upload:' + str(e))

                try:
                    response = createConvertedUploadObject(newUploadFileName=xmlOutput, newUploadFileType='HAML', previousUploadFileName=csvKey, token=token, url=url)
                    print('response from new upload:' + str(response))

                    # Write out the xml text
                    # This should trigger the XML validation.
                    print('encoding this string:' + str(type(converter.xmlText)))
                    encoded_string = converter.xmlText.encode("utf-8")
                    print('encoded text:' + str(encoded_string))
                    s3 = boto3.resource("s3")
                    print('saving file:' + str(xmlOutput))
                    s3.Bucket(bucket).put_object(Key=xmlOutput, Body=encoded_string)

                    # Set validation status of the .csv file
                    setValidationStatus(uploadFileName=csvKey, isValid=True, validationFeedback='Converted to HAML.\n' + str(converter.validationFeedback), validatorType='HAML_CONVERT', token=token, url=url)
                except Exception as e:
                    print('Cannot save file to S3 Storage:')
                    print(str(e))
                    setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed to save Converted HAML File!\n' + str(converter.validationFeedback), validatorType='HAML_CONVERT', token=token, url=url)
            else:
                print('Failed to convert the CSV File')
                setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed to Convert CSV to HAML File!\n' + str(converter.validationFeedback), validatorType='HAML_CONVERT', token=token, url=url)
        except Exception as e:
            print('Failed to convert file:' + str(e))
            setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed to convert file:\n' + str(e) + str(converter.validationFeedback), validatorType='HAML_CONVERT', token=token, url=url)
    except Exception as e:
        # This isnt' great because I dont have the csvKey already. I cant set the validation status.
        print('Failed Fetching data from S3:' + str(e))
        setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed Fetching data from S3:\n' + str(e), validatorType='HAML_CONVERT')