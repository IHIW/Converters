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

        maxValidationLength=10000
        if(len(validationFeedback) > maxValidationLength):
            print('Warning, validator feedback length is greater than the maximum (' + str(maxValidationLength)
                  + ') so I will truncate the feedback to ' + str(maxValidationLength) + ' characters.')
            validationFeedback=validationFeedback[0:maxValidationLength]

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

def createConvertedUploadObject(newUploadFileName=None, newUploadFileType=None, token=None, url=None, previousUploadFileName=None):
    print('Creating new upload object,\t' + 'newUploadFileType=' + str(newUploadFileType))
    if(previousUploadFileName is not None and len(previousUploadFileName)>1):
        print('previousConvertedUploadFileName=' + str(previousUploadFileName))
    else:
        print('No previous upload file name! Cannot Continue!')
        return None

    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)

    if token is None or len(token) < 1:
        print('Error. No login token available when creating converted upload object.')
        return None


    try:
        fullUrl = str(url) + '/api/uploads/copyupload'

        # Body is empty, we're passing the interesting stuff in the parameters.
        body = {}

        params = {
            'oldFileName': previousUploadFileName
            #'oldfileName': previousUploadFileName
            ,'newType': newUploadFileType
            ,'newFileName':newUploadFileName
            }
        query_string = urllib.parse.urlencode(params)
        fullUrl = fullUrl + "?" + query_string

        print('body:' + str(body))
        print('fullurl:' + str(fullUrl))

        encodedJsonData = str(json.dumps(body)).encode('utf-8')
        updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='PUT')
        updateRequest.add_header('Content-Type', 'application/json')
        updateRequest.add_header('Authorization', 'Bearer ' + token)

        responseData = request.urlopen(updateRequest).read().decode("UTF-8")
        if(responseData is None or len(responseData) < 1):
            print('updateValidationStatus returned an empty response!')
            return False
        response=json.loads(responseData)
        if str(response['id']) is not None:
            return response
        else:
            print('No response was found when creating the new object, returning None.')
            return None

    except SyntaxError as e:
        print('Syntax error when parsing response from request:\n' + str(e) + '\n' + str(exc_info()))
        return False
    except urllib.error.HTTPError as e:
        print('HTTP error when creating the Upload object for converted file for upload file ' + str(previousUploadFileName) + ' : ' + str(e))
        return False
    except Exception as e:
        print('Error when creating the Upload object for converted file:\n' + str(e) + '\n' + str(exc_info()))
        return False

'''
def createNewUploadObject(newUploadFileName=None, newUploadFileType=None, token=None, url=None):
    print('Creating new upload object,\t' + 'newUploadFileType=' + str(newUploadFileType))

    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)
    try:
        fullUrl = str(url) + '/api/uploads'

        # Body is empty, we're passing the interesting stuff in the parameters.
        body = {}

        params = {
            'oldFileName': previousUploadFileName
            #'oldfileName': previousUploadFileName
            ,'newType': newUploadFileType
            ,'newFileName':newUploadFileName
            }
        query_string = urllib.parse.urlencode(params)
        fullUrl = fullUrl + "?" + query_string

        print('body:' + str(body))
        print('fullurl:' + str(fullUrl))

        encodedJsonData = str(json.dumps(body)).encode('utf-8')
        updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='PUT')
        updateRequest.add_header('Content-Type', 'application/json')
        updateRequest.add_header('Authorization', 'Bearer ' + token)

        responseData = request.urlopen(updateRequest).read().decode("UTF-8")
        if(responseData is None or len(responseData) < 1):
            print('updateValidationStatus returned an empty response!')
            return False
        response=json.loads(responseData)
        if str(response['id']) is not None:
            return response
        else:
            print('No response was found when creating the new object, returning None.')
            return None

    except SyntaxError as e:
        print('Syntax error when parsing response from request:\n' + str(e) + '\n' + str(exc_info()))
        return False
    except urllib.error.HTTPError as e:
        print('HTTP error when creating the Upload object for converted file for upload file ' + str(previousUploadFileName) + ' : ' + str(e))
        return False
    except Exception as e:
        print('Error when creating the Upload object for converted file:\n' + str(e) + '\n' + str(exc_info()))
        return False
'''
def getCredentials(configFileName='validation_config.yml'):
    try:
        configStream = open(configFileName, 'r')
        configDict = yaml.load(configStream, Loader=yaml.FullLoader)
        user=configDict['username']
        password = configDict['password']

        print('Finished Fetching Credentials.')
        return (user, password)
    except Exception as e:
        print('Could not load login configuration.')
        print('I expected to find ' + configFileName + ' with entries :\nurl: {}\nusername: {}\n password: {}')
        print(str(e))
        return (None,None)

