import argparse
from sys import exc_info

from Common.IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, getUploadByFilename, deleteUpload

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", required=True, help="task to perform", type=str)
    parser.add_argument("-p", "--parent", required=False, help="parent upload name", type=str)
    parser.add_argument("-c", "--child", required=False, help="child upload name", type=str)
    parser.add_argument("-b", "--bucket", required=False, help="S3 Bucket Name", type=str )

    return parser.parse_args()

def testCreateChildUpload(args = None):
    print('Testing REST access to the website, createChildUpload')
    parentUploadFileName = args.parent
    childUploadFileName = args.child

    if(parentUploadFileName is None or len(parentUploadFileName) < 1):
        raise Exception ('Need Parent Upload Filename ("parent" arg).')

    if(childUploadFileName is None or len(childUploadFileName) < 1):
        raise Exception ('Need Child Upload Filename ("child" arg).')

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
    print('Testing Rest Methods')

    try:
        args=parseArgs()
        task =args.task
        print('Task=' + str(task))
        if(task== 'CREATE_CHILD_UPLOAD'):
            testCreateChildUpload(args=args)
        else:
            print('I do not understand which task to perform')


    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise







