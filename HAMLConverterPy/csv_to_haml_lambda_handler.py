import boto3
#import os
#import sys
from ihiw_converter import Converter
import json


s3 = boto3.client('s3')

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



        #bucket = event['s3']['bucket']
        #csvFileObject = event['s3']['Keycsv']
        #manufacturer = event['s3']['Keymanufacturer']
        csvFileObject=open(content['Records'][0]['s3']['object']['key'])
        print('csvFileObject:' + str(csvFileObject))
        manufacturer=''
        xmlOutput = str()
        #xmlFileObject = event['s3']['Keyxml']

        converter = Converter(csvFileObject,manufacturer,xmlFileObject)
        Manufacturer,Table = converter.DetermineManufacturer()
        
        if Manufacturer == 'OneLambda':
            print('Manufacturer', Manufacturer)
            converter.ProcessOneLambda(Table)
        elif Manufacturer == 'Immucor':
            print('Manufacturer', Manufacturer)
            converter.ProcessImmucor(Table)
        else: 
            print('Not known manufacturer, unable to convert file')

        print('I need to create new upload with this text:' + '?????')
            
    except ValueError: 
        print('Not known manufacturer, unable to convert file')