import yaml
import ast
import urllib
import json

from sys import exc_info
from urllib import request

def setValidationStatus(uploadFileName=None, isValid=None, validationFeedback=None, validatorType=None, token=None, url=None):
    print('Setting upload validation status,\t' + 'uploadFileName=' + str(uploadFileName) + '\tvalidatorType=' + str(validatorType) + '\tisValid=' + str(isValid) + '\tvalidationFeedback=(' + str(validationFeedback) + ')\turl=' + str(url))
    if (uploadFileName is None or isValid is None or validationFeedback is None or validatorType is None):
        print('Missing data, cannot set validation status:'
              + '\tuploadFileName:' + str(uploadFileName)
              + '\tisValid:' + str(isValid)
              + '\tvalidationFeedback:'
              + str(validationFeedback)
              + '\tvalidatorType:' + str(validatorType))
        return False
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)
    if(validatorType is None):
        validatorType = 'UNKNOWN'
    if (validationFeedback is None or len(str(validationFeedback))==0):
        validationFeedback = 'No Feedback Provided.'
    try:
        print ('Setting ' + str(validatorType) + ' validation status ' + str(isValid) + ' for file ' + str(uploadFileName))

        fullUrl = str(url) + '/api/uploads/setvalidation'

        body = {
            'valid': isValid
            , 'validationFeedback': validationFeedback
            , 'validator': validatorType
            , 'upload': {
                'fileName': uploadFileName
            }
        }

        print('body:' + str(body))
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
        # Probably need to make this more robust.
        if(str(response['valid'])==str(isValid)  and str(response['validationFeedback'])==str(validationFeedback)):
            return True
        else:
            print('Could not set validation status, response:\n' + str(response))
            return False
    except SyntaxError as e:
        print('Syntax error when parsing response from request:\n' + str(e) + '\n' + str(exc_info()))
        return False
    except urllib.error.HTTPError as e:
        print('HTTP error when setting validation status for upload file ' + str(uploadFileName) + ' : ' + str(e))
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
