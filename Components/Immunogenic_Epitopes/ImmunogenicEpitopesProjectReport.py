from boto3 import client

from Common.ParseExcel import createBytestreamExcelOutputFile, getColumnNumberAsString
from Common.S3_Access import writeFileToS3
from Components.Immunogenic_Epitopes.ImmunogenicEpitopesValidator import validateEpitopesDataMatrix, getColumnNames

s3 = client('s3')
from sys import exc_info
import yaml

from Common.IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, getUploadByFilename, createConvertedUploadObject



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

    # Get the project ID from the config
    try:
        configStream = open('validation_config.yml', 'r')
        configDict = yaml.load(configStream, Loader=yaml.FullLoader)
        projectID = configDict['project_id']['immunogenic_epitopes']
    except Exception as e:
        print('Exception when loading project ID from config, does the config contain an entry for this?:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

    # collect all data matrix files.
    uploadList = getUploads(token=token, url=url)
    print('This is my upload list:' + str(uploadList))
    print('Parsing ' + str(len(uploadList)) + ' uploads to find data matrices for project ' + str(projectID) + '..')
    dataMatrixUploadList = []
    for upload in uploadList:
        if(projectID == upload['project']['id']):
            if(upload['type'] == 'PROJECT_DATA_MATRIX'):
                dataMatrixUploadList.append(upload)
            else:
                #print('Disregarding this upload because it is not a data matrix.')
                pass
        else:
            #print('Disregarding this upload because it is not in our project.')
            pass
    print('I found a total of ' + str(len(dataMatrixUploadList)) + ' data matrices for project' + str(projectID) + '.\n')

    # Create Spreadsheet, Define Headers?
    outputWorkbook, outputWorkbookbyteStream = createBytestreamExcelOutputFile()
    # TODO: Support multiple sheets. This is just a single sheet.
    outputWorksheet = outputWorkbook.add_worksheet()
    # Define Styles
    headerStyle = outputWorkbook.add_format({'bold': True})
    errorStyle = outputWorkbook.add_format({'bg_color': 'red'})
    # Write headers on new sheet.
    #sheetHeaders = inputWorkbookData[0].keys()
    sheetHeaders=getColumnNames(isImmunogenic=True)
    print('These are the headers:' + str(sheetHeaders))
    for headerIndex, header in enumerate(sheetHeaders):
        cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex) + '1'
        outputWorksheet.write(cellIndex, header, headerStyle)







    # Combine them together.
    for dataMatrixUpload in dataMatrixUploadList:
        print('Checking Validation of this file:' + dataMatrixUpload['fileName'])



        excelFileObject = s3.get_object(Bucket=bucket, Key=dataMatrixUpload['fileName'])
        inputExcelBytes = excelFileObject["Body"].read()
        # validateEpitopesDataMatrix returns all the information we need.
        (validationResults, inputExcelFileData, errorResultsPerRow) = validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=True)
        #print('This file has this validation status:' + validationResults)

        reportLineIndex=1
        # Loop input Workbook data
        for dataLineIndex, dataLine in enumerate(inputExcelFileData):
        # print('Copying this line:' + str(dataLine))
            reportLineIndex += 1


            for headerIndex, header in enumerate(sheetHeaders):
                cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex) + str(reportLineIndex)

                # Was there an error in this cell? Highlight it red and add error message
                if (header in errorResultsPerRow[dataLineIndex].keys() and len(str(errorResultsPerRow[dataLineIndex][header])) > 0):
                    # TODO: Make the error styles optional.
                    outputWorksheet.write(cellIndex, dataLine[header], errorStyle)
                    outputWorksheet.write_comment(cellIndex, errorResultsPerRow[dataLineIndex][header])
                else:
                    outputWorksheet.write(cellIndex, dataLine[header])






        # Print the validation status on the entered spreadsheet information.
        # First step, just put the validation comments as a first comment in th

    # Keep a list of HML files to zip.

    # write excel summary.

    # Widen the columns a bit so we can read them.
    outputWorksheet.set_column('A:' + getColumnNumberAsString(len(sheetHeaders) - 1), 30)
    # Freeze the header row.
    outputWorksheet.freeze_panes(1, 0)
    outputWorkbook.close()

    writeFileToS3(newFileName='ImmunogenicEpitopesReport.xlsx', bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)

    # create zip file
    # add excel summary

    # for hml and haml files
        # add to zip



