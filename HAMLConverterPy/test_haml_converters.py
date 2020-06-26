try:
    from IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadByFilename
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common.IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadByFilename



def testRestAccess():
    print('Testing REST access to the website')
    (user, password) = getCredentials(configFileName='converter_config.yml')
    url = getUrl(configFileName='converter_config.yml')
    token = getToken(user=user, password=password, url=url)

    #response = createConvertedUploadObject(newUploadFileType='HML', previousUploadFileName='1497_1593086716939_HAML_immunogenic_bad1.xlsx', token=token, url=url)
    #print('Response from createConvertedUploadObject:' + str(response))

    response = getUploadByFilename(fileName='1_1592339213839_HAML_HLAM_Fusion.csv.haml', token=token, url=url)
    print('Response from createConvertedUploadObject:' + str(response))

if __name__ == '__main__':
    testRestAccess()