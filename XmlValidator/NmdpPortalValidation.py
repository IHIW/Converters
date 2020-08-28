import json
import urllib
from sys import exc_info


from boto3 import client
s3 = client('s3')


def nmdp_validation_handler(event, context):
    print('I found the schema validation handler.')
    print('This is the event that was passed in:' + str(event))
    # This is the AWS Lambda handler function.
    try:
        print('This is bens message in the handler!!!!!!')

        print('This is the event:' + str(event))

        # Get the uploaded file.
        content = json.loads(event['Records'][0]['Sns']['Message'])

        bucket = content['Records'][0]['s3']['bucket']['name']

        print('I just found this bucket name:' + str(bucket))

        xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')

        print('I found the XML Key:' + str(xmlKey))
        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read()

        print('I found this xml text:' + str(xmlText))

        # TODO: I should do the validation here.
        #   1) Send message to Service
        #   2) Interpret the response
        #   3) Determine if file is valid or not
        #   4) Create a feedback text
        #   5) Set validation status of the upload object.
        return {
            'statusCode': 200,
            'body': json.dumps('Hello from Lambda, we ran the validation handler successfully.')

        }

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def validateNmdpPortal(xmlText=None):
    # TODO: there's nothing here yet. send a message to the NMDP portal and parse response
    try:
        print('Inside the NMPD Portal Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        return('NMPD validation Results')

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))

