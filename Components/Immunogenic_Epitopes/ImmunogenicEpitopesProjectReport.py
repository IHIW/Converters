from boto3 import client

from Common.ParseExcel import createBytestreamExcelOutputFile, getColumnNumberAsString
from Common.S3_Access import writeFileToS3
from Common.Validation import createFileListFromUploads, validateUniqueEntryInList, validateGlString
from Components.Immunogenic_Epitopes.ImmunogenicEpitopesValidator import validateEpitopesDataMatrix, getColumnNames
from Common.IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, getUploadByFilename, createConvertedUploadObject, getProjectID

s3 = client('s3')
from sys import exc_info
import yaml

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


def fetchGlString(hlaEntry=None, hmlUploadList=None):
    # TODO: Move to a common method, probably Validation.py
    # Fetch a GL String from a spreadsheet entry.
    # Return a tuple, so we can use the glString and the file name:
    # (glString, fileName)

    # This should validate as either a filename or GL String.
    # If it validates as a GL String, use the GL string
    # If it validates as a single file, extract the GL String from the file and add the file to the list
    listValidationResult = validateUniqueEntryInList(query=hlaEntry, searchList=hmlUploadList, allowPartialMatch=True, columnName='HLA')
    glStringValidationResults = validateGlString(glString=hlaEntry)
    if(listValidationResult=='' and len(glStringValidationResults) > 0):
        # TODO: Pull GlStrings from the file.
        glString = 'TODO: get GLString from file ' + str(hlaEntry)
        fileName = hlaEntry
    elif(len(listValidationResult)>0 and glStringValidationResults == ''):
        glString = hlaEntry
        fileName = None
    else:
        # TODO: How to report this to the downloader? We should see if the data is completely invalid.
        #  I suppose the spreadsheet entry will have a red validation error, maybe that's good enough. Double Check.
        print('Validation Error: This does not look like a glString or a single valid HML file:' + str(hlaEntry))
        glString = None
        fileName = None

    return (glString,fileName)


