from boto3 import client
#import json
#import urllib
from Common.ParseExcel import createExcelTransplantationReport
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

try:
    import IhiwRestAccess
    import ParseExcel
    import ParseXml
    import Validation
    import S3_Access
    import ImmunogenicEpitopesValidator
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common import IhiwRestAccess
    from Common import ParseExcel
    from Common import ParseXml
    from Common import Validation
    from Common import S3_Access
    import ImmunogenicEpitopesValidator

s3 = client('s3')
from sys import exc_info

import zipfile
import io
from time import sleep

# TODO: In general I re-worked the epitopes validator, and i need the project report to match it.
#  I don't have per-row validation feedback to generate on the fly.
#  Perhaps it's better to collect the data matrixes in individual tabs
#  Validate them individually and collect the validation issues on the single tab. That would have the submitter data.
#  Then make a first tab as a summary of all the submitted data matrices.


def immunogenic_epitope_project_report_handler(event, context):
    print('Lambda handler: Creating a project report for immunogenic epitopes.')
    # This is the AWS Lambda handler function.
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        sleep(1)
        # TODO: get the bucket from the sns message ( there is no sns message, trigger one?)
        #bucket = content['Records'][0]['s3']['bucket']['name']
        bucket = 'ihiw-management-upload-prod'
        #bucket = 'ihiw-management-upload-staging'

        #adminUserID=

        createImmunogenicEpitopesReport(bucket=bucket)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


def createUploadEntriesForReport(summaryFileName=None, zipFileName=None):
    # TODO: This should be a standalone upload, not a child upload. Need some work on this part.

    # TODO: This will also make multiple copies. I should check if the report file already exists and/or (probably) overwrite it
    parentUploadName = '1497_1615205312528_PROJECT_DATA_MATRIX_ProjectReport'
    url = IhiwRestAccess.getUrl()
    token = IhiwRestAccess.getToken(url=url)

    if(url is not None and token is not None and len(url)>0 and len(token)>0):

        IhiwRestAccess.createConvertedUploadObject(newUploadFileName=summaryFileName
                                                   , newUploadFileType='OTHER'
                                                   , previousUploadFileName=parentUploadName
                                                   , url=url, token=token)
        IhiwRestAccess.createConvertedUploadObject(newUploadFileName=zipFileName
                                                   , newUploadFileType='OTHER'
                                                   , previousUploadFileName=parentUploadName
                                                   , url=url, token=token)

        IhiwRestAccess.setValidationStatus(uploadFileName=parentUploadName, isValid=True,
                                           validationFeedback='Valid Report.', validatorType='PROJECT_REPORT', url=url,
                                           token=token)
        IhiwRestAccess.setValidationStatus(uploadFileName=summaryFileName, isValid=True,
                                           validationFeedback='Valid Report.', validatorType='PROJECT_REPORT', url=url,
                                           token=token)
        IhiwRestAccess.setValidationStatus(uploadFileName=zipFileName, isValid=True,
                                           validationFeedback='Valid Report.', validatorType='PROJECT_REPORT', url=url,
                                           token=token)
    else:
        raise Exception('Could not create login token when creating upload entries for report files.')

def getTransplantationReportSpreadsheet(donorTyping=None, recipientTyping=None, recipHamlPreTxFilename=None, recipHamlPostTxFilename=None, s3=None, bucket=None):
    recipPreTxAntibodyData = ParseXml.parseHamlFileForBeadData(hamlFileName=recipHamlPreTxFilename, s3=s3, bucket=bucket)
    recipPostTxAntibodyData = ParseXml.parseHamlFileForBeadData(hamlFileName=recipHamlPostTxFilename, s3=s3, bucket=bucket)
    transplantationReportSpreadsheet, preTxAntibodies, postTxAntibodies = ParseExcel.createExcelTransplantationReport(donorTyping=donorTyping, recipientTyping=recipientTyping, recipPreTxAntibodyData=recipPreTxAntibodyData, recipPostTxAntibodyData=recipPostTxAntibodyData, preTxFileName=recipHamlPreTxFilename, postTxFileName=recipHamlPostTxFilename)
    return transplantationReportSpreadsheet, preTxAntibodies, postTxAntibodies

def createImmunogenicEpitopesReport(bucket=None):
    print('Creating an Immunogenic Epitopes Submission Report.')

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



    print('Done. Summary is here: ' + str(summaryFileName) + '\nSupporting zip is here: ' + str(zipFileName)
          + '\nin bucket: ' + str(bucket))

def getDataMatrixUploads(projectIDs=None, token=None, url=None):
    # collect all data matrix files.
    uploadList = IhiwRestAccess.getUploads(token=token, url=url)
    #print('I found these uploads:' + str(uploadList))
    #print('This is my upload list:' + str(uploadList))
    print('Parsing ' + str(len(uploadList)) + ' uploads to find data matrices for project(s) ' + str(projectIDs) + '..')
    if(not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]
    dataMatrixUploadList = []
    for upload in uploadList:
        if (upload['project']['id'] in projectIDs):
            if (upload['type'] == 'PROJECT_DATA_MATRIX'):
                dataMatrixUploadList.append(upload)
            else:
                # print('Disregarding this upload because it is not a data matrix.')
                pass
        else:
            # print('Disregarding this upload because it is not in our project.')
            pass
    print(
        'I found a total of ' + str(len(dataMatrixUploadList)) + ' data matrices for project' + str(projectIDs) + '.\n')
    return dataMatrixUploadList







