import boto3
#import os
#import sys
from ihiw_converter import Converter

import json
import urllib
import io

try:
    from IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common.IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials




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

        # Login token for rest methods...
        print('Getting a login token and URL...')
        (user, password) = getCredentials(configFileName='converter_config.yml')
        url = getUrl(configFileName='converter_config.yml')
        token = getToken(user=user, password=password, url=url)

        # Somehow check if the convert was successful.
        if(converter.xmlText is not None and len(converter.xmlText) > 0):
            try:
                # Call the Rest enpoint to create a new Upload entry. (Actually this should be BEFORE the file is actually created.
                response=createConvertedUploadObject(newUploadFileName=csvKey + '.haml', previousUploadFileName=csvKey, token=token, url=url)

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