def fetchHamlFilename(hamlEntry=None, hamlUploadList=None):
    # TODO: Move to a common method, probably Validation.py
    uploadMatchList = []
    print('Fetching HAML Filename, hamlEntry:' + str(hamlEntry) + '\nhamlUploadList=' + str(hamlUploadList))

    for hamlUpload in hamlUploadList:
        print('Checking (' + hamlEntry + '),(' + hamlUpload + ')')
        if(hamlEntry in hamlUpload):
            print('Match (' + hamlEntry + '),(' + hamlUpload + ')')
            uploadMatchList.append(hamlUpload)

    if(len(uploadMatchList)==0):
        return None
    elif(len(uploadMatchList)==1):
        # Single file is best!
        return uploadMatchList[0]
    elif(len(uploadMatchList)==2):
        # two files, hopefully one is the haml file. Return that one.
        # TODO: There should be a parent/child relationship. Just return the child. Better than doing this string comparison.
        if (uploadMatchList[0] in uploadMatchList[1]):
            return uploadMatchList[1]
        elif (uploadMatchList[1] in uploadMatchList[0]):
            return uploadMatchList[0]
        else:
            print('Warning: I found two files, but they do not seem to be a converted haml file:' + str(uploadMatchList))
            return None
    else:
        # Multiple matches, we can't attribute this to a single file.
        return None



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
    #sheetHeaders = inputWorkbookData[0].keys()
    sheetHeaders=getColumnNames(isImmunogenic=True)

    extraHeaders=['data_matrix_filename','valid_datarow', 'submitted_timestamp', 'submitting_user', 'submitting_laboratory','hla_glstring_donor','hla_glstring_recipient']

    uploadList = getUploads(token=token, url=url)
    hmlUploadList = createFileListFromUploads(uploads=uploadList, projectFilter=projectID, fileTypeFilter='HML')
    hamlUploadList = createFileListFromUploads(uploads=uploadList, projectFilter=projectID, fileTypeFilter='HAML')

    # Print Headers for Normal data matrix columns
    for headerIndex, header in enumerate(sheetHeaders):
        cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex) + '1'
        outputWorksheet.write(cellIndex, header, headerStyle)

    # Print headers for extra data headers
    for extraHeaderIndex, extraHeader in enumerate(extraHeaders):
        cellIndex = getColumnNumberAsString(base0ColumnNumber=len(sheetHeaders)+extraHeaderIndex) + '1'
        outputWorksheet.write(cellIndex, extraHeader, headerStyle)


    reportLineIndex = 1

    # supportingFiles = []
    # TODO Use real data instead of test data
    supportingFiles = ['1497_1595349611357_HML_good.hml.1.0.1.xml', '1497_1595852685039_HAML_HAMLMatchItImmucor.csv.haml'] # Test data.

    # Combine data matrices together.
    for dataMatrixUpload in dataMatrixUploadList:
        print('Checking Validation of this file:' + dataMatrixUpload['fileName'])

        excelFileObject = s3.get_object(Bucket=bucket, Key=dataMatrixUpload['fileName'])
        inputExcelBytes = excelFileObject["Body"].read()
        # validateEpitopesDataMatrix returns all the information we need.
        (validationResults, inputExcelFileData, errorResultsPerRow) = validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=True, projectID=projectID)
        #print('This file has this validation status:' + validationResults)

        # Get the upload object

        createdByUser = dataMatrixUpload['createdBy']['user']
        submittingUser = str(createdByUser['id']) + ':' + str(createdByUser['firstName']) + ' ' + str(createdByUser['lastName'])
        createdByLab = dataMatrixUpload['createdBy']['lab']
        submittingLaboratory = str(createdByLab['id']) + ':' + str(createdByLab['labCode']) + ':' + str(createdByLab['department']) + ', ' + str(createdByLab['institution'])
        submittedTimestamp = str(dataMatrixUpload['createdAt'])

        # Loop input Workbook data
        for dataLineIndex, dataLine in enumerate(inputExcelFileData):
        # print('Copying this line:' + str(dataLine))
            reportLineIndex += 1

            for headerIndex, header in enumerate(sheetHeaders):
                cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex) + str(reportLineIndex)

                # Was there an error in this cell? Highlight it red and add error message
                if (header in errorResultsPerRow[dataLineIndex].keys() and len(str(errorResultsPerRow[dataLineIndex][header])) > 0):
                    outputWorksheet.write(cellIndex, dataLine[header], errorStyle)
                    outputWorksheet.write_comment(cellIndex, errorResultsPerRow[dataLineIndex][header])
                else:
                    # TODO: What if a dataline is missing a bit of information? Handle if this is missing in the input file.
                    #  I think this may already be fixed, just test with missing data
                    outputWorksheet.write(cellIndex, dataLine[header])

            donorGlString, donorFileName = fetchGlString(hlaEntry=dataLine['hla_donor'], hmlUploadList=hmlUploadList)
            recipientGlString, recipientFileName = fetchGlString(hlaEntry=dataLine['hla_recipient'], hmlUploadList=hmlUploadList)

            recipientHamlPreTx = fetchHamlFilename(hamlEntry=dataLine['haml_recipient_pre_tx'], hamlUploadList = hamlUploadList)
            recipientHamlPostTx = fetchHamlFilename(hamlEntry=dataLine['haml_recipient_post_tx'], hamlUploadList = hamlUploadList)

            # Store these supporting files.
            for supportingFileName in [donorFileName,recipientFileName,recipientHamlPreTx,recipientHamlPostTx]:
                if(supportingFileName is not None):
                    supportingFiles.append(supportingFileName)

            for extraHeaderIndex, extraHeader in enumerate(extraHeaders):
                cellIndex = getColumnNumberAsString(base0ColumnNumber=len(sheetHeaders) + extraHeaderIndex) + str(reportLineIndex)
                if( extraHeader=='data_matrix_filename'):
                    extraHeaderData = str(dataMatrixUpload['fileName'])
                elif extraHeader=='valid_datarow':
                    extraHeaderData = 'False'
                elif extraHeader == 'submitted_timestamp':
                    extraHeaderData = submittedTimestamp
                elif extraHeader == 'submitting_user':
                    extraHeaderData = submittingUser
                elif extraHeader == 'submitting_laboratory':
                    extraHeaderData = submittingLaboratory
                elif extraHeader == 'hla_glstring_donor':
                    extraHeaderData = str(donorGlString)
                elif extraHeader == 'hla_glstring_recipient':
                    extraHeaderData = str(recipientGlString)
                else:
                    raise Exception('I do not know what to do with this extra header. Handle this data:' + str(extraHeader))

                outputWorksheet.write(cellIndex, extraHeaderData)

    # Widen the columns a bit so we can read them.
    outputWorksheet.set_column('A:' + getColumnNumberAsString(len(sheetHeaders) +len(extraHeaders) - 1), 30)
    # Freeze the header row.
    outputWorksheet.freeze_panes(1, 0)
    outputWorkbook.close()
    writeFileToS3(newFileName=summaryFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)

    # create zip file
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    #supportingFileZip.writestr('HelloWorld.txt', 'Hello World!')
    supportingFileZip.writestr(summaryFileName, outputWorkbookbyteStream.getvalue())

    supportingFiles = list(set(supportingFiles))
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
    print('This is my upload list:' + str(uploadList))
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







