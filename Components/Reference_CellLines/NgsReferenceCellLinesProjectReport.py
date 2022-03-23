from boto3 import client
#import json
#import urllib


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
from sys import exc_info

import zipfile
import io
from time import sleep


def reference_cell_line_project_report_handler(event, context):
    print('Lambda handler: Creating a project report for reference_cell_lines.')
    # This is the AWS Lambda handler function.
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        sleep(1)
        print('This Lambda handler has not been implemented yet.')
        # TODO: get the bucket from the sns message ( there is no sns message, trigger one?)
        #bucket = content['Records'][0]['s3']['bucket']['name']
        #bucket = 'ihiw-management-upload-prod'
        #bucket = 'ihiw-management-upload-staging'

        #adminUserID=

        #createImmunogenicEpitopesReport(bucket=bucket)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


def createReferenceCellLinesReport(bucket=None, newline='\r\n'):
    print('Creating a Reference Cell Lines Report.')

    reportText = 'NGS HLA genes typing of Reference Cell Lines and Quality Control Project Report' + newline + newline

    # TODO: FileSize?
    sampleSummaryText = 'UserID,UserName+Lab,UploadName,UploadType,PT/QC,UNK,SampleIDs' + newline

    # Initialize my Zip Files
    zipFileHmlStream = io.BytesIO()
    hmlFileZip = zipfile.ZipFile(zipFileHmlStream, 'a', zipfile.ZIP_DEFLATED, False)
    # TODO: A .Fastq zip as well? Multiple? It is big.

    url=IhiwRestAccess.getUrl()
    token=IhiwRestAccess.getToken(url=url)
    print('Website URL:' + str(url))
    print('bucket:' + str(bucket))
    refCellLineProjectID = IhiwRestAccess.getProjectID(projectName='reference_cell_line')

    projectHMLUploads = IhiwRestAccess.getFilteredUploads(projectIDs=[refCellLineProjectID], uploadTypes='HML', token=token, url=url)
    projectFastqUploads = IhiwRestAccess.getFilteredUploads(projectIDs=[refCellLineProjectID], uploadTypes='FASTQ', token=token, url=url)

    reportText += 'Total HML Files submitted: ' + str(len(projectHMLUploads)) + newline
    reportText += 'Total FASTQ Files submitted: ' + str(len(projectFastqUploads)) + newline

    # Key = submitter ihiw_user.id, Value = Name, Lab
    userIDs = {}
    for upload in projectHMLUploads:
        userIDs[upload['createdBy']['id']] = upload['createdBy']['user']['firstName'] + ' ' + upload['createdBy']['user']['lastName'] + ': ' + upload['createdBy']['lab']['institution']
    for upload in projectFastqUploads:
        userIDs[upload['createdBy']['id']] = upload['createdBy']['user']['firstName'] + ' ' + upload['createdBy']['user']['lastName'] + ': ' + upload['createdBy']['lab']['institution']
    print('Unique Submitter IDs:' + str(sorted(list(userIDs.keys()))))

    # for each submitter
    for userIndex, userID in enumerate(sorted(list(userIDs.keys()))):
        print('Finding Uploads for User:' + str(userID) + ' (' + str(userIndex + 1) + ' of ' + str(len(list(userIDs.keys()))) + ')')

        reportText += newline + 'User ' + str(userID) + ' (' + str(userIDs[userID]) + ')' + newline

        currentUserHMLs =  [hmlUpload for hmlUpload in projectHMLUploads if hmlUpload['createdBy']['id'] == userID]
        reportText += str(len(currentUserHMLs)) + ' HML Files Submitted:' + newline
        for hmlUpload in currentUserHMLs:
            reportText += '\t' + str(hmlUpload['fileName']) + newline

            sampleSummaryText += str(userID) + ',' + str(userIDs[userID]) + ',' + str(hmlUpload['fileName'])  + ',HML,'



            # Get HML Information, especially Sample IDs.
            xmlFileObject = None
            sampleIds=''
            isPTQC=''
            isUNK = ''

            try:
                hmlFileObject = s3.get_object(Bucket=bucket, Key=hmlUpload['fileName'])
                hmlText=hmlFileObject["Body"].read()
                hmlFileZip.writestr(hmlUpload['fileName'], hmlText)

                sampleIds = ' ; '.join(ParseXml.getSampleIDs(xmlText=hmlText))

                if ('PT' in sampleIds.upper() or 'PT' in hmlUpload['fileName'].upper()
                    or 'QC' in sampleIds.upper() or 'QC' in hmlUpload['fileName'].upper()):
                    isPTQC='YES'

                if ('UNK' in sampleIds.upper() or 'UNK' in hmlUpload['fileName'].upper()):
                    isUNK = 'YES'

            except Exception as err:
                reportText += 'Could not fetch upload from S3: ' + str(hmlUpload['fileName'])

            sampleSummaryText += str(isPTQC) + ',' + str(isUNK) + ',' + str(sampleIds) + newline


        currentUserFASTQs = [fastqUpload for fastqUpload in projectFastqUploads if fastqUpload['createdBy']['id'] == userID]
        reportText += str(len(currentUserFASTQs)) + ' FASTQ Files Submitted:' + newline
        for fastqUpload in currentUserFASTQs:
            reportText += '\t' + str(fastqUpload['fileName']) + newline

            isPTQC=''
            isUNK=''
            if ('PT' in fastqUpload['fileName'].upper() or 'QC' in fastqUpload['fileName'].upper()):
                isPTQC = 'YES'

            if ('UNK' in fastqUpload['fileName'].upper()):
                isUNK = 'YES'

            sampleSummaryText += str(userID) + ',' + str(userIDs[userID]) + ',' + str(fastqUpload['fileName']) + ',FASTQ,' +  str(isPTQC) + ',' + str(isUNK) + ',' + ',' + newline

    hmlFileZip.writestr('SummaryReport.txt', reportText)
    hmlFileZip.writestr('SampleSummary.csv', sampleSummaryText)

    hmlFileZip.close()
    S3_Access.writeFileToS3(newFileName='Project.NGS.RefCellLines.HMLs.zip', bucket=bucket, s3ObjectBytestream=zipFileHmlStream)


    # TODO: Find Project Leader

        # TODO: Change the rest method to create upload, to allow the validation user? Or else I need admin rights...
        # TODO: Create Upload Object for the Leader (if possible?)

    #print('Report Text:' + str(reportText))






