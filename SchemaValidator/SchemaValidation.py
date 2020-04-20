import json
import yaml
import urllib
import ast
from boto3 import client
s3 = client('s3')
from lxml import etree
from sys import exc_info
from urllib import request


def validate_handler(event, context):
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        bucket = event['Records'][0]['s3']['bucket']['name']
        xmlKey = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
        xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        xmlText = xmlFileObject["Body"].read().decode()

        # Parse xml and determine the file type. It might be hml or haml or ?, For now, assume hml.
        fileType = 'hml'

        # Fetch the Schema Text
        if (fileType == 'hml'):
            schemaKey = 'schema/hml-1.0.1.xsd'
        elif (fileType == 'haml'):
            raise Exception('I have not yet implemented validation of haml files.')
        else:
            raise Exception('Unknown file type:' + str(fileType))

        schemaFileObject = s3.get_object(Bucket=bucket, Key=schemaKey)
        schemaText = schemaFileObject["Body"].read().decode()

        # Perform the validation.
        validationResults = validateAgainstSchema(schemaText=schemaText, xmlText=xmlText)
        print('ValidationResults:' + str(validationResults))

        # Request the management app to update the validation status for this file.
        url = getUrl()
        token=getToken(url=url)

        setValidationStatus(uploadFileName=xmlKey, isValid=(validationResults=='Valid'), validationFeedback=validationResults, url=url, token=token)

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def setValidationStatus(uploadFileName=None, isValid=None, validationFeedback=None, token=None, url=None):
    print('Setting upload validation status,\t' + 'uploadFileName=' + str(uploadFileName) + '\tisValid=' + str(isValid) + '\tvalidationFeedback=(' + str(validationFeedback) + ')\turl=' + str(url))
    if (uploadFileName is None or isValid is None or validationFeedback is None):
        print('Missing data, cannot set validation status:'
              + '\tuploadFileName:' + str(uploadFileName)
              + '\tisValid:' + str(isValid)
              + '\tvalidationFeedback:' + str(validationFeedback))
        return False
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)

    validationSuccess = updateValidationStatus(fileName=uploadFileName, isValid=isValid, validationFeedback=validationFeedback, url=url, token=token)

    return validationSuccess

def validateAgainstSchema(schemaText=None, xmlText=None):
    try:
        # Validate XML against Schema.
        schemaTree = etree.XMLSchema(etree.XML(schemaText))
        xmlParser = etree.XMLParser(schema=schemaTree)
        try:
            xmlTree = etree.fromstring(xmlText, xmlParser)
            # If we get this far, the XML has validated successfully.
            return ('Valid')
        except etree.XMLSyntaxError as err:
            return ('Invalid:\t' + str(err))

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))

def updateValidationStatus(fileName=None, isValid=None, validationFeedback=None, token=None, url=None):
    if(url is None):
        url=getUrl()
    if(fileName is None):
        print('No filename was provided, I cannot set validation status.')
        return False
    try:
        fullUrl = str(url) + '/api/uploads/setvalidation'
        # TODO: Haml Files?
        body = {'valid': isValid, 'validationFeedback': validationFeedback, 'fileName':fileName, 'type':'HML'}
        encodedJsonData = str(json.dumps(body)).encode('utf-8')
        updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='PUT')
        updateRequest.add_header('Content-Type', 'application/json')
        updateRequest.add_header('Authorization', 'Bearer ' + token)
        responseData = request.urlopen(updateRequest).read().decode("UTF-8")
        if(responseData is None or len(responseData) < 1):
            print('updateValidationStatus returned an empty response!')
            return False
        response=json.loads(responseData)

        # The response contains the saved data, if successful. If the response matches what we expect it was a success.
        if(str(response['fileName'])==str(fileName) and str(response['valid'])==str(isValid)
            and str(response['validationFeedback'])==str(validationFeedback)):
            return True
        else:
            print('Could not set validation status, response:\n' + str(response))
            return False
    except SyntaxError as e:
        print('Syntax error when parsing response from request:\n' + str(e) + '\n' + str(exc_info()))
        return False
    except urllib.error.HTTPError as e:
        print('HTTP error when setting validation status for upload file ' + str(fileName) + ' : ' + str(e))
        return False
    except Exception as e:
        print('Error when updating validation status:\n' + str(e) + '\n' + str(exc_info()))
        return False

def getCredentials():
    try:
        configStream = open('validation_config.yml', 'r')
        configDict = yaml.load(configStream, Loader=yaml.FullLoader)
        user=configDict['username']
        password = configDict['password']

        print('Finished Fetching Credentials.')
        return (user, password)
    except Exception as e:
        print('Could not load login configuration.')
        print('I expected to find validation_config.yml with entries :\nurl: {}\nusername: {}\n password: {}')
        print(str(e))
        return (None,None)

def getUrl():
    try:
        configStream = open('validation_config.yml', 'r')
        configDict = yaml.load(configStream, Loader=yaml.FullLoader)
        url = configDict['url']

        print('Finished Fetching Url.')
        return url
    except Exception as e:
        print('Could not load login configuration.')
        print('I expected to find validation_config.yml with entries :\nurl: {}\nusername: {}\n password: {}')
        print(str(e))
        return None

def getToken(url=None, user=None, password=None):
    try:
        if(user is None or password is None):
            (user, password) = getCredentials()
        if (url is None):
            url = getUrl()

        fullUrl = str(url) + "/api/authenticate"
        body = {'username': user, 'password': password}
        encodedJsonData=str(json.dumps(body)).encode('utf-8')
        tokenRequest=request.Request(url=fullUrl, data=encodedJsonData)
        tokenRequest.add_header('Content-Type', 'application/json')
        requestResponse=request.urlopen(tokenRequest)
        responseData=ast.literal_eval(requestResponse.read().decode("UTF-8"))
        tokenText = responseData['id_token']
        print('Finished Fetching Token.')
        return tokenText
    except urllib.error.HTTPError as e:
        print('HTTP error when obtaining token:' + str(e))
        return None
    except urllib.error.URLError as e:
        print('URL error when obtaining token:' + str(e))
        return None
    except KeyError:
        print("There was no access token: " + str(requestResponse))
        return None
    except ValueError as e:
        print('ValueError when obtaining token:' + str(e))
        return None
    print("Token couldn't be obtained")
    return None
