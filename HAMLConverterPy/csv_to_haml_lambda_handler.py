import boto3
import urllib
from ihiw_converter import Converter
from IhiwRestAccess import getUploadsByParentId, deleteUpload, createConvertedUploadObject
from time import sleep
import io



''' <summary>
    /// Handler was converted to Python by Teresa Tavella
    /// University of Bologna
    /// https://github.com/TessaTi/IHIW_Converter_py
 '''

def csv_to_haml_lambda_handler(event, context):
    # Some default JSON to help with debugging, this will be replaced by the event payload
    uploadDetails = {}
    uploadDetails['is_valid'] = False
    uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the step function flowchart.'
    uploadDetails['validator_type'] = 'HAML_CONVERT'

    try:
        # Sleep 1 second, enough time to make sure the file is available. I think this actually doesn't help anything.
        # sleep(1)

        # Fetching the upload detail bundle from the step function payload
        if "Input" in event and "Payload" in event['Input']:
            uploadDetails = event['Input']['Payload']
        else:
            print(str(uploadDetails['validation_feedback']))
            return uploadDetails

        bucket = uploadDetails['bucket']
        #print('bucket:' + str(bucket))

        csvKey = uploadDetails['file_name']

        # Filenames that have a space character need to be decoded.
        decodedKey = urllib.parse.unquote_plus(csvKey)
        #print('decodedCsvKey:' + str(decodedKey))
        csvKey = decodedKey

        url = uploadDetails['url']
        token = uploadDetails['token']
        try:
            # Get the file from S3
            print('Getting the file from S3...')
            s3 = boto3.client('s3')

            # Get the CSV object from S3
            csvFileObject = s3.get_object(Bucket=bucket, Key=csvKey)
            #print('csvFileObject:' + str(csvFileObject))
            #csvText = csvFileObject["Body"].read().decode()
            #print('csvFileText:' + str(csvText))
            s3ObjectBytestream = io.BytesIO(csvFileObject['Body'].read())
            #print('s3 object:' + str(s3ObjectBytestream))

            xmlOutput = (csvKey.replace('ANTIBODY_CSV','HAML') + '.haml')
            #print('outputfilename:' + str(xmlOutput))
            #xmlFileObject = event['s3']['Keyxml']


            # Pass None to the xml output file, so it doesn't write it.
            converter = Converter(csvFileName=s3ObjectBytestream,manufacturer=None,xmlFile=None)
            converter.convert()

            #print('I found this validation feedback from the conversion:' + str(converter.validationFeedback))

            # Somehow check if the convert was successful.
            if(converter.xmlText is not None and len(converter.xmlText) > 0):
                try:
                    # Delete the Children of this parent Upload.
                    print('Looking for children of this upload object..')
                    childUploads = getUploadsByParentId(token=token,url=url,parentId=uploadDetails['id'])
                    # TODO: Test this, we should be able to delete previous children of an upload file (this happens when we re-upload the CSV on the IHIW database)
                    #print('We found these children: ' + str(childUploads))
                    for childUpload in childUploads:
                        if(childUpload['type'] == 'HAML'):
                            childUploadFileName = childUpload['fileName']
                            childUploadId = childUpload['id']
                            #print('Found a child HAML file, I will delete this one:' + str(childUploadFileName))
                            #print('passing token=' + str(token))
                            #print('passing url=' + str(url))
                            deleteResponse = deleteUpload(token=token,url=url, uploadId=childUploadId)
                            print('Found this reponse from deleting the child:' + str(deleteResponse))
                except Exception as e:
                    print('Warning! Could not delete the previous child upload:' + str(e))

                try:
                    response = createConvertedUploadObject(newUploadFileName=xmlOutput, newUploadFileType='HAML', previousUploadFileName=csvKey, token=token, url=url)
                    #print('response from new upload:' + str(response))

                    # Write out the xml text
                    # This should trigger the XML validation.
                    #print('encoding this string:' + str(type(converter.xmlText)))
                    if(len(converter.xmlText)>5):
                        encoded_string = converter.xmlText.encode("utf-8")

                        #print('encoded text:' + str(encoded_string))
                        s3 = boto3.resource("s3")
                        #print('saving file:' + str(xmlOutput))
                        s3.Bucket(bucket).put_object(Key=xmlOutput, Body=encoded_string)

                        # Set validation status of the .csv file
                        uploadDetails['is_valid'] = True
                        uploadDetails['validation_feedback'] = 'Converted to HAML.\n' + str(converter.validationFeedback)
                        uploadDetails['validator_type'] = 'HAML_CONVERT'
                    else:
                        # Set validation status of the .csv file
                        uploadDetails['is_valid'] = False
                        uploadDetails['validation_feedback'] = 'Could not convert to HAML:\n' + str(converter.validationFeedback)
                        uploadDetails['validator_type'] = 'HAML_CONVERT'
                except Exception as e:
                    print('Cannot save file to S3 Storage:')
                    print(str(e))
                    uploadDetails['is_valid'] = False
                    uploadDetails['validation_feedback'] = 'Failed to save Converted HAML File to S3!\n' + str(converter.validationFeedback)
                    uploadDetails['validator_type'] = 'HAML_CONVERT'

            else:
                print('Failed to convert the CSV File')
                uploadDetails['is_valid'] = False
                uploadDetails['validation_feedback'] = 'Failed to Convert CSV to HAML File!\n' + str(converter.validationFeedback)
                uploadDetails['validator_type'] = 'HAML_CONVERT'

        except Exception as e:
            print('Exception. Failed to convert file:' + str(e))
            #setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed to convert file:\n' + str(e) + str(converter.validationFeedback), validatorType='HAML_CONVERT', token=token, url=url)

    except Exception as e:
        # This isnt' great because I dont have the csvKey already. I cant set the validation status.
        print('Exception. Failed Fetching data from S3:' + str(e))

        uploadDetails['is_valid'] = False
        uploadDetails['validation_feedback'] = 'Failed Fetching data from S3:\n' + str(e)
        uploadDetails['validator_type'] = 'HAML_CONVERT'

    return uploadDetails