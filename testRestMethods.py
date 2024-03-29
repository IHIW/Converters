import argparse
from sys import exc_info
import time

from Common.IhiwRestAccess import createConvertedUploadObject, setValidationStatus, getUrl, getToken, getCredentials, \
    getUploadByFilename, deleteUpload, getUploadsByParentId, getUploads, getProjectID, getUploadsByProjectID, fixUpload, \
    getFilteredUploads, getUploadsByProjects, createProjectSummaryUploadObject
from Common.Validation import validateGlStrings
from OrphanedUploads.queryOrphanedUploads import queryOrphanedUploads
from Common.S3_Access import revalidateUpload


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", required=True, help="task to perform", type=str)
    parser.add_argument("-T", "--type", required=False, help="upload type", type=str)
    parser.add_argument("-u", "--upload", required=False, help="upload", type=str)
    parser.add_argument("-p", "--parent", required=False, help="parent upload name", type=str)
    parser.add_argument('-P','--project', required=False, help="project ID", type=str)
    parser.add_argument("-c", "--child", required=False, help="child upload name", type=str)
    parser.add_argument("-b", "--bucket", required=False, help="S3 Bucket Name", type=str )
    parser.add_argument("-d", "--default", required=False, help="default (Project ID) to use", type=str )
    parser.add_argument("-g", "--glstring", required=False, help="GLString", type=str )
    parser.add_argument("-v", "--verbose", help="verbose operation", action="store_true")

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

def testQueryOrphans(args=None):
    print('Testing the query to find orphaned uploads')
    print('Bucket:' + str(args.bucket))
    queryOrphanedUploads(bucket=args.bucket, verbose=args.verbose, defaultProjectID=args.default)

def testRevalidateUpload(args=None):
    print('Revalidating Upload')
    print('Bucket:' + str(args.bucket))
    print('Upload:' + str(args.upload))
    revalidateUpload(bucket=args.bucket, uploadFilename=args.upload)

def testGetChildUpload(args=None):
    print('Testing REST access to the website, testGetChildUpload')
    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)

    print('Getting the parent upload object:' + str(args.parent))
    response = getUploadByFilename(token=token, url=url, fileName = args.parent)
    #print('Response from getUploadByFilename:' + str(response))
    uploadId = str(response['id'])
    print('Upload '+str(args.parent) + ' has the id:' + uploadId)


    print('Getting Children using the new fast method:'  + str(uploadId))
    start = time.time()
    response = getUploadsByParentId(token=token, url=url, parentId=uploadId)
    print('Response from response:' + str(response))
    duration = time.time() - start
    print('That took ' + str(duration) + ' seconds.')


def testQueryUnvalidatedUploads(args=None):
    print('Looking for uploads without validation status')

    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)
    print('Quering URL ' + str(url))


    uploadList=[]
    projectIds = str(args.project).split(',')
    for projectID in projectIds :
        projectUploads = getUploadsByProjectID(url=url, token=token, projectId=projectID)
        if(projectUploads is not None):
            print('For Project ' + str(projectID) + ' I found ' + str(len(projectUploads)) + ' total uploads.')
            uploadList.extend(projectUploads)
        else:
            print('For Project ' + str(projectID) + ' there were zero uploads.')


    validatedUploads=[]
    unvalidatedUploads=[]
    antibodyCsvWithoutChildren=[]
    for upload in uploadList:
        validations = upload['validations']
        if(len(validations)<1):
            unvalidatedUploads.append(upload)
        else:
            validatedUploads.append(upload)


    print('There are ' + str(len(validatedUploads)) + ' validated uploads.\n')
    print('There are ' + str(len(unvalidatedUploads)) + ' unvalidated uploads, here are their names:')

    for upload in unvalidatedUploads:
        print(str(upload['fileName']))
        #print(str(upload))


def testGetProjectUploads(args=None):
    print('Getting Project Uploads for immunogenic_epitopes project:')
    projectId = getProjectID(projectName='immunogenic_epitopes')
    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)

    projectUploads = getUploadsByProjectID(url=url,token=token,projectId=projectId)

    if(projectUploads is not None):
        print('I found ' + str(len(projectUploads)) + ' uploads for project ' + str(projectId))

        for projectUpload in projectUploads:
            print(projectUpload['fileName'] + ' is of type ' + projectUpload['type'])
    else:
        raise Exception ('projectUploads received no response!')


def testFixUpload(args=None):
    uploadName = args.upload
    projectID = args.project
    uploadType = args.type

    print('I will fix this upload (' + str(uploadName) + ' by changing it to project ' + str(projectID) + ' and upload type ' + str(uploadType))
    fixUpload(uploadName=uploadName, projectID=projectID, uploadType=uploadType)


def testListUploads(args=None):
    projectIDs = str(args.project).split(',')
    uploadTypes = str(args.type).split(',')
    print('finding uploads for projects ' + str(projectIDs) + ' and upload types ' + str(uploadTypes))
    projectUploads = getUploadsByProjects(projectIDs=projectIDs)
    targetUploads=[]
    for projectUpload in projectUploads:
        if(projectUpload['type'] in uploadTypes):
            targetUploads.append(projectUpload)

    print('I found ' + str(len(targetUploads)) + ' uploads.')
    for targetUpload in targetUploads:
        print(targetUpload['fileName'] + ' : ' + targetUpload['type'] + ' : ' + str(targetUpload['project']['id']) )


def testCheckGLString(args=None):
    glString = args.glstring
    print('Validating this glstring:\n' + str(glString))
    isValid, validationFeedback = validateGlStrings(glStrings=[glString])

    print('isValid:' + str(isValid))
    print('validationFeedback:' + str(validationFeedback))


def testCreateNewUpload(args=None):
    print('Creating new upload:' + str(args.upload))

    createProjectSummaryUploadObject(projectId=int(args.project), newUploadFileName=str(args.upload), newUploadFileType="OTHER")


if __name__ == '__main__':
    print('Testing Rest Methods')

    try:
        args=parseArgs()
        task =args.task
        print('Task=' + str(task))
        if(task== 'CREATE_CHILD_UPLOAD'):
            testCreateChildUpload(args=args)
        elif(task== 'GET_CHILD_UPLOADS'):
            testGetChildUpload(args=args)
        elif(task == 'UPLOADS_BY_PROJECT'):
            testGetProjectUploads(args=args)
        elif (task == 'QUERY_ORPHANS'):
            testQueryOrphans(args=args)
        elif(task== 'QUERY_UNVALIDATED_UPLOADS'):
            testQueryUnvalidatedUploads(args=args)
        elif(task == 'REVALIDATE_UPLOAD'):
            testRevalidateUpload(args=args)
        elif (task == 'FIX_UPLOAD'):
            testFixUpload(args=args)
        elif (task == 'LIST_UPLOADS'):
            testListUploads(args=args)
        elif (task == 'CHECK_GLSTRING'):
            testCheckGLString(args=args)
        elif (task == 'CREATE_UPLOAD'):
            testCreateNewUpload(args=args)
        else:
            print('I do not understand which task to perform')

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise
