from boto3 import client
#import json
#import urllib


try:
    import IhiwRestAccess
    import S3_Access

except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common import IhiwRestAccess
    from Common import S3_Access

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

    # Initialize my Zip Files
    zipFileHmlStream = io.BytesIO()
    hmlFileZip = zipfile.ZipFile(zipFileHmlStream, 'a', zipfile.ZIP_DEFLATED, False)
    # TODO: A .Fastq zip as well?

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
        userIDs[upload['createdBy']['id']] = upload['createdBy']['user']['firstName'] + ' ' + upload['createdBy']['user']['lastName'] + ', ' + upload['createdBy']['lab']['institution']
    for upload in projectFastqUploads:
        userIDs[upload['createdBy']['id']] = upload['createdBy']['user']['firstName'] + ' ' + upload['createdBy']['user']['lastName'] + ', ' + upload['createdBy']['lab']['institution']
    print('Unique Submitter IDs:' + str(sorted(list(userIDs.keys()))))

    # for each submitter
    for userID in sorted(list(userIDs.keys())):
        reportText += newline + 'User ' + str(userID) + ' (' + str(userIDs[userID]) + ')' + newline

        currentUserHMLs =  [hmlUpload for hmlUpload in projectHMLUploads if hmlUpload['createdBy']['id'] == userID]
        reportText += str(len(currentUserHMLs)) + ' HML Files Submitted:' + newline
        for hmlUpload in currentUserHMLs:
            reportText += '\t' + str(hmlUpload['fileName']) + newline

            # Get HML Information, especially Sample IDs.
            xmlFileObject = None
            try:
                hmlFileObject = s3.get_object(Bucket=bucket, Key=hmlUpload['fileName'])
                hmlFileZip.writestr(hmlUpload['fileName'], hmlFileObject["Body"].read())

            except Exception as err:
                reportText += 'Could not fetch upload from S3: ' + str(hmlUpload['fileName'])

            # TODO: Get Sample ID Lists from Each HML Object, write the sample IDs in the report.

        currentUserFASTQs = [fastqUpload for fastqUpload in projectFastqUploads if fastqUpload['createdBy']['id'] == userID]
        reportText += str(len(currentUserFASTQs)) + ' FASTQ Files Submitted:' + newline
        for fastqUpload in currentUserFASTQs:
            reportText += '\t' + str(fastqUpload['fileName']) + newline




    # supportingFileZip.writestr('HelloWorld.txt', 'Hello World!')
    hmlFileZip.writestr('SummaryReport.txt', reportText)

    '''    for supportingFile in list(set(supportingUploadFilenames)):
        print('Adding file ' + str(supportingFile) + ' to ' + str(zipFileName))

        supportingFileObject = s3.get_object(Bucket=bucket, Key=supportingFile)
        # TODO: We're writing a string in the zip file.
        #  I think that's fine for hml & text-like files but this might cause problems with some file types.
        supportingFileZip.writestr(supportingFile, supportingFileObject["Body"].read())'''


    # Store Report S3

    hmlFileZip.close()
    S3_Access.writeFileToS3(newFileName='NGS.RefCellLines.HMLs.zip', bucket=bucket, s3ObjectBytestream=zipFileHmlStream)


    # TODO: Find Project Leader

        # TODO: Change the rest method to create upload, to allow the validation user? Or else I need admin rights...
        # TODO: Create Upload Object for the Leader (if possible?)

    print('Report Text:' + str(reportText))

    '''

    url=IhiwRestAccess.getUrl()
    token=IhiwRestAccess.getToken(url=url)
    immuEpsProjectID = IhiwRestAccess.getProjectID(projectName='immunogenic_epitopes')
    dqEpsProjectID = IhiwRestAccess.getProjectID(projectName='dq_immunogenicity')
    #summaryFileName = 'Project.' + str(immuEpsProjectID) + '.Report.xlsx'
    #zipFileName = 'Project.' + str(immuEpsProjectID) + '.Report.zip'
    summaryFileName = 'ImmunogenicEpitopes.ProjectReport.xlsx'
    zipFileName = 'ImmunogenicEpitopes.ProjectReport.zip'

    dataMatrixUploadList = getDataMatrixUploads(projectIDs=[immuEpsProjectID, dqEpsProjectID], token=token, url=url)

    # Create Spreadsheet, Define Headers?
    outputWorkbook = Workbook()
    summaryWorksheet = outputWorkbook.active
    summaryWorksheet.freeze_panes = 'A2'

    # Write headers on new sheet.
    summaryHeaders = ('donor_glstring', 'recipient_glstring','antibodies_pretx','antibodies_posttx'
        ,'data_matrix_filename','valid','submitting_user','submitting_lab','submission_date', 'transplantation_report')

    dataMatrixHeaders=ImmunogenicEpitopesValidator.getColumnNames(isImmunogenic=True)

    #print('These are the summary headers:' + str(summaryHeaders))
    #print('These are the data matrix headers:' + str(dataMatrixHeaders))

    summaryWorksheet.append(summaryHeaders)
    summaryWorksheet.column_dimensions['A'].width = 40
    summaryWorksheet.column_dimensions['B'].width = 40
    summaryWorksheet.column_dimensions['C'].width = 40
    summaryWorksheet.column_dimensions['D'].width = 40
    summaryWorksheet.column_dimensions['E'].width = 40
    summaryWorksheet.column_dimensions['F'].width = 12
    summaryWorksheet.column_dimensions['G'].width = 25
    summaryWorksheet.column_dimensions['H'].width = 25
    summaryWorksheet.column_dimensions['I'].width = 25
    summaryWorksheet.column_dimensions['J'].width = 40
    summaryWorksheet.column_dimensions['K'].width = 40

    #for headerIndex, header in enumerate(summaryHeaders):
        #columnLetter = get_column_letter(headerIndex+1)
        #cellIndex = columnLetter + '1'
        #summaryWorksheet[cellIndex] = header
    #    summaryWorksheet.column_dimensions[columnLetter].width = 35

    supportingUploadFilenames = []
    supportingSpreadsheets = {}

    reportLineIndex = 0

    # preload an upload list to use repeatedly later
    allUploads = IhiwRestAccess.getUploads(token=token,url=url)

    # Combine data matrices together for summary worksheet..
    for dataMatrixIndex, dataMatrixUpload in enumerate(dataMatrixUploadList):
        #print('Checking Validation of this file:' + dataMatrixUpload['fileName'])
        #print('This is the upload: ' + str(dataMatrixUpload))

        excelFileObject = s3.get_object(Bucket=bucket, Key=dataMatrixUpload['fileName'])
        inputExcelBytes = io.BytesIO(excelFileObject["Body"].read())
        # validateEpitopesDataMatrix returns all the information we need.
        (validationResults, validatedWorkbook) = ImmunogenicEpitopesValidator.validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=True, projectIDs=[immuEpsProjectID, dqEpsProjectID])
        if(validatedWorkbook is not None):
            supportingSpreadsheets[dataMatrixUpload['fileName']]=ParseExcel.createBytestreamExcelOutputFile(workbookObject=validatedWorkbook)
            dataMatrixFileName = dataMatrixUpload['fileName']
            submittingUser = dataMatrixUpload['createdBy']['user']['firstName'] + ' ' + dataMatrixUpload['createdBy']['user']['lastName'] + ':\n' + dataMatrixUpload['createdBy']['user']['email']
            submittingLab = dataMatrixUpload['createdBy']['lab']['department'] + ', ' + dataMatrixUpload['createdBy']['lab']['institution']
            submissionDate = dataMatrixUpload['createdAt']


            # Loop input Workbook data
            #for dataLineIndex, dataLine in enumerate(inputExcelFileData):
            firstSheet = validatedWorkbook[validatedWorkbook.sheetnames[0]]
            for dataLineIndex, dataLine in enumerate(firstSheet.iter_rows(min_row=2)):

                reportLineIndex += 1
                print('Copying this line:' + str(dataLine))
                donorGlString = '?'
                recipientGlString = '?'
                recipHamlPreTxFileName = '?'
                recipHamlPostTxFileName = '?'


                for headerIndex, header in enumerate(dataMatrixHeaders):
                    columnLetter = validatedWorkbook.columnNameLookup[header]
                    print('Checking header ' + str(header) + ' which is at column ' + columnLetter)

                    cellIndex = columnLetter + str(dataLineIndex + 2)
                    cellData = firstSheet[cellIndex].value
                    print('Cell Index: ' + str(cellIndex))
                    print('Data:' + str(cellData))

                    currentGlString = None


                    # Add supporting files.
                    fileResults=[]
                    if(header.endswith('_hla')):
                        fileResults=IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HML'], token=token, url=url, fileName=str(cellData), projectIDs=[immuEpsProjectID, dqEpsProjectID], allUploads=allUploads)

                        if(len(fileResults) == 1):
                            # We found a single file mapped to this HLA result. Get a GlString.
                            currentGlString = ParseXml.getGlStringFromHml(hmlFileName=fileResults[0]['fileName'], s3=s3, bucket=bucket)
                        else:
                            # We didn't find a single file to calculate a glString from. Use the existing data
                            currentGlString = cellData
                        if(currentGlString is None or len(currentGlString) < 1):
                            currentGlString=''

                        # print the glString in the appropriate column
                        if(header=='donor_hla'):
                            donorGlString=currentGlString
                            donorGlStringValidationResults = Validation.validateGlString(glString=donorGlString)
                        elif(header=='recipient_hla'):
                            recipientGlString=currentGlString
                            recipientGlStringValidationResults = Validation.validateGlString(glString=recipientGlString)
                        else:
                            raise Exception ('I cannot understand to do with the data for column ' + str(header) + ':' + str(cellData))

                    elif('_haml_' in (header)):
                        # TODO: Include Antibody_CSV?
                        fileResults=IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HAML'], token=token, url=url, fileName=str(cellData), projectIDs=[immuEpsProjectID, dqEpsProjectID], allUploads=allUploads)
                        #print('I just found these haml results:' + str(fileResults))

                        # TODO: Assuming a single HAML file here. What if !=1 results are found?
                        if(header=='recipient_haml_pre_tx' and len(fileResults)==1):
                            recipHamlPreTxFileName = fileResults[0]['fileName']
                        elif(header=='recipient_haml_post_tx' and len(fileResults)==1):
                            recipHamlPostTxFileName = fileResults[0]['fileName']
                        else:
                            pass

                    else:
                        pass

                    for uploadFile in fileResults:
                        #print('Appending this file to the upload list:' + str(uploadFile))
                        supportingUploadFilenames.append(uploadFile['fileName'])


                transplantationReportFileName = 'AntibodyReport_' + dataMatrixUpload['fileName'] + '_Row' + str(dataLineIndex+2) + '.xlsx'
                transplantationReportText, preTxAntibodies, postTxAntibodies = getTransplantationReportSpreadsheet(donorTyping=donorGlString, recipientTyping=recipientGlString, recipHamlPreTxFilename=recipHamlPreTxFileName, recipHamlPostTxFilename=recipHamlPostTxFileName ,s3=s3, bucket=bucket)
                supportingSpreadsheets[transplantationReportFileName]=transplantationReportText

                if len(validationResults)==0:
                    validationText='Valid'
                else:
                    validationText=str(len(validationResults)) + ' validation issues found'

                preTxAntibodyText=''
                postTxAntibodyText=''
                for specificity in sorted(list(preTxAntibodies.keys())):
                    preTxAntibodyText = preTxAntibodyText + specificity + ' : ' + str(preTxAntibodies[specificity]) + '\n'
                preTxAntibodyText = preTxAntibodyText[:-1]
                for specificity in sorted(list(postTxAntibodies.keys())):
                    postTxAntibodyText = postTxAntibodyText + specificity + ' : ' + str(postTxAntibodies[specificity]) + '\n'
                postTxAntibodyText = postTxAntibodyText[:-1]

                # Make a tuple matching this:     summaryHeaders = ('donor_glstring', 'recipient_glstring','antibodies_pretx','antibodies_posttx'
                #         ,'data_matrix_filename','valid','submitting_user','submitting_lab','submission_date', 'transplantation_report')
                currentTuple=(donorGlString, recipientGlString,preTxAntibodyText,postTxAntibodyText, dataMatrixFileName,validationText,submittingUser,submittingLab,submissionDate, transplantationReportFileName
                         )
                summaryWorksheet.append(currentTuple)
                print('Added Row: ' + str(tuple(summaryWorksheet.rows)[reportLineIndex]))
                summaryWorksheet.row_dimensions[reportLineIndex+1].height=80


        else:
            print('No workbook data was found for data matrix ' + str(dataMatrixUpload['fileName']) )
            print('Upload ID of missing data matrix:' +  str(dataMatrixUpload['id']) )

    # Text wrapping. For every cell.
    for row in summaryWorksheet.iter_rows():
        for cell in row:
            cell.alignment = cell.alignment.copy(wrapText=True)


    createUploadEntriesForReport(summaryFileName=summaryFileName, zipFileName=zipFileName)
    outputWorkbookbyteStream = ParseExcel.createBytestreamExcelOutputFile(workbookObject=outputWorkbook)
    S3_Access.writeFileToS3(newFileName=summaryFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)


    # create zip file
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    #supportingFileZip.writestr('HelloWorld.txt', 'Hello World!')
    supportingFileZip.writestr(summaryFileName, outputWorkbookbyteStream)

    for supportingFile in list(set(supportingUploadFilenames)):
        print('Adding file ' + str(supportingFile) + ' to ' + str(zipFileName))

        supportingFileObject = s3.get_object(Bucket=bucket, Key=supportingFile)
        # TODO: We're writing a string in the zip file.
        #  I think that's fine for hml & text-like files but this might cause problems with some file types.
        supportingFileZip.writestr(supportingFile, supportingFileObject["Body"].read())

    for transplantationReportFileName in supportingSpreadsheets:
        supportingFileZip.writestr(transplantationReportFileName, supportingSpreadsheets[transplantationReportFileName])
    

    supportingFileZip.close()
    S3_Access.writeFileToS3(newFileName=zipFileName, bucket=bucket, s3ObjectBytestream=zipFileStream)

    '''

    #print('Done. Summary is here: ' + str(summaryFileName) + '\nSupporting zip is here: ' + str(zipFileName)  + '\nin bucket: ' + str(bucket))









