from datetime import datetime

from Common.IhiwRestAccess import getCredentials, getUrl, getToken, getUploadIfExists, getUploads
from Common.S3_Access import getUploadListFromS3


def queryOrphanedUploads(bucket=None, verbose=False):
    print('Searching for Orphaned Uploads')

    objectListFromS3 = getUploadListFromS3(bucket=bucket)

    url = getUrl()
    token = getToken()

    uploadListFromDatabase = getUploads(token=token, url=url)

    queryText = ''

    nonHandleableFiles = []

    # For each Upload on S3
    for uploadedFile in objectListFromS3:
        s3FileName = uploadedFile.key

        # Filter some of them (XSD files, etc.?)
        if str(s3FileName).startswith('schema/'):
            nonHandleableFiles.append(s3FileName)
            if(verbose):
                print('This is a Schema File:' + str(s3FileName))

        elif str(s3FileName).startswith('Project.') and (str(s3FileName).endswith('.xlsx') or str(s3FileName).endswith('.zip')):
            nonHandleableFiles.append(s3FileName)
            if(verbose):
                print('This is a Project Report File:' + str(s3FileName))

        elif str(s3FileName).startswith('ihiw.log.'):
            nonHandleableFiles.append(s3FileName)
            if(verbose):
                print('This is a Log File:' + str(s3FileName))

        elif str(s3FileName).endswith('Validation_Report.xlsx'):
                nonHandleableFiles.append(s3FileName)
                if (verbose):
                    print('This is a Validation Report:' + str(s3FileName))


        else:
            # Does it have an upload assigned?
            uploadFound = False

            for upload in uploadListFromDatabase:
                uploadFileName = upload['fileName']
                if(s3FileName == str(uploadFileName)):
                    uploadFound = True

                    break

            if(uploadFound):
                if (verbose):
                    print('An upload Object already exists for ' + str(s3FileName))
            else:
                if (verbose):
                    print('Handling this file with missing Upload Database Entry:' + str(s3FileName))

                nameTokens = s3FileName.split('_')
                if len(nameTokens) > 1:
                    #return currentIhiwUser.getId() + "_" + System.currentTimeMillis() + "_" + upload.getType() + "_" + file.getOriginalFilename();
                    try:
                        ihiwUserID = nameTokens[0]
                        numericalUserID = int(ihiwUserID)

                        currentMillis = nameTokens[1]
                        numericalCurrentMillis = int(currentMillis)
                        modifiedDate = datetime.fromtimestamp(numericalCurrentMillis / 1000.0)

                        uploadType = None
                        # Get Upload Type
                        if(nameTokens[2] == 'HML'):
                            uploadType = 'HML'
                        elif (nameTokens[2] == 'ANTIBODY' and nameTokens[3] == 'CSV'):
                            uploadType = 'ANTIBODY_CSV'
                        elif (nameTokens[2] == 'INFO' and nameTokens[3] == 'CSV'):
                            uploadType = 'INFO_CSV'
                        elif (nameTokens[2] == 'FASTQ'):
                            uploadType = 'FASTQ'
                        elif (nameTokens[2] == 'PROJECT' and nameTokens[3] == 'DATA' and nameTokens[4] == 'MATRIX'):
                            uploadType = 'ANTIBODY_CSV'
                        elif (nameTokens[2] == 'HAML'):
                            uploadType = 'HAML'
                        elif(nameTokens[2] == 'PED'):
                            uploadType = 'PED'

                        else:
                            if (verbose):
                                print('Cannot convert to integers ' + str(s3FileName))
                            nonHandleableFiles.append(s3FileName)

                        if(uploadType is not None):
                            # Supposedly everything went well at this point.

                            defaultProjectID = 1

                            #INSERT INTO ihiwManagement.upload (type, created_at, modified_at, file_name, enabled, created_by_id, project_id) VALUES ("HML", "2021-04-28 04:12:00", "2021-04-28 04:46:00", "FILENAME?????" ,1, 1, 1);
                            currentQueryText = ('INSERT INTO ihiwManagement.upload (type, created_at, modified_at, file_name, enabled, created_by_id, project_id) ' +
                                'VALUES ("' + uploadType + '", "' + modifiedDate.strftime("%Y-%m-%d %H:%M:%S") + '", "' + modifiedDate.strftime("%Y-%m-%d %H:%M:%S") + '", "' +
                                s3FileName + '" ,1, ' + str(ihiwUserID) + ', ' + str(defaultProjectID) + ');\n')

                            queryText += currentQueryText
                    except ValueError:
                        if (verbose):
                            print('Cannot convert to integers ' + str(s3FileName))
                        nonHandleableFiles.append(s3FileName)
                else:
                    if (verbose):
                        print('Cannot parse upload info for ' + str(s3FileName))
                    nonHandleableFiles.append(s3FileName)


    print('\nThis is the resulting sql query:\n\n' + str(queryText))

    print('\nI could not handle these files\n\n' + str('\n'.join(sorted(nonHandleableFiles))))