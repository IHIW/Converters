import yaml
import ast
import json
from sys import exc_info

try:
    import urllib
    from urllib import request
except Exception as e:
    print('Warning, packages urllib and request are not available.')

try:
    from requests_toolbelt import MultipartEncoder
    import requests
except Exception as e:
    print('Warning, packages requests and requests_toolbelt are not available.')

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

def getUploads(token=None, url=None, timeout=120):
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)

    if token is None or len(token) < 1:
        print('Error. No login token available when getting uploads.')
        return None

    print('Fetching All Uploads, timeout = ' + str(timeout) + ' seconds')

    fullUrl = str(url) + '/api/uploads'
    body = {}

    encodedJsonData = str(json.dumps(body)).encode('utf-8')
    updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='GET')
    updateRequest.add_header('Content-Type', 'application/json')
    updateRequest.add_header('Authorization', 'Bearer ' + token)
    responseData = request.urlopen(updateRequest, timeout=timeout).read().decode("UTF-8")
    #print('Response:' + str(responseData))
    if (responseData is None or len(responseData) < 1):
        print('updateValidationStatus returned an empty response!')
        return False
    response = json.loads(responseData)

    #print('uploadListResponse:' + str(response))

    print('Done, I found (' + str(len(response)) + ' uploads')

    return response

def getFilteredUploads(projectIDs=[], uploadTypes=None, token=None, url=None):
    if(projectIDs is None):
        raise Exception('I need a project ID to filter on.')
    elif(not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]

    if(uploadTypes is None):
        uploadTypes = []
    elif(not isinstance(uploadTypes, list)):
        uploadTypes = [uploadTypes]

    # Convert to String for consistency..
    projectIDs = [str(projectID) for projectID in projectIDs]
    uploadTypes = [str(uploadType) for uploadType in uploadTypes]

    # Get Uploads
    filteredUploadList = []
    for projectID in projectIDs:
        uploadList = getUploadsByProjectID(token=token, url=url, projectId=projectID)

        if uploadList is not None:
            for upload in uploadList:
                uploadType = str(upload['type'])
                if (uploadTypes is None or len(uploadTypes)==0 or uploadType in uploadTypes):
                    filteredUploadList.append(upload)
                else:
                    pass

    print('I found a total of ' + str(len(filteredUploadList)) + ' filtered uploads for projects ' + str(projectIDs) + ' and upload types ' + str(uploadTypes) +'.\n')
    return filteredUploadList

def getIhiwUserById(token=None, url=None, ihiwUserId=None):
    if(url is None):
        url = getUrl()
    if(token is None):
        token = getToken(url=url)

    if token is None or len(token) < 1:
        print('Error. No login token available when getting uploads.')
        return None

    try:
        fullUrl = str(url) + '/api/ihiw-users/' + str(ihiwUserId)
        body = {}

        encodedJsonData = str(json.dumps(body)).encode('utf-8')
        updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='GET')
        updateRequest.add_header('Content-Type', 'application/json')
        updateRequest.add_header('Authorization', 'Bearer ' + token)
        responseData = request.urlopen(updateRequest).read().decode("UTF-8")
        #print('Response:' + str(responseData))
        if (responseData is None or len(responseData) < 1):
            print('getIhiwUserById returned an empty response!')
            return False
        response = json.loads(responseData)

        return response
    except urllib.error.HTTPError as e:
        print(str(e) + ' when searching for user ' + str(ihiwUserId))
        return None

