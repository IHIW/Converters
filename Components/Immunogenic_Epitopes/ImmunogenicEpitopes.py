from boto3 import client
s3 = client('s3')
#from lxml import etree
from sys import exc_info, path
#import json
#import urllib

# For importing common methods, may be in the same directory when deployed as a package
try:
    from IhiwRestAccess import RestHelloWorld
except Exception:
    from Common.IhiwRestAccess import RestHelloWorld

def immunogenic_epitope_handler(event, context):
    print('I found the schema validation handler.')
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        #content = json.loads(event['Records'][0]['Sns']['Message'])

        #bucket = content['Records'][0]['s3']['bucket']['name']
        #xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        #xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        #xmlText = xmlFileObject["Body"].read()


        validationResults='Valid'
        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


def parseExcelFile(excelFile=None):
    if(excelFile is None):
        print('No excel file was provided! I cannot parse nothing!')
        return None
    elif(type(excelFile)==str):
        # It's a file path. Open it.
        print('Opening file:' + excelFile)
        excelFile = open(excelFile, 'r')
    else:
        # It's a file. Don't need to do anything.
        pass

    print ('Parsing Excel File:' + str(excelFile))
    RestHelloWorld()