from Common.IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadByFilename, deleteUpload

def testCreateChildUpload(parentUploadFileName = None, childUploadFileName=None):
    print('Testing REST access to the website, createChildUpload')
    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)

    # TODO: Fix the createNewUploadObject Method, use it here. That method is currently broken so I need to supply an existing upload filename.
    # print('Creating Parent Upload:' + str(parentUploadFileName))

    # Create Child Upload
    print('Creating Child Upload:' + str(childUploadFileName))
    response = createConvertedUploadObject(newUploadFileName=childUploadFileName, newUploadFileType='XLSX', previousUploadFileName=parentUploadFileName, token=token, url=url)
    print('Response from createConvertedUploadObject:' + str(response))

    print('Setting validation status of the parent file:' + str(parentUploadFileName))
    isParentValid=True
    parentValidationStatus='This parent file looks quite valid indeed'
    response = setValidationStatus(uploadFileName=parentUploadFileName, isValid=isParentValid, validationFeedback=parentValidationStatus, validatorType='TEST_VALIDATOR', token=token, url=url)
    print('Response from setValidationStatus:' + str(response))

    isChildValid=False
    childValidationStatus='This child file has some validation issues:\n1) It is the wrong format\n2) There were other problems found.'
    response = setValidationStatus(uploadFileName=childUploadFileName, isValid=isChildValid, validationFeedback=childValidationStatus, validatorType='TEST_VALIDATOR', token=token, url=url)
    print('Response from setValidationStatus:' + str(response))


def testDeleteUpload(uploadFileName=None):
    print('Testing REST access to the website, testDeleteUpload')
    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)

    print('Getting an upload object:' + str(uploadFileName))
    response = getUploadByFilename(token=token, url=url, fileName = uploadFileName)
    #print('Response from getUploadByFilename:' + str(response))
    uploadId = str(response['id'])
    print('Upload '+str(uploadFileName) + ' has the id:' + uploadId)

    print('Deleting upload:' + str(uploadId))
    response = deleteUpload(uploadId=uploadId, token=token, url=url)
    print('Response from response:' + str(response))


if __name__ == '__main__':
    print('Hello World!')
    parentUploadFileName = '11_1627546967381_HML_Gendx_Ref3.hml'
    #parentUploadFileName = '1497_1627550689215_HML_Gendx_Ref3.hml'
    #parentUploadFileName = '1592_1627552367919_HML_Gendx_Ref3.hml'
    childUploadFileName = 'childfilename4.xlsx'

    testCreateChildUpload(parentUploadFileName=parentUploadFileName, childUploadFileName = childUploadFileName)

    testDeleteUpload(uploadFileName=childUploadFileName)
