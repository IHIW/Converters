import boto3
import io
import json
import urllib

from IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadIfExists

def calculate_positive_beads_handler(event, context):
    try:
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

    except Exception as e:
        # This isnt' great because I dont have the csvKey already. I cant set the validation status.
        print('Failed Fetching data from S3:' + str(e))
        #setValidationStatus(uploadFileName=csvKey, isValid=False, validationFeedback='Failed Fetching data from S3:\n' + str(e), validatorType='HAML_CONVERT')



def calculatePositiveBeads(xmlText=None):
    print('Calculating Positive Beads:')