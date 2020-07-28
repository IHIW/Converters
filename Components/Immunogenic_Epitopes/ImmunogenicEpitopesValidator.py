from boto3 import client
s3 = client('s3')
from sys import exc_info
import json
import urllib

# For importing common methods, may be in the same directory when deployed as a package
try:
    from IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, createConvertedUploadObject, getProjectID, getUploadIfExists
    from ParseExcel import parseExcelFileWithColumns, createExcelValidationReport
    from Validation import validateUniqueEntryInList, validateBoolean, validateNumber, validateMaleFemale, createFileListFromUploads, validateHlaGenotypeEntry
    from S3_Access import writeFileToS3
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common.IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, createConvertedUploadObject, getProjectID, getUploadIfExists
    from Common.ParseExcel import parseExcelFileWithColumns, createExcelValidationReport
    from Common.Validation import validateUniqueEntryInList, validateBoolean, validateNumber, validateMaleFemale, createFileListFromUploads, validateHlaGenotypeEntry
    from Common.S3_Access import writeFileToS3

def immunogenic_epitope_handler(event, context):
    print('I found the immunogenic epitope validation handler.')
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        content = json.loads(event['Records'][0]['Sns']['Message'])

        bucket = content['Records'][0]['s3']['bucket']['name']
        excelKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        print('Excel Filename:' + excelKey)

        validationResults = None
        # Is this an excel file? It should have the xlsx extension.
        if (str(excelKey).lower().endswith('.xls') or str(excelKey).lower().endswith('.xlsx')):
            print('This is an excel file with the name:' + str(excelKey))

            # Get the upload information.
            url = getUrl()
            token = getToken(url=url)

            # TODO: What if there is no  upload? This will currently probaly just crash. Check if uploadFile is None.
            uploadFile = getUploadIfExists(fileName=excelKey, url=url, token=token)
            print('I found this upload object:' + str(uploadFile))
            projectName = uploadFile['project']['name']
            projectID =  uploadFile['project']['id']
            print('The upload is for this project:' + str(projectName) + ',id=' + str(projectID))
            fileType = uploadFile['type']
            print('this upload is file type:' + str(fileType))

            # Is this a data Matrix?
            if (fileType != 'PROJECT_DATA_MATRIX'):
                print('the file type ' + str(fileType) + ' is not a project data matrix, i will not validate it.')
            else:
                immunogenicEpitopeProjectNumber=getProjectID(projectName='immunogenic_epitopes')
                nonImmunogenicEpitopeProjectNumber=getProjectID(projectName='non_immunogenic_epitopes')

                if (projectID == immunogenicEpitopeProjectNumber):
                    print('This is the Immunogenic Epitopes project!')
                    excelFileObject = s3.get_object(Bucket=bucket, Key=excelKey)
                    inputExcelBytes = excelFileObject["Body"].read()

                    (validationResults, inputExcelFileData, errorResultsPerRow) = validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=True, projectID=projectID)
                    isValid=(validationResults == 'Valid')
                    print('validation results were retrieved, attempting to set status.')
                    print('ValidationResults:(\n' + str(validationResults) + '\n)')
                    setValidationStatus(uploadFileName=excelKey, isValid=isValid,
                        validationFeedback=validationResults, url=url, token=token,
                        validatorType='IMMUNOGENIC_EPITOPES')

                    createValidationReport(isReportValid=isValid, uploadFileName=excelKey,errors=errorResultsPerRow, inputWorkbookData=inputExcelFileData, bucket=bucket, url=url, token=token,validatorType='IMMUNOGENIC_EPITOPES')
                elif (projectID == nonImmunogenicEpitopeProjectNumber):
                    print('This is the Non Immunogenic Epitopes project!')
                    excelFileObject = s3.get_object(Bucket=bucket, Key=excelKey)
                    inputExcelBytes = excelFileObject["Body"].read()
                    (validationResults, inputExcelFileData, errorResultsPerRow) = validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=False, projectID=projectID)
                    isValid=(validationResults == 'Valid')
                    print('validation results were retrieved, attempting to set status.')
                    print('ValidationResults:(\n' + str(validationResults) + '\n)')
                    setValidationStatus(uploadFileName=excelKey, isValid=isValid,
                        validationFeedback=validationResults, url=url, token=token,
                        validatorType='NON_IMMUNOGENIC_EPITOPES')
                    createValidationReport(isReportValid=isValid, uploadFileName=excelKey, errors=errorResultsPerRow, inputWorkbookData=inputExcelFileData, bucket=bucket, url=url, token=token, validatorType='NON_IMMUNOGENIC_EPITOPES')

                else:
                    print('This is not the (Non) Immunogenic Epitopes project! I will not validate it. Double-check the project names')
        else:
            print(excelKey + ' is not an excel file so I will not validate it.')

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def validateEpitopesDataMatrix(excelFile=None, isImmunogenic=None, projectID=None):
    # This method returns a tuple, with (text validation status, inputExcelData, and a list of dictionaries representing row&column-specific error results)
    #print('Validating Epitopes Data Matrix:' + str(excelFile))
    validationErrors=[]
    inputExcelData = None
    if(isImmunogenic == None):
        print('Please pass isImmunogenic=True/False, to specify whether we should validatate Immunogenic or NonImmunogenic epitopes.')
        return('Cannot determine if this is a immunogenic or non immunogenic matrix. Please pass isImmunogenic=True/False', inputExcelData, validationErrors)
    elif(isImmunogenic):
        print('Validating Immunogenic Epitopes.')
        epitopeColumnNames = getColumnNames(isImmunogenic=True)
    else:
        print('Validating Non Immunogenic Epitopes.')
        epitopeColumnNames = getColumnNames(isImmunogenic=False)

    #print('Parsing Excel File with Columns...')
    (inputExcelData, originalColumnHeaders, validationErrors) = parseExcelFileWithColumns(excelFile=excelFile, columnNames=epitopeColumnNames)

    if(type(inputExcelData) is str):
        # If it returned a string then it's an error message. Something is wrong with the data.
        raise Exception ('Invalid Excel Document: ' + str(inputExcelData) + str(inputExcelData) + str(validationErrors))
    elif(type(inputExcelData) is list):
        print('So far so good after parsing excel file, ' + str(len(inputExcelData)) + ' entries found.')
    else:
        return('Something went wrong when parsing Excel data. Investigate why this is not a list:' + str(inputExcelData), inputExcelData, validationErrors)

    # If it's a list then we did a great job. Double check that it has at least one entry.
    if(len(inputExcelData)<1):
        return('No data was found in the input excel file. Did you put any data in there?', inputExcelData, validationErrors)

    url = getUrl()
    token = getToken(url=url)

    if(token==None):
        return('Could not aquire a login token.', inputExcelData, validationErrors)

    try:
        uploadList = getUploads(token=token, url=url)
        hmlUploadList = createFileListFromUploads(uploads=uploadList, projectFilter=projectID, fileTypeFilter='HML')
        hamlUploadList = createFileListFromUploads(uploads=uploadList, projectFilter=projectID, fileTypeFilter='HAML')
    except Exception as e:
        print('Exception when getting list of uploads:\n' + str(e) + '\n' + str(exc_info()))
        return ('Exception when getting list of uploads:\n' + str(e) , inputExcelData, validationErrors)

    # Do more specific validation of the columns. Check that each column is valid.
    # This is project-specific so there are different validations for each column.
    for dataRowIndex, dataRow in enumerate(inputExcelData):
        currentRowValidationResults = validationErrors[dataRowIndex]
        if (isImmunogenic):
            # set default values
            for key in getColumnNames(isImmunogenic=isImmunogenic):
                currentRowValidationResults[key] = (currentRowValidationResults[key] if (key in currentRowValidationResults.keys()) else '')
            # set individual validation things.
            currentRowValidationResults['hla_donor'] += validateHlaGenotypeEntry(query=dataRow['hla_donor'], searchList=hmlUploadList, allowPartialMatch=True, columnName='hla_donor')
            currentRowValidationResults['hla_recipient'] += validateHlaGenotypeEntry(query=dataRow['hla_recipient'], searchList=hmlUploadList, allowPartialMatch=True, columnName='hla_recipient')
            currentRowValidationResults['haml_recipient_pre_tx'] += validateUniqueEntryInList(query=dataRow['haml_recipient_pre_tx'], searchList=hamlUploadList, allowPartialMatch=True, columnName='haml_recipient_pre_tx')
            currentRowValidationResults['haml_recipient_post_tx'] += validateUniqueEntryInList(query=dataRow['haml_recipient_post_tx'], searchList=hamlUploadList, allowPartialMatch=True, columnName='haml_recipient_post_tx')
            currentRowValidationResults['prozone_pre_tx'] += validateBoolean(query=dataRow['prozone_pre_tx'], columnName='prozone_pre_tx')
            currentRowValidationResults['prozone_post_tx'] += validateBoolean(query=dataRow['prozone_post_tx'], columnName='prozone_post_tx')
            currentRowValidationResults['availability_pre_tx'] += validateBoolean(query=dataRow['availability_pre_tx'], columnName='availability_pre_tx')
            currentRowValidationResults['availability_post_tx'] += validateBoolean(query=dataRow['availability_post_tx'], columnName='availability_post_tx')
            currentRowValidationResults['months_post_tx'] += validateNumber(query=dataRow['months_post_tx'], columnName='months_post_tx')
            currentRowValidationResults['gender_recipient'] += validateMaleFemale(query=dataRow['gender_recipient'], columnName='gender_recipient')
            currentRowValidationResults['age_recipient_tx'] += validateNumber(query=dataRow['age_recipient_tx'], columnName='age_recipient_tx')
            currentRowValidationResults['pregnancies_recipient'] += validateBoolean(query=dataRow['pregnancies_recipient'], columnName='pregnancies_recipient')
            currentRowValidationResults['immune_suppr_post_tx'] += validateBoolean(query=dataRow['immune_suppr_post_tx'], columnName='immune_suppr_post_tx')
        else:
            # set default values
            for key in getColumnNames(isImmunogenic=isImmunogenic):
                currentRowValidationResults[key] = (currentRowValidationResults[key] if (key in currentRowValidationResults.keys()) else '')
            currentRowValidationResults['hla_recipient'] += validateHlaGenotypeEntry(query=dataRow['hla_recipient'], searchList=hmlUploadList, allowPartialMatch=True, columnName='hla_recipient', uploadList=uploadList)
            currentRowValidationResults['haml_recipient'] += validateUniqueEntryInList(query=dataRow['haml_recipient'], searchList=hamlUploadList, allowPartialMatch=True, columnName='haml_recipient')
            currentRowValidationResults['prozone'] += validateBoolean(query=dataRow['prozone'], columnName='prozone')
            currentRowValidationResults['availability'] += validateBoolean(query=dataRow['availability'], columnName='availability')
            currentRowValidationResults['gender_recipient'] += validateMaleFemale(query=dataRow['gender_recipient'], columnName='gender_recipient')
            currentRowValidationResults['age_recipient_tx'] += validateNumber(query=dataRow['age_recipient_tx'], columnName='age_recipient_tx')
        validationErrors[dataRowIndex] = currentRowValidationResults
    validationFeedback = ''
    for validationErrorRow in validationErrors:
        for validationColumnName in validationErrorRow.keys():
            currentValidationResult = validationErrorRow[validationColumnName]
            if(currentValidationResult is not None and len(currentValidationResult) > 0):
                validationFeedback = validationFeedback + currentValidationResult + ';\n'

    if len(validationFeedback) < 1:
        return ('Valid', inputExcelData, validationErrors)
    else:
        return (validationFeedback, inputExcelData, validationErrors)

