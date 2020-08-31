import string
import requests
import boto3
from sys import exc_info

def validateNmdpPortal(xmlText=None):
    # TODO: there's nothing here yet. send a message to the NMDP portal and parse response
    #curl -X POST -d @"C:\Users\ioannis\Desktop\good.hml.1.0.1.xml" -H "Content-Type: text/xml" https://qa-api.nmdp.org/hml_gw/v1/validate

    #content = json.loads(event['Records'][0]['Sns']['Message'])

    #bucket = content['Records'][0]['s3']['bucket']['name']
    #xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
    #xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
    #xmlText = xmlFileObject["Body"].read()

    try:
        print('Inside the NMPD Portal Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        baseurl = r'https://qa-api.nmdp.org/hml_gw/v1/validate'
        headers = {
            'Content-Type': 'text/xml',
        }

        bucketname = 'ihiw-management-upload-staging'
        filename = '1497_1589832668946_HML_good.hml.1.0.1.hml'
        s3 = boto3.resource('s3')
        data = s3.Object(bucketname, filename).get()['Body'].read()

        #data = open(r"C:\Users\ioannis\Desktop\good.hml.1.0.1.xml", "rb")

        #udata = str(data.__format__(xmlText)).encode('utf-8')
        response = requests.post(url=baseurl, headers=headers, data=data)
        return('NMPD validation Results are the following: ' + response.text)

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))