def getUploadsByParentId(token=None, url=None, parentId=None):
    if (url is None):
        url = getUrl()
    if (token is None):
        token = getToken(url=url)

    if parentId is None:
        print('Parent ID is none, cannot find any uploads with this parent')
        return None
    else:
        if token is None or len(token) < 1:
            print('Error. No login token available when getting uploads.')
            return None

        try:
            fullUrl = str(url) + '/api/uploads/children/' + urllib.parse.quote(str(parentId))
            body = {}

            encodedJsonData = str(json.dumps(body)).encode('utf-8')
            updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='GET')
            updateRequest.add_header('Content-Type', 'application/json')
            updateRequest.add_header('Authorization', 'Bearer ' + token)
            responseData = request.urlopen(updateRequest).read().decode("UTF-8")
            # print('Response:' + str(responseData))
            if (responseData is None or len(responseData) < 1):
                print('getUploadsByParentId returned an empty response!')
                return False
            response = json.loads(responseData)

            return response
        except urllib.error.HTTPError as e:
            print(str(e) + ' when searching for children of upload ' + str(parentId))
            return None

def getUploadsByProjectID(token=None, url=None, projectId=None):
    if (url is None):
        url = getUrl()
    if (token is None):
        token = getToken(url=url)

    if(projectId is None):
        print('Warning! No projectId was provided, cannot find uploads.')
        return None
    else:
        if token is None or len(token) < 1:
            print('Error. No login token available when getting uploads.')
            return None

        try:
            fullUrl = str(url) + '/api/uploads/getbyproject/' + urllib.parse.quote(str(projectId))
            body = {}

            encodedJsonData = str(json.dumps(body)).encode('utf-8')
            updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='GET')
            updateRequest.add_header('Content-Type', 'application/json')
            updateRequest.add_header('Authorization', 'Bearer ' + token)
            responseData = request.urlopen(updateRequest).read().decode("UTF-8")
            # print('Response:' + str(responseData))
            if (responseData is None or len(responseData) < 1):
                print('getUploadsByProjectId returned an empty response!')
                return False
            response = json.loads(responseData)

            return response
        except urllib.error.HTTPError as e:
            print(str(e) + ' when searching for uploads by project ' + str(projectId))
            return None


# TODO: I deprecated this method, delete it at some point. Use getFilteredUploads instead. These methods had almost the same logic.
def getUploadsByProjects(token=None, url=None, projectIDs=None):
    raise Exception ('getUploadsByProjects is deprecated, use getFilteredUploads instead.')


