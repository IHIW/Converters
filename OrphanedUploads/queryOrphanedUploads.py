from Common.IhiwRestAccess import getCredentials, getUrl, getToken, getUploadIfExists
from Common.S3_Access import getUploadListFromS3


def queryOrphanedUploads(bucket=None):
    print('Searching for Orphaned Uploads')

    objectList = getUploadListFromS3(bucket=bucket)

    for uploadedObject in objectList:
        s3FileName = uploadedObject.key
        print('Here is one upload:' + str(s3FileName))

    url = getUrl()
    token = getToken()

    uploadList = getUploads