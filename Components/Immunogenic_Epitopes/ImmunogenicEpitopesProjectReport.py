from boto3 import client

from Common.ParseExcel import createBytestreamExcelOutputFile, getColumnNumberAsString
from Common.ParseXml import getGlStringFromHml
from Common.S3_Access import writeFileToS3
from Common.Validation import validateGlString
from Components.Immunogenic_Epitopes.ImmunogenicEpitopesValidator import validateEpitopesDataMatrix, getColumnNames
from Common.IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, getUploadByFilename, \
    createConvertedUploadObject, getProjectID, getUploadFileNamesByPartialKeyword

s3 = client('s3')
from sys import exc_info
#import yaml

import zipfile
import io
#from StringIO import StringIO




def immunogenic_epitope_project_report_handler(event, context):
    print('Lambda handler: Creating a project report for immunogenic epitopes.')
    # This is the AWS Lambda handler function.
    try:
        # bucket = content['Records'][0]['s3']['bucket']['name']

        createImmunogenicEpitopesReport()


    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)



def createImmunogenicEpitopesReport(bucket=None):
    print('Creating an Immunogenic Epitopes Submission Report.')

    url=getUrl()
    token=getToken(url=url)
    projectID = getProjectID(projectName='immunogenic_epitopes')
    summaryFileName = 'Project.' + str(projectID) + '.Report.xlsx'
    zipFileName = 'Project.' + str(projectID) + '.Report.zip'

    dataMatrixUploadList = getDataMatrixUploads(projectID=projectID, token=token, url=url)

    # Create Spreadsheet, Define Headers?
    outputWorkbook, outputWorkbookbyteStream = createBytestreamExcelOutputFile()
    outputWorksheet = outputWorkbook.add_worksheet()
    # Define Styles
    headerStyle = outputWorkbook.add_format({'bold': True})
    errorStyle = outputWorkbook.add_format({'bg_color': 'red'})
    # Write headers on new sheet.
    summaryHeaders = ['data_matrix_filename','submitting_user','submitting_lab','submission_date']
    dataMatrixHeaders=getColumnNames(isImmunogenic=True)


    print('These are the summary headers:' + str(summaryHeaders))
    print('These are the data matrix headers:' + str(dataMatrixHeaders))

    for headerIndex, header in enumerate(summaryHeaders):
        cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex) + '1'
        outputWorksheet.write(cellIndex, header, headerStyle)

    for headerIndex, header in enumerate(dataMatrixHeaders):
        cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex+len(summaryHeaders)) + '1'
        outputWorksheet.write(cellIndex, header, headerStyle)

    reportLineIndex = 1

    supportingFiles = []
    #supportingFiles = ['1497_1593502560693_HML_HmlRecipient.xml'] # Test data.

    # Combine data matrices together.
    for dataMatrixUpload in dataMatrixUploadList:
        print('Checking Validation of this file:' + dataMatrixUpload['fileName'])
        print('This is the upload: ' + str(dataMatrixUpload))

        excelFileObject = s3.get_object(Bucket=bucket, Key=dataMatrixUpload['fileName'])
        inputExcelBytes = excelFileObject["Body"].read()
        # validateEpitopesDataMatrix returns all the information we need.
        (validationResults, inputExcelFileData, errorResultsPerRow) = validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=True)
        #print('This file has this validation status:' + validationResults)

        dataMatrixFileName = dataMatrixUpload['fileName']
        # TODO: Add submitting user email address to this field.
        submittingUser = dataMatrixUpload['createdBy']['user']['firstName'] + ' ' + dataMatrixUpload['createdBy']['user']['lastName'] + ':\n' + dataMatrixUpload['createdBy']['user']['email']
        submittingLab = dataMatrixUpload['createdBy']['lab']['department'] + ', ' + dataMatrixUpload['createdBy']['lab']['institution']
        submissionDate = dataMatrixUpload['createdAt']

        # Loop input Workbook data
        for dataLineIndex, dataLine in enumerate(inputExcelFileData):
        # print('Copying this line:' + str(dataLine))
            reportLineIndex += 1

            outputWorksheet.write(getColumnNumberAsString(base0ColumnNumber=0) + str(reportLineIndex), dataMatrixFileName)
            outputWorksheet.write(getColumnNumberAsString(base0ColumnNumber=1) + str(reportLineIndex), submittingUser)
            outputWorksheet.write(getColumnNumberAsString(base0ColumnNumber=2) + str(reportLineIndex), submittingLab)
            outputWorksheet.write(getColumnNumberAsString(base0ColumnNumber=3) + str(reportLineIndex), submissionDate)

            for headerIndex, header in enumerate(dataMatrixHeaders):
                cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex+len(summaryHeaders)) + str(reportLineIndex)

                currentGlString = None
                # Add supporting files.
                fileResults=[]
                if(header.endswith('_hla')):
                    fileResults=getUploadFileNamesByPartialKeyword(fileName=str(dataLine[header]), projectID=projectID)

                    if(len(fileResults) == 1):
                        # We found a single file mapped to this HLA result. Get a GlString.
                        currentGlString = getGlStringFromHml(hmlFileName=fileResults[0]['fileName'], s3=s3, bucket=bucket)
                elif('_haml_' in (header)):
                    fileResults=getUploadFileNamesByPartialKeyword(fileName=str(dataLine[header]), projectID=projectID)
                else:
                    pass

                for uploadFile in fileResults:
                    supportingFiles.append(uploadFile['fileName'])

                if(currentGlString is None):
                    currentCellValue = dataLine[header]
                else:
                    currentCellValue = currentGlString

                    # Get some validation results on the GL String
                    glStringValidationResults = validateGlString(glString=currentGlString)
                    #print('****** I found these glString validationRestults:' + str(glStringValidationResults))
                    if(glStringValidationResults != ''):
                        errorResultsPerRow[dataLineIndex][header] = glStringValidationResults


                # Was there an error in this cell? Highlight it red and add error message
                if (header in errorResultsPerRow[dataLineIndex].keys() and len(str(errorResultsPerRow[dataLineIndex][header])) > 0):
                    # TODO: Make the error styles optional.
                    outputWorksheet.write(cellIndex, currentCellValue, errorStyle)
                    outputWorksheet.write_comment(cellIndex, errorResultsPerRow[dataLineIndex][header])
                else:
                    # TODO: What if a dataline is missing a bit of information? Handle if this is missing in the input file.
                    outputWorksheet.write(cellIndex, currentCellValue)

    # Widen the columns a bit so we can read them.
    outputWorksheet.set_column('A:' + getColumnNumberAsString(len(dataMatrixHeaders) - 1), 30)
    # Freeze the header row.
    outputWorksheet.freeze_panes(1, 0)
    outputWorkbook.close()
    writeFileToS3(newFileName=summaryFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)

    # create zip file
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    #supportingFileZip.writestr('HelloWorld.txt', 'Hello World!')
    supportingFileZip.writestr(summaryFileName, outputWorkbookbyteStream.getvalue())

    for supportingFile in supportingFiles:
        print('Adding file ' + str(supportingFile) + ' to ' + str(zipFileName))

        supportingFileObject = s3.get_object(Bucket=bucket, Key=supportingFile)
        # TODO: We're writing a string in the zip file.
        #  I think that's fine for hml & text-like files but this might cause problems with some file types.
        supportingFileZip.writestr(supportingFile, supportingFileObject["Body"].read())

    supportingFileZip.close()
    writeFileToS3(newFileName=zipFileName, bucket=bucket, s3ObjectBytestream=zipFileStream)

    print('Done. Summary is here: ' + str(summaryFileName) + '\nSupporting zip is here: ' + str(zipFileName)
          + '\nin bucket: ' + str(bucket))

def getDataMatrixUploads(projectID=None, token=None, url=None):
    # collect all data matrix files.
    uploadList = getUploads(token=token, url=url)
    #print('This is my upload list:' + str(uploadList))
    #print('Parsing ' + str(len(uploadList)) + ' uploads to find data matrices for project ' + str(projectID) + '..')
    dataMatrixUploadList = []
    for upload in uploadList:
        if (projectID == upload['project']['id']):
            if (upload['type'] == 'PROJECT_DATA_MATRIX'):
                dataMatrixUploadList.append(upload)
            else:
                # print('Disregarding this upload because it is not a data matrix.')
                pass
        else:
            # print('Disregarding this upload because it is not in our project.')
            pass
    print(
        'I found a total of ' + str(len(dataMatrixUploadList)) + ' data matrices for project' + str(projectID) + '.\n')
    return dataMatrixUploadList