def getUrl(configFileName='validation_config.yml'):
    try:
        configStream = open(configFileName, 'r')
        configDict = yaml.load(configStream, Loader=yaml.FullLoader)
        url = configDict['url']

        print('Finished Fetching Url.')
        return url
    except Exception as e:
        print('Could not load login configuration.')
        print('I expected to find ' + configFileName + ' with entries :\nurl: {}\nusername: {}\n password: {}')
        print(str(e))
        return None

def getToken(url=None, user=None, password=None):
    try:
        if(user is None or password is None or len(user)==0 or len(password)==0 ):
            (user, password) = getCredentials()
        if (url is None or len(url)==0):
            url = getUrl()

        if(user is None or len(user)==0):
            print('Error when fetching Token. Empty username.')
            return None

        if(password is None or len(password)==0):
            print('Error when fetching Token. Empty password.')
            return None

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

def getUploads(token=None, url=None):
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)

    if token is None or len(token) < 1:
        print('Error. No login token available when getting uploads.')
        return None

    fullUrl = str(url) + '/api/uploads'
    body = {}

    encodedJsonData = str(json.dumps(body)).encode('utf-8')
    updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='GET')
    updateRequest.add_header('Content-Type', 'application/json')
    updateRequest.add_header('Authorization', 'Bearer ' + token)
    responseData = request.urlopen(updateRequest).read().decode("UTF-8")
    #print('Response:' + str(responseData))
    if (responseData is None or len(responseData) < 1):
        print('updateValidationStatus returned an empty response!')
        return False
    response = json.loads(responseData)

    #print('uploadListResponse:' + str(response))


    return response

def getUploadsByParentId(token=None, url=None, parentId=None, allUploads=None):
    # TODO: It would be better to do this inside a rest method somewhere. Getting all the uploads and looping through might not be most efficient.
    if parentId is None:
        print('Parent ID is none, cannot find any uploads with this parent')
        return None
    else:
        if(allUploads is None):
            allUploads=getUploads(token=token,url=url)

        uploadList = []
        for upload in allUploads:
            if(upload['parentUpload'] is not None
                and str(upload['parentUpload']['id']) == str(parentId)
            ):
                uploadList.append(upload)

        return uploadList

def getUploadFileNamesByPartialKeyword(token=None, url=None, fileName=None, projectIDs=None, allUploads=None, uploadTypeFilter=None):
    if(projectIDs is not None and not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]

    if(uploadTypeFilter is not None and not isinstance(uploadTypeFilter, list)):
        uploadTypeFilter = [uploadTypeFilter]

    if token is None or len(token) < 1:
        print('Error. No login token available when getting uploads by partial keyword.')
        return None


    #print('Checking IDS:' + str(projectIDs))
    if fileName is None:
        print('fileName is none, cannot find any uploads with this parent')
        return None
    else:
        if(allUploads is None):
            allUploads=getUploads(token=token,url=url)

        #print('Checking keyword ' + fileName + ' against uploads:\n' + str(allUploads))

        uploadList = []

        for upload in allUploads:
            if(upload['fileName'] is not None
                and fileName.lower() in str(upload['fileName']).lower()
                and (projectIDs is None or int(upload['project']['id']) in projectIDs)
                and (uploadTypeFilter is None or str(upload['type']) in uploadTypeFilter)
            ):
                uploadList.append(upload)

                # Also append the children of this upload
                childUploads = getUploadsByParentId(token=token, url=url, parentId=upload['id'], allUploads=allUploads)
                for childUpload in childUploads:
                    uploadList.append(childUpload)

        # TODO: What if there are duplicate files? will list(set(list)) work? This could cause a bug when adding files to the zip. Not sure.
        #print('returning this file list of len ' + str(len(uploadList)) + ' : ' + str(uploadList))
        # list comprehension to remove duplicate uploads
        #uploadList = [dict(t) for t in {tuple(d.items()) for d in uploadList}]
        #print('returning this file list of len ' + str(len(uploadList)) + ' : ' + str(uploadList))
        return uploadList

