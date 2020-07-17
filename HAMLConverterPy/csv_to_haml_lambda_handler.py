import boto3
#import os
#import sys
from ihiw_converter import Converter

import json
import urllib
import io

try:
    from IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadByFilename
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common.IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadByFilename




''' <summary>
    /// Handler was converted to Python by Teresa Tavella
    /// University of Bologna
    /// https://github.com/TessaTi/IHIW_Converter_py
 '''

def csv_to_hml_lambda_handler(event, context):
    try:
        content = json.loads(event['Records'][0]['Sns']['Message'])
        print('Content:' + str(content))
        bucket = content['Records'][0]['s3']['bucket']['name']

        print('bucket:' + str(bucket))
        csvKey = content['Records'][0]['s3']['object']['key']

        print('csvKey:' + str(csvKey))

        if not (str(csvKey[len(csvKey)-4:len(csvKey)]).lower() in ['.csv','.tsv']):
            print('Upload ' + str(csvKey) + ' is not a .csv file. I will not convert it to HAML.')
            return None

        # Login token for rest methods...
        print('Getting a login token and URL...')
        (user, password) = getCredentials(configFileName='converter_config.yml')
        url = getUrl(configFileName='converter_config.yml')
        token = getToken(user=user, password=password, url=url)

        csvUploadObject = getUploadByFilename(token=token, url=url, fileName=csvKey)
        if(csvUploadObject is None or 'type' not in csvUploadObject.keys() or csvUploadObject['type'] is None):
            print('Could not find the Upload object for upload ' + str(csvKey) + '\nI will not convert it to HAML.' )
            return None
        elif (csvUploadObject['type'] != 'HAML'):
            print('The upload ' + str(csvKey) + ' is type ' + csvUploadObject['type'] + '. I will not convert it to HAML.')
            return None

        s3 = boto3.client('s3')

        csvFileObject = s3.get_object(Bucket=bucket, Key=csvKey)
        print('csvFileObject:' + str(csvFileObject))
        #csvText = csvFileObject["Body"].read().decode()
        #print('csvFileText:' + str(csvText))
        s3ObjectBytestream = io.BytesIO(csvFileObject['Body'].read())
        print('s3 object:' + str(s3ObjectBytestream))

        manufacturer=''
        xmlOutput = (csvKey + '.haml')
        print('outputfilename:' + str(xmlOutput))
        #xmlFileObject = event['s3']['Keyxml']

        # Pass None to the xml output file, so it doesn't write it.
        converter = Converter(s3ObjectBytestream,manufacturer,None)
        converter.convert()

        # Somehow check if the convert was successful.
        if(converter.xmlText is not None and len(converter.xmlText) > 0):
            try:
                # Call the Rest enpoint to create a new Upload entry. This should be BEFORE the file is actually created.
                response=createConvertedUploadObject(newUploadFileName=xmlOutput,  newUploadFileType= 'HAML', previousUploadFileName=csvKey, token=token, url=url)
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
                setValidationStatus(uploadFileName=csvKey, isValid=True, validationFeedback='Converted to HAML.', validatorType='HAML_CONVERT', token=token, url=url)
            except Exception:
                print('Cannot save file to S3 Storage')
                setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed to save Converted HAML File!', validatorType='HAML_CONVERT', token=token, url=url)
        else:
            print('Failed to convert the CSV File')
            setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed to Convert CSV to HAML File!', validatorType='HAML_CONVERT', token=token, url=url)


            
    except ValueError: 
        print('Not known manufacturer, unable to convert file')
        setValidationStatus