def getColumnNames(isImmunogenic=True):
    if (isImmunogenic):
        return [
            'hla_donor'
            , 'hla_recipient'
            , 'haml_recipient_pre_tx'
            , 'haml_recipient_post_tx'
            , 'prozone_pre_tx'
            , 'prozone_post_tx'
            , 'availability_pre_tx'
            , 'availability_post_tx'
            , 'months_post_tx'
            , 'gender_recipient'
            , 'age_recipient_tx'
            , 'pregnancies_recipient'
            , 'immune_suppr_post_tx'
        ]
    else:
        return ['hla_recipient'
            , 'haml_recipient'
            , 'prozone'
            , 'availability'
            , 'gender_recipient'
            , 'age_recipient_tx'
        ]

def createValidationReport(isReportValid=None, uploadFileName=None,errors=None, inputWorkbookData=None, bucket=None, token=None, url=None, validatorType=None):
    print('Creating a validation Report.')

    reportFileName = uploadFileName + '.Validation_Report.xlsx'
    outputWorkbook, outputWorkbookbyteStream = createExcelValidationReport(errors=errors, inputWorkbookData=inputWorkbookData)

    # if it already exists, we don't need to create the upload object for the report.
    # This throws a HTTP Error 404 if the file doesn't exist
    # I think it's not great to use try/catch for program logic, maybe there's a better solution
    existingUpload = getUploadIfExists(token=token, url=url, fileName=reportFileName)
    if(existingUpload is None):
        print('There is no child upload for the report file ' + str(reportFileName) + ' so I will create one.')
        createConvertedUploadObject(newUploadFileName=reportFileName, newUploadFileType='XLSX', token=token, url=url,previousUploadFileName=uploadFileName)
    else:
        print('There is already a child upload(' + str(existingUpload) + ') for report file ' + str(reportFileName) + ' so I will not create one.')

    setValidationStatus(uploadFileName=reportFileName, isValid=isReportValid, validationFeedback='Download this report for Detailed Validation Results.'
        , validatorType=validatorType+'_REPORT',token=token,url=url)

    writeFileToS3(newFileName=reportFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)