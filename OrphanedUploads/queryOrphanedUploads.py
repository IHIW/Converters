from datetime import datetime
from os import makedirs
from os.path import isdir, join


from Common.IhiwRestAccess import getCredentials, getUrl, getToken, getUploadIfExists, getUploads, getIhiwUserById
from Common.S3_Access import getUploadListFromS3


def queryOrphanedUploads(bucket=None, verbose=False,  defaultProjectID = None):
    print('Searching for Orphaned Uploads')

    objectListFromS3 = getUploadListFromS3(bucket=bucket)

    url = getUrl()
    token = getToken()

    uploadListFromDatabase = getUploads(token=token, url=url)

    queryText = ''

    nonHandleableFiles = set()

    # For each Upload on S3
    for uploadedFile in objectListFromS3:
        s3FileName = uploadedFile.key

        # Filter some of them (XSD files, etc.?)
        if str(s3FileName).startswith('schema/'):
            nonHandleableFiles.add(s3FileName)
            if(verbose):
                print('This is a Schema File:' + str(s3FileName))

        elif str(s3FileName).startswith('Project.') and (str(s3FileName).endswith('.xlsx') or str(s3FileName).endswith('.zip')):
            nonHandleableFiles.add(s3FileName)
            if(verbose):
                print('This is a Project Report File:' + str(s3FileName))

        elif str(s3FileName).startswith('ihiw.log.'):
            nonHandleableFiles.add(s3FileName)
            if(verbose):
                print('This is a Log File:' + str(s3FileName))

        elif str(s3FileName).endswith('Validation_Report.xlsx'):
                nonHandleableFiles.add(s3FileName)
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

                        # TODO: Check if the user actually exists.
                        # Because Sometimes the upoad was created in a test environment, but still using the staging bucket.
                        # I Think it will work if I'm using Admin credentials.

                        userFromWebsite = getIhiwUserById(token=token, url=url, ihiwUserId=numericalUserID)

                        if userFromWebsite is not None:

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
                                uploadType = 'PROJECT_DATA_MATRIX'
                            elif (nameTokens[2] == 'HAML'):
                                uploadType = 'HAML'
                            elif(nameTokens[2] == 'PED'):
                                uploadType = 'PED'

                            else:
                                if (verbose):
                                    print('Cannot convert to integers ' + str(s3FileName))
                                nonHandleableFiles.add(s3FileName)

                            uploadAge = datetime.now() - modifiedDate
                            uploadAgeDays = uploadAge.total_seconds() / 60.0 / 60.0 / 24.0
                            maximumAgeDays = 365
                            #print ('This upload date ' + modifiedDate.strftime("%Y-%m-%d %H:%M:%S") + ' is ' + str(uploadAgeDays) + ' days old.' )

                            # Lets just not worry about the older files.
                            if(uploadAgeDays > maximumAgeDays):
                                if (verbose):
                                    print('Skipping this upload because it is > ' + str(maximumAgeDays) + ' days old ' + str(s3FileName) + '(Created ' + modifiedDate.strftime("%Y-%m-%d %H:%M:%S")  + ')')
                                nonHandleableFiles.add(s3FileName)


                            # Skipping HAML files for now, maybe it's better to just re-convert them later.
                            elif(uploadType is not None and uploadType in ['HML','ANTIBODY_CSV', 'INFO_CSV','FASTQ','PED','PROJECT_DATA_MATRIX']):
                            #elif(uploadType is not None and uploadType in ['ANTIBODY_CSV']):
                                # Supposedly everything went well at this point.


                                #INSERT INTO ihiwManagement.upload (type, created_at, modified_at, file_name, enabled, created_by_id, project_id) VALUES ("HML", "2021-04-28 04:12:00", "2021-04-28 04:46:00", "FILENAME?????" ,1, 1, 1);
                                currentQueryText = ('INSERT INTO ihiwManagement.upload (type, created_at, modified_at, file_name, enabled, created_by_id, project_id) ' +
                                    'VALUES ("' + uploadType + '", "' + modifiedDate.strftime("%Y-%m-%d %H:%M:%S") + '", "' + modifiedDate.strftime("%Y-%m-%d %H:%M:%S") + '", "' +
                                    s3FileName + '" ,1, ' + str(ihiwUserID) + ', ' + str(int(defaultProjectID)) + ');\n')

                                queryText += currentQueryText
                            else:
                                if (verbose):
                                    print('Not the correct upload type: ' + str(s3FileName))
                                nonHandleableFiles.add(s3FileName)
                        else:
                            if (verbose):
                                print('Ihiw User ID (' + str(ihiwUserID) + ') could not be found ' + str(s3FileName))
                            nonHandleableFiles.add(s3FileName)

                    except ValueError:
                        if (verbose):
                            print('Cannot convert to integers ' + str(s3FileName))
                        nonHandleableFiles.add(s3FileName)
                else:
                    if (verbose):
                        print('Cannot parse upload info for ' + str(s3FileName))
                    nonHandleableFiles.add(s3FileName)


    #print('\nThis is the resulting sql query:\n\n' + str(queryText))

    outputdir = 'SqlOutput'
    if not isdir(outputdir):
        makedirs(outputdir)

    queryFileName = join(outputdir,('OrphanedUploads.' + str(bucket) + '.' + str(url) + '.sql').replace('https://','').replace('/','').replace('\\',''))

    with open(queryFileName, 'w') as outputFile:
        outputFile.write(queryText)

    stillOrphansFilename = join(outputdir,('OrphanedUploads.' + str(bucket) + '.' + str(url) + '.Orphans.txt').replace('https://','').replace('/','').replace('\\',''))

    with open(stillOrphansFilename, 'w') as outputFile:
        outputFile.write(str('\n'.join(sorted(list(nonHandleableFiles)))))
