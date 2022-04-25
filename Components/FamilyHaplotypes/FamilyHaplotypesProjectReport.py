from boto3 import client
#import json
#import urllib
from Common.S3_Access import writeFileToS3

try:
    import IhiwRestAccess
    import S3_Access
    import ParseXml

except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common import IhiwRestAccess
    from Common import S3_Access
    from Common import ParseXml

s3 = client('s3')

import zipfile
import io


def createFamilyHaplotypeReport(bucket=None, newline='\r\n', projectIDs=None, url=None, token=None, fileTypeFilter=None):
    print('Creating a Reference Cell Lines Report.')

    reportText = 'Family Haplotype Report' + newline + newline

    if(projectIDs is None):
        raise Exception('Cannot create report because you did not give me a project ID')
    elif(not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]
    projectIDs = [str(projectID) for projectID in projectIDs]

    if url is None:
        url=IhiwRestAccess.getUrl()
    if token is None:
        token=IhiwRestAccess.getToken(url=url)

    print('Website URL:' + str(url))
    print('bucket:' + str(bucket))

    for projectId in projectIDs:

        print('ProjectID:' + str(projectId))
        projectUploads = IhiwRestAccess.getFilteredUploads(projectIDs=[projectId], uploadTypes=fileTypeFilter, token=token, url=url)
    
        # Key = submitter ihiw_user.id, Value = Name, Lab, etc...
        userIDs = {}
        for upload in projectUploads:
            userIDs[upload['createdBy']['id']] = (
                'Uploads Created By: ' + upload['createdBy']['user']['firstName']
                + ' ' + upload['createdBy']['user']['lastName']
                + '\nUploader Email: ' + upload['createdBy']['user']['email']
                + '\nLab:\n' + upload['createdBy']['lab']['labCode']
                + '\n' + upload['createdBy']['lab']['department']
                + '\n' + upload['createdBy']['lab']['institution']
                + '\nLab Created By: ' + upload['createdBy']['lab']['firstName']
                + ' ' + upload['createdBy']['lab']['lastName']
                + '\nLab Director: ' + upload['createdBy']['lab']['director']
                + '\nLab Email: ' + upload['createdBy']['lab']['email']

            )

        print('Unique Submitter IDs:' + str(sorted(list(userIDs.keys()))))
        # for each submitter
        for userIndex, userID in enumerate(sorted(list(userIDs.keys()))):
            print('Finding Uploads for User:' + str(userID) + ' (' + str(userIndex + 1) + ' of ' + str(len(list(userIDs.keys()))) + ')')
    
            reportText += newline + 'User ' + str(userID) + '\n' + str(userIDs[userID]) + newline

            currentUserUploads =  [upload for upload in projectUploads if upload['createdBy']['id'] == userID]


            reportText += str(len(currentUserUploads)) + ' Uploads Files Submitted:' + newline
            for hmlUpload in currentUserUploads:
                reportText += '\t' + str(hmlUpload['fileName']) + ' : ' + str(hmlUpload['type']) + newline

    print('Report Text' + newline + reportText)
    writeFileToS3(s3ObjectBytestream=reportText, newFileName='Project.' + '_'.join(projectIDs) + '.Report.txt', bucket=bucket)