def getUploadFileNamesByPartialKeyword(token=None, url=None, fileNameQueries=None, projectIDs=None, allUploads=None, uploadTypeFilter=None, uploadUser=None):
    # Make lists of the filter options.
    if(projectIDs is not None and not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]
    if(uploadTypeFilter is not None and not isinstance(uploadTypeFilter, list)):
        uploadTypeFilter = [uploadTypeFilter]
    if(uploadUser is not None and not isinstance(uploadUser, list)):
        uploadUser = [uploadUser]
    if(fileNameQueries is not None and not isinstance(fileNameQueries, list)):
        fileNameQueries = [fileNameQueries]

    # Convert to String for consistency..
    if(projectIDs is not None):
        projectIDs = [str(projectID) for projectID in projectIDs]
    if(uploadTypeFilter is not None):
        uploadTypeFilter = [str(uploadType) for uploadType in uploadTypeFilter]
    if(uploadUser is not None):
        uploadUser = [str(userId) for userId in uploadUser]

    if token is None or len(token) < 1:
        print('Error. No login token available when getting uploads by partial keyword.')
        return None

    #print('Checking IDS:' + str(projectIDs))
    if fileNameQueries is None:
        print('fileNameQueries is none, cannot find any uploads without any filename queries')
        return None
    else:
        if(allUploads is None):
            # TODO: This should not be getting all uploads, get uploads by projects instead.
            #allUploads=getUploads(token=token,url=url)
            raise Exception('In getUploadFileNamesByPartialKeyword, Switch from getUploads to getUploadsByProject')

        uploadList = []

        for upload in allUploads:
            #print('Checking upload:' + str(upload))

            projectID = str(upload['project']['id'])
            #print('upload:' + str(upload))

            if((projectIDs is None or projectID in projectIDs)
                and (uploadTypeFilter is None or str(upload['type']) in uploadTypeFilter)
                and (uploadUser is None or str(upload['createdBy']['id']) in uploadUser)
            ):
                # Check the filename as a secondary step.
                for fileNameQuery in fileNameQueries:
                    if(upload['fileName'] is not None
                        and fileNameQuery.lower() in str(upload['fileName']).lower()):

                        uploadList.append(upload)

                        # Also append the children of this upload
                        childUploads = getUploadsByParentId(token=token, url=url, parentId=upload['id'])
                        for childUpload in childUploads:
                            uploadList.append(childUpload)
                        break
            else:
                pass

        # TODO: What if there are duplicate files? will list(set(list)) work? This could cause a bug when adding files to the zip. Not sure.

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
        return str(projectID)
    except Exception as e:
        print('Exception when loading project ID from config, does the config contain an entry for project_id:' + str(projectName) + '?:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def fixUpload(uploadName=None, uploadType=None, projectID=None, url=None, token=None):
    if (url is None):
        url = getUrl()
    if (token is None):
        token = getToken(url=url)

    oldUpload = getUploadByFilename(url=url, token=token, fileName=uploadName)
    print('Found this upload:' + str(oldUpload))
    newUpload = {}
    newUpload['id'] = oldUpload['id']
    newUpload['fileName'] = oldUpload['fileName']

    if(uploadType is not None):
        print('Changing upload type from ' + str(oldUpload['type']) + ' to ' + str(uploadType))
        newUpload['type'] = str(uploadType)
    else:
        newUpload['type'] = oldUpload['type']

    newUpload['project']={}
    if(projectID is not None):
        print('Changing upload project id from ' + str(oldUpload['project']['id']) + ' to ' + str(projectID))
        newUpload['project']['id'] = int(str(projectID))
    else:
        newUpload['project']['id'] = oldUpload['project']['id']

    # Save Upload.
    try:
        print('Saving Upload:' + str(oldUpload))

        fullUrl = str(url) + '/api/uploads'

        body = {
            'upload': newUpload
        }


        print('body:' + str(body))
        encodedJsonData = str(json.dumps(body)).encode('utf-8')

        #pretendFile=StringIO('Hello World')

        '''m = MultipartEncoder(
            fields={'upload': '1499', 'file': pretendFile}
        )'''

        #print ('m:' + str(m))
        #response = requests.put(fullUrl, data=m,  headers={'Content-Type': 'multipart/form-data','Authorization': 'Bearer ' + token})

        # TODO: This is not working. It needs to be a multipart request, but excluding the optional file attribute. Haven't quite figured that out yet.
        #response = requests.put(fullUrl, data=body, files={'file':None}, headers={'Content-Type': 'multipart/form-data','Authorization': 'Bearer ' + token})
        raise Exception('FixReport is not working yet. Needs a multipart request.')


        '''
        updateRequest = request.Request(url=fullUrl, data=encodedJsonData, method='PUT')
        #updateRequest.add_header('Content-Type', 'application/json')
        updateRequest.add_header('Content-Type', 'multipart/form-data')
        #updateRequest.add_header('Content-Type', 'application/octet-stream')
        updateRequest.add_header('Authorization', 'Bearer ' + token)

        responseData = request.urlopen(updateRequest).read().decode("UTF-8")
        if (responseData is None or len(responseData) < 1):
            print('updateValidationStatus returned an empty response!')
            return False
        response = json.loads(responseData)
        '''

        print('Received response from updateUpload:' + str(response))


    except SyntaxError as e:
        print('Syntax error when Saving Upload from request:\n' + str(e) + '\n' + str(exc_info()))
        return False
    except urllib.error.HTTPError as e:
        print('HTTP error when Saving Upload for upload file ' + str(uploadName) + ' : ' + str(e))
        return False
    except Exception as e:
        print('Error when Saving Upload :\n' + str(e) + '\n' + str(exc_info()))
        return False