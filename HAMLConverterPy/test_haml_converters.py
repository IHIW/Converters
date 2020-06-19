try:
    from IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common.IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials



def testRestAccess():
    print('Testing REST access to the website')
    (user, password) = getCredentials(configFileName='converter_config.yml')
    url = getUrl(configFileName='converter_config.yml')
    token = getToken(user=user, password=password, url=url)

    response = createConvertedUploadObject(newUploadFileName='test.generated.upload.haml', previousUploadFileName='	1_1592339213839_HAML_HLAM_Fusion.csv', token=token, url=url)

if __name__ == '__main__':
    testRestAccess()