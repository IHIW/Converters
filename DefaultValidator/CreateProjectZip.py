from sys import exc_info
import zipfile
import io

try:
    import IhiwRestAccess
    import S3_Access
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common import IhiwRestAccess
    from Common import S3_Access

def createZipFile(oldFileName=None, newFileName=None, projectId=None, url=None, token=None, bucket=None, newline='\n'):
    print('Creating Zip File (' + str(newFileName) + ')')

    # Initialize my Zip Files
    zipFileHmlStream = io.BytesIO()
    fileZip = zipfile.ZipFile(zipFileHmlStream, 'a', zipfile.ZIP_DEFLATED, False)

    # Declare report
    reportText = 'Project Summary Zip File Content Summary' + newline + newline + 'Laboratory,Submitter,UploadName,UploadType,Size(KB)' + newline

    # Get Uploads
    projectUploads = IhiwRestAccess.getFilteredUploads(projectIDs=[projectId], uploadTypes=None, token=token, url=url)
    totalFileCount = len(projectUploads)

    # Loop Uploads
    for uploadIndex, upload in enumerate(projectUploads):

        if uploadIndex % 500 == 0:
            print('Zipping upload # ' + str(uploadIndex) + '/' + str(len(projectUploads)))
            print('Some upload info:')
            print(str(upload))

        laboratory = upload['createdBy']['lab']['institution']
        labId = str(upload['createdBy']['lab']['id'])
        submitter = upload['createdBy']['user']['firstName'] + ' ' + upload['createdBy']['user']['lastName']
        uploadName = str(upload['fileName'])
        uploadType = str(upload['type'])

        if (uploadName == newFileName or uploadName == oldFileName):
            print('Skipping file ' + str(uploadName))
        else:
            uploadData = S3_Access.getFile(bucket=bucket, uploadFilename=uploadName)
            try:
                fileSizeKB = 1.0 * uploadData['ContentLength'] / 1024

                if fileSizeKB > 4000:
                    fileSizeKB = str(fileSizeKB) + ' (Not included in ZIP file)'
                else:
                    fileText = uploadData["Body"].read()
                    fileZip.writestr('Lab_' + str(labId) + '/' + uploadName, fileText)

            except Exception as e:
                print('Cannot determine file size of upload ' + str(uploadName))
                fileSizeKB = 0

            reportText +=  str(labId) + ': ' + laboratory + ',' + submitter + ',' + uploadName + ',' + uploadType  + ',' +  str(fileSizeKB) + newline

    # Add report to zip
    fileZip.writestr('ContentSummary.csv', reportText)

    fileZip.close()
    S3_Access.writeFileToS3(newFileName=newFileName, bucket=bucket, s3ObjectBytestream=zipFileHmlStream)

    # TODO: Delete the temporary zip. It's very small (size 0) so maybe it can just stay...

    return totalFileCount

def create_project_zip_handler(event, context):
    print('I found the handler for creating zip files.')
    uploadDetails={}

    try:
        # Fetching the upload detail bundle from the step function payload
        if "Input" in event and "Payload" in event['Input']:
            uploadDetails = event['Input']['Payload']
            oldFileName = uploadDetails['file_name']
            print('old file name:' + str(oldFileName))
            projectId = oldFileName.replace('.Downloads.zip.TEMP','').replace('Project.','')
            print('projectId:' + str(projectId))
            newFileName = oldFileName.replace('.Downloads.zip.TEMP','.Downloads.zip')
            print('new file name:' + str(newFileName))

            uploadFileCount = createZipFile(oldFileName=oldFileName, newFileName=newFileName, projectId=projectId, url=uploadDetails['url'], token=uploadDetails['token'], bucket=uploadDetails['bucket'])

            uploadDetails['is_valid'] = True
            uploadDetails['file_name'] = newFileName
            uploadDetails['validation_feedback'] = 'Project Zip File containing ' + str(uploadFileCount) + ' files Created Successfully.'
            uploadDetails['validator_type'] = 'PROJECT_ZIP'

        else:
            uploadDetails['is_valid'] = False
            uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the default validation part of the step function flow.'
            uploadDetails['validator_type'] = 'PROJECT_ZIP'
            print(str(uploadDetails['validation_feedback']))
            return uploadDetails

    except Exception as e:
        exceptionText = 'Exception:\n' + str(e) + '\n' + str(exc_info())
        print(exceptionText)
        uploadDetails['is_valid'] = False
        uploadDetails['validation_feedback'] = exceptionText
        uploadDetails['validator_type'] = 'PROJECT_ZIP'

    return uploadDetails