def getUploadByFilename(token=None, url=None, fileName=None):
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)
    print('Getting upload by filename:' + str(fileName))

    if token is None or len(token) < 1:
        print('Error. No login token available when getting upload by Filename')
        return None


    # Encoding the file name, in case it contains spaces
    fullUrl = str(url) + '/api/uploads/getbyfilename/' + urllib.parse.quote(fileName)
    #print('FullUrl:' +str(fullUrl))
    body = {}

    encodedJsonData = str(json.dumps(body)).encode('utf-8')
    updateRequest = request.Request(url=str(fullUrl), data=encodedJsonData, method='GET')
    updateRequest.add_header('Content-Type', 'application/json')
    updateRequest.add_header('Authorization', 'Bearer ' + token)
    responseData = request.urlopen(updateRequest).read().decode("UTF-8")
    #print('Response:' + str(responseData))
    if (responseData is None or len(responseData) < 1):
        print('updateValidationStatus returned an empty response!')
        return False
    response = json.loads(responseData)
    return response

def getUploadIfExists(token=None, url=None, fileName=None):
    try:
        existingUpload = getUploadByFilename(token=token, url=url, fileName=fileName)
        return existingUpload
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        else:
            raise

def deleteUpload(token=None, url=None, uploadId=None):
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)
    print('deleting upload by id:(' + str(uploadId) + ')')

    try:

        if token is None or len(token) < 1:
            print('Error. No login token available when Deleting upload.')
            return None


        fullUrl = str(url) + '/api/uploads/' + str(uploadId)
        body = {}

        encodedJsonData = str(json.dumps(body)).encode('utf-8')
        updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='DELETE')
        updateRequest.add_header('Content-Type', 'application/json')
        updateRequest.add_header('Authorization', 'Bearer ' + token)

        # TODO: Something weird happening with permissions etc. Debug this, this occurs when I "Edit" an antibody_csv file
        print('Delete Upload fullURL:(' + str(fullUrl) + ')')
        print('Delete Upload token:(' + str(token) + ')')
        print('Delete Upload updateRequest:(' + str(updateRequest) + ')')

        responseData = request.urlopen(updateRequest).read().decode("UTF-8")
        print('Response from deleting upload:' + str(responseData))
        if (responseData is None or len(responseData) < 1):
            print('updateValidationStatus returned an empty response!')
            return False
        response = json.loads(responseData)
        return response
    except Exception as e:
        print('Exception when deleting the upload:' + str(e))
        raise e

def getProjectID(configFileName='validation_config.yml', projectName=None):
    if(projectName is None):
        raise Exception('getProjectID: projectName is undefined.')

    # Get the project ID from the config
    try:
        print('Fetching project ID of ' + str(projectName) + ' from ' + str(configFileName))
        configStream = open(configFileName, 'r')
        configDict = yaml.load(configStream, Loader=yaml.FullLoader)
        #print('configDict:' + str(configDict)) # Dont print this, it contains passwords.
        projectID = configDict['project_id'][projectName]
        return projectID
    except Exception as e:
        print('Exception when loading project ID from config, does the config contain an entry for project_id:' + str(projectName) + '?:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


