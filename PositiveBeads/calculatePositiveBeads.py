import boto3
import io
import json
import urllib


def calculate_positive_beads_handler(event, context):
    try:
        #print('EVENT:')
        #print(str(event))

        hamlKey = event['Input']['Payload']['file_name']
        #print('hamlkey:' + str(hamlKey))

        bucket=event['Input']['Payload']['Input']['detail']['requestParameters']['bucketName']
        #print('bucket:' + str(bucket))

        decodedKey = urllib.parse.unquote_plus(hamlKey)
        #print('decodedHAMLKey:' + str(decodedKey))
        hamlKey = decodedKey

        token=event['Input']['Payload']['token']
        print('Token=' + str(token))

        s3 = boto3.client('s3')
        csvFileObject = s3.get_object(Bucket=bucket, Key=hamlKey)
        print('csvFileObject:' + str(csvFileObject))
        s3ObjectBytestream = io.BytesIO(csvFileObject['Body'].read())
        print('s3 object:' + str(s3ObjectBytestream))

        positiveBeadsText = calculatePositiveBeads(xmlText=s3ObjectBytestream)
        event['is_valid'] = True
        event['validation_text'] = positiveBeadsText
        return event

    except Exception as e:
        # This isnt' great because I dont have the csvKey already. I cant set the validation status.
        print('An exception has occured:' + str(e))
        #setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed Fetching data from S3:\n' + str(e), validatorType='HAML_CONVERT')



def calculatePositiveBeads(xmlText=None):
    print('Calculating Positive Beads:')
    positiveBeadsText = 'Yep, looks like there are some positive beads! A*01 and DRB1*01 or something!'
    return positiveBeadsText