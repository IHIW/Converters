import boto3
#import os
#import sys
from ihiw_converter import Converter
import json
import urllib
import io




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
        manufacturer,Table = converter.DetermineManufacturer()
        print('determined manufacturer: ' + manufacturer)
        
        if manufacturer == 'OneLambda':
            print('Manufacturer', manufacturer)
            converter.ProcessOneLambda(Table)
        elif manufacturer == 'Immucor':
            print('Manufacturer', manufacturer)
            converter.ProcessImmucor(Table)
        else: 
            print('Not known manufacturer, unable to convert file')

        print('encoding this string:' + str(type(converter.xmlText)))
        encoded_string = converter.xmlText.encode("utf-8")
        print('encoded text:' + str(encoded_string))

        #print('getting s3 resource')
        s3 = boto3.resource("s3")
        print('saving file:' + str(xmlOutput))
        s3.Bucket(bucket).put_object(Key=xmlOutput, Body=encoded_string)

        # Call the Rest enpoint to create a new Upload entry. (Actually this should be BEFORE the file is actually created.
            
    except ValueError: 
        print('Not known manufacturer, unable to convert file')
