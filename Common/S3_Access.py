import zipfile
from os.path import join
from sys import exc_info
import boto3
from boto3 import client
import io

try:
    import IhiwRestAccess
except Exception as e:
    print('S3_Access Failed in importing files: ' + str(e))
    from Common import IhiwRestAccess

s3 = client('s3')

def createProjectZipFile(bucket=None, projectIDs=None, url=None, token=None, fileTypeFilter=None):
    print('Creating Project Zip Files for project(s) ' + str(projectIDs))
    #print('URL=' + str(url))

    if url is None:
        url = IhiwRestAccess.getUrl()
        token = IhiwRestAccess.getToken(url=url)

    projectIDs = [str(projectID) for projectID in projectIDs]

    # Get a list of uploads
    print('Fetching Upload List...')
    if(fileTypeFilter is None):
        projectUploads = IhiwRestAccess.getUploadsByProjects(token=token,url=url,projectIDs=projectIDs)
    else:
        projectUploads = IhiwRestAccess.getFilteredUploads(token=token, url=url, projectIDs=projectIDs, uploadTypes=fileTypeFilter)


    print('I found ' + str(len(projectUploads)) + ' uploads for project IDs ' + str(projectIDs))

    # TODO: Sort by FileType? Maybe I should "Start" with Data matrices. Or Put them in Separate .zip by file size.
    # zipFileCounter=1
    # fileSizeLimit=10000

    zipFileName = 'Project.' + str('_'.join(projectIDs)) + '.Data.zip'


    # create zip file
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    for uploadIndex, projectUpload in enumerate(projectUploads):
    #for supportingFile in list(set(supportingUploadFilenames)):
        try:
            # TODO: Should I filter some files? Yeah probably, don't add .zip files, to avoid redundancy.
            # Sort into "subfolders" in .zip file
            supportingFileName = projectUpload['fileName']
            uploadType = str(projectUpload['type'])
            uploadProjectId = str(projectUpload['project']['id'])
            uploadProjectName = str(projectUpload['project']['name']).replace('.','').replace(' ','_').replace('-','_')
            #print('ProjectName=' + str(uploadProjectName))

            if (uploadIndex%100==0):
                #print('Adding file ' + str(supportingFile) + ' to ' + str(zipFileName))
                print('Progress = ' + str(uploadIndex) + '/' + str(len(projectUploads)) + ' = ' + str (100 * (uploadIndex/len(projectUploads))) + '%')

            supportingFileObject = s3.get_object(Bucket=bucket, Key=supportingFileName)
            fileNameWithRelativePath=join('project_' + str(uploadProjectName),join(uploadType,supportingFileName))
            supportingFileZip.writestr(fileNameWithRelativePath, supportingFileObject["Body"].read())

        except Exception as e:
            print('Exception when writing file to zip:\n' + str(e) + '\n' + str(exc_info()) )
            print('\nFilename:' + str(supportingFileName))

        # TODO: Add logic for maximum .zip file size.
        #  Note: make sure these newly created .zip files won't be included in the actual project .zip.


    print('Closing Zip File....')
    supportingFileZip.close()
    print('Writing file to bucket ' + str(bucket) + ' : ' + zipFileName)
    writeFileToS3(newFileName=zipFileName, bucket=bucket, s3ObjectBytestream=zipFileStream)

    # TODO: Make Upload Object for (each) project leader
    print('Done')

def writeFileToS3(s3ObjectBytestream=None, newFileName=None, bucket=None):
    print('Writing a file to S3:' + str(newFileName) + ' to bucket: ' + str(bucket))
    # print('The bytestream is of this type:' + str(type(s3ObjectBytestream)))
    try:
        s3 = boto3.resource("s3")
        print('saving file:' + str(newFileName))
        #print('bytestream has this type:' + str(type(s3ObjectBytestream)))
        # Some bytestream-like objects are different than others. Handle it nicely.
        if (type(s3ObjectBytestream) is io.BytesIO):
            body = s3ObjectBytestream.getvalue()
        else:
            body = s3ObjectBytestream
        # This is valid in the case of XL spreadsheets, which are io.BytesIO streams. different stream types might break this.
        #body = s3ObjectBytestream.getvalue()
        # This is for openpyxl bytestreams
        #body=s3ObjectBytestream
        s3.Bucket(bucket).put_object(Key=newFileName, Body=body)
        print('Done saving file.')
    except Exception as e:
        print('Problem saving file!\n' + str(e))

def getUploadListFromS3(bucket=None):
    print('Getting upload list from bucket:' + str(bucket))
    try:
        s3 = boto3.resource("s3")

        objectList = s3.Bucket(bucket).objects.all()

        print('Done getting Upload List.')

        return objectList
    except Exception as e:
        print('Problem saving file!\n' + str(e))

def revalidateUpload(bucket=None, uploadFilename=None):
    print('Touching the upload ' + str(uploadFilename) + ' in bucket ' + str(bucket))
    try:
        # TODO: Understand the difference between Resource and Client
        s3Resource = boto3.resource("s3")
        s3Client = client('s3')

        # Read ByteSteam
        fileObject = s3Client.get_object(Bucket=bucket, Key=uploadFilename)
        byteStream = fileObject["Body"].read()

        # Put the object back where I found it
        # TODO: Copying the object to itself, in place, does not trigger the cloudtrail, and the step functions.  "Put" does work
        s3Resource.Bucket(bucket).put_object(Key=uploadFilename, Body=byteStream)

    except Exception as e:
        print('Problem Revalidating Upload:\n' + str(e))

def getFileSize(bucket=None, uploadFilename=None):
    print('Getting the file size of the upload ' + str(uploadFilename) + ' in bucket ' + str(bucket))
    try:
        s3Client = client('s3')
        fileObject = s3Client.get_object(Bucket=bucket, Key=uploadFilename)
        fileSizeBytes=fileObject['ContentLength']
        # kilobytes = bytes/1024. We do Binary here
        return 1.0 * fileSizeBytes / 1024

    except Exception as e:
        print('Problem Getting File Size:\n' + str(e))
        return 0.0