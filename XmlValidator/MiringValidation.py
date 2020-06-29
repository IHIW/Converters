from sys import exc_info
from boto3 import client
s3 = client('s3')
import json
import urllib
from urllib import request



def miring_validation_handler(event, context):
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        content = json.loads(event['Records'][0]['Sns']['Message'])

        bucket = content['Records'][0]['s3']['bucket']['name']
        xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read()


        # Perform the validation.
        validationResults = validateMiring(xmlText=xmlText)

        print('results of miring validation:' + str(validationResults))

        # Request the management app to update the validation status for this file.
        #url = getUrl()
        #token=getToken(url=url)

        #setValidationStatus(uploadFileName=xmlKey, isValid=(validationResults=='Valid'), validationFeedback=validationResults, url=url, token=token)

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


def validateMiring(xmlText=None):
    # TODO: there's nothing here yet. send a message to miring.b12x.org and get a response.
    try:
        print('Inside the MIRING Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])

        #$ curl -X POST --data-urlencode 'xml[]=<hml>...</hml>' http://miring.b12x.org/validator/ValidateMiring/

        fullUrl = 'http://miring.b12x.org/validator/ValidateMiring'

        body = {
            'xml': xmlText.decode()
        }

        print('body:' + str(body))
        jsonDump = json.dumps(body)
        print('jsonDump:' + jsonDump)
        encodedJsonData = str(jsonDump).encode('utf-8')
        print('encodedJsonData:' + str(encodedJsonData))
        updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='POST')

        updateRequest.add_header('Content-Type', 'application/json')
        #updateRequest.add_header('xml',xmlText)

        print('doing request')
        response = request.urlopen(updateRequest)
        print('request done')
        responseData = response.read()

        print('responseData:' + str(responseData))

        responseText = responseData.decode()

        print('responseText:' + responseText)
        if (responseText is None or len(responseText) < 1):
            print('updateValidationStatus returned an empty response!')
            return False
        #response = json.loads(responseText)


        return(responseText)

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))
