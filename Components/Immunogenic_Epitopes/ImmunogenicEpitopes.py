from boto3 import client
s3 = client('s3')
from sys import exc_info
import json
import urllib

# For importing common methods, may be in the same directory when deployed as a package
try:
    from IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, getUploadByFilename, createConvertedUploadObject
    from ParseExcel import parseExcelFileWithColumns, createExcelValidationReport
    from Validation import validateUniqueEntryInList, validateBoolean, validateNumber, validateMaleFemale, createFileListFromUploads, validateHlaGenotypeEntry
    from S3_Access import writeFileToS3
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common.IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, getUploadByFilename, createConvertedUploadObject
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
        if(str(excelKey).lower().endswith('.xlsx.xlsx')):
            # TODO: I think this is actually pretty dangerous.
            #  I might be creating an infinite loop if i am not careful. I dont want to re-validate the report file.
            #  Good solutions: check if there is a parent upload, and skip the validation
            #  Or Skip validation if there is already a valdiation status.
            #  The current file type is XLSX for this upload.
            print('This is a report file! Not validating it.')

        elif (str(excelKey).lower().endswith('.xls') or str(excelKey).lower().endswith('.xlsx')):
            print('This is an excel file with the name:' + str(excelKey))

            # Get the upload information.
            url = getUrl()
            token = getToken(url=url)

            uploadFile = getUploadByFilename(fileName=excelKey, url=url, token=token)
            print('I found this upload object:' + str(uploadFile))
            projectName = uploadFile['project']['name']
            print('The upload is for this project:' + str(projectName))
            fileType = uploadFile['type']
            print('this upload is file type:' + str(fileType))

            # Is this a data Matrix?
            if (fileType != 'PROJECT_DATA_MATRIX'):
                print('the file type ' + str(fileType) + ' is not a project data matrix, i will not validate it.')
            else:
                # TODO: Checking by the name of the project is probably not the best. It changes between Staging and Production. It changes if the project is edited.
                # TODO: Add the project IDs as configuration values in validation_config.yml
                immunogenicEpitopeProjectName='Definition of immunogenic epitopes'
                nonImmunogenicEpitopeProjectName='Project name: Definition of non-immunogenic epitopes edit'

                if (projectName == immunogenicEpitopeProjectName):
                    print('This is the Immunogenic Epitopes project!')
                    excelFileObject = s3.get_object(Bucket=bucket, Key=excelKey)
                    inputExcelBytes = excelFileObject["Body"].read()

                    (validationResults, inputExcelFileData, errorResultsPerRow) = validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=True)
                    isValid=(validationResults == 'Valid')
                    print('validation results were retrieved, attempting to set status.')
                    print('ValidationResults:(\n' + str(validationResults) + '\n)')
                    setValidationStatus(uploadFileName=excelKey, isValid=isValid,
                        validationFeedback=validationResults, url=url, token=token,
                        validatorType='IMMUNOGENIC_EPITOPES')
                    if(not isValid):
                        createValidationReport(uploadFileName=excelKey,errors=errorResultsPerRow, inputWorkbookData=inputExcelFileData, bucket=bucket, url=url, token=token,validatorType='IMMUNOGENIC_EPITOPES')
                elif (projectName == nonImmunogenicEpitopeProjectName):
                    print('This is the Non Immunogenic Epitopes project!')
                    excelFileObject = s3.get_object(Bucket=bucket, Key=excelKey)
                    inputExcelBytes = excelFileObject["Body"].read()
                    (validationResults, inputExcelFileData, errorResultsPerRow) = validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=False)
                    isValid=(validationResults == 'Valid')
                    print('validation results were retrieved, attempting to set status.')
                    print('ValidationResults:(\n' + str(validationResults) + '\n)')
                    setValidationStatus(uploadFileName=excelKey, isValid=isValid,
                        validationFeedback=validationResults, url=url, token=token,
                        validatorType='NON_IMMUNOGENIC_EPITOPES')
                    if(not isValid):
                        createValidationReport(uploadFileName=excelKey,errors=errorResultsPerRow, inputWorkbookData=inputExcelFileData, bucket=bucket, url=url, token=token, validatorType='NON_IMMUNOGENIC_EPITOPES')
                else:
                    print('This is not the (Non) Immunogenic Epitopes project! I will not validate it. Double-check the project names')
        else:
            print(excelKey + ' is not an excel file so I will not validate it.')

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)

def validateEpitopesDataMatrix(excelFile=None, isImmunogenic=None):
    # This method returns a tuple, with (text validation status, inputExcelData, and a list of dictionaries representing row&column-specific error results)
    print('Validating Epitopes Data Matrix:' + str(excelFile))
    validationErrors=[]
    inputExcelData = None
    if(isImmunogenic == None):
        print('Please pass isImmunogenic=True/False, to specify whether we should validatate Immunogenic or NonImmunogenic epitopes.')
        return('Cannot determine if this is a immunogenic or non immunogenic matrix. Please pass isImmunogenic=True/False', inputExcelData, validationErrors)
    elif(isImmunogenic):
        print('Validating Immunogenic Epitopes.')
        epitopeColumnNames = [
            'hml_id_donor'
            , 'hml_id_recipient'
            , 'haml_id_recipient_pre_tx'
            , 'haml_id_recipient_post_tx'
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
        print('Validating Non Immunogenic Epitopes.')
        epitopeColumnNames= ['hml_id_recipient'
            ,'haml_id_recipient'
            ,'prozone'
            ,'availability'
            ,'gender_recipient'
            ,'age_recipient_tx'
        ]

    inputExcelData, originalColumnHeaders = parseExcelFileWithColumns(excelFile=excelFile, columnNames=epitopeColumnNames)

    if(type(inputExcelData) is str):
        # If it returned a string then it's an error message. Something is wrong with the data.
        return('Invalid Excel Document: ' + str(inputExcelData), inputExcelData, validationErrors)
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

    uploadList = None
    hmlList = None

    try:
        uploadList = getUploads(token=token, url=url)
        uploadFileList = createFileListFromUploads(uploads=uploadList)
    except Exception as e:
        print('Exception when getting list of uploads:\n' + str(e) + '\n' + str(exc_info()))
        return ('Exception when getting list of uploads:\n' + str(e) , inputExcelData, validationErrors)

    # Get list of upload HML IDs.
    # TODO: Check based on HML IDs as well. For now, just use filenames.
    #existingHMLIDs = getHMLIDs()


    # Do more specific validation of the columns. Check that each column is valid.

    if(isImmunogenic):
        for dataRow in inputExcelData:
            currentRowValidationResults={}
            # findUniqueFile returns an empty string if a single file was found.
            currentRowValidationResults['hml_id_donor'] = validateHlaGenotypeEntry(query=dataRow['hml_id_donor'], searchList=uploadFileList, allowPartialMatch=True, columnName='hml_id_donor', uploadList=uploadList)
            currentRowValidationResults['hml_id_recipient'] = validateHlaGenotypeEntry(query=dataRow['hml_id_recipient'], searchList=uploadFileList, allowPartialMatch=True, columnName='hml_id_recipient', uploadList=uploadList)
            currentRowValidationResults['haml_id_recipient_pre_tx'] = validateUniqueEntryInList(query=dataRow['haml_id_recipient_pre_tx'], searchList=uploadFileList, allowPartialMatch=True, columnName='haml_id_recipient_pre_tx')
            currentRowValidationResults['haml_id_recipient_post_tx'] = validateUniqueEntryInList(query=dataRow['haml_id_recipient_post_tx'], searchList=uploadFileList, allowPartialMatch=True, columnName='haml_id_recipient_post_tx')
            currentRowValidationResults['prozone_pre_tx'] = validateBoolean(query=dataRow['prozone_pre_tx'], columnName='prozone_pre_tx')
            currentRowValidationResults['prozone_post_tx'] = validateBoolean(query=dataRow['prozone_post_tx'], columnName='prozone_post_tx')
            currentRowValidationResults['availability_pre_tx'] = validateBoolean(query=dataRow['availability_pre_tx'], columnName='availability_pre_tx')
            currentRowValidationResults['availability_post_tx'] = validateBoolean(query=dataRow['availability_post_tx'], columnName='availability_post_tx')
            currentRowValidationResults['months_post_tx'] = validateNumber(query=dataRow['months_post_tx'], columnName='months_post_tx')
            currentRowValidationResults['gender_recipient'] = validateMaleFemale(query=dataRow['gender_recipient'], columnName='gender_recipient')
            currentRowValidationResults['age_recipient_tx'] = validateNumber(query=dataRow['age_recipient_tx'], columnName='age_recipient_tx')
            currentRowValidationResults['pregnancies_recipient'] = validateBoolean(query=dataRow['pregnancies_recipient'], columnName='pregnancies_recipient')
            currentRowValidationResults['immune_suppr_post_tx'] = validateBoolean(query=dataRow['immune_suppr_post_tx'], columnName='immune_suppr_post_tx')

            validationErrors.append(currentRowValidationResults)
    else:
        for dataRow in inputExcelData:
            currentRowValidationResults = {}
            # findUniqueFile returns an empty string if a single file was found.
            currentRowValidationResults['hml_id_recipient'] = validateHlaGenotypeEntry(query=dataRow['hml_id_recipient'], searchList=uploadFileList, allowPartialMatch=True, columnName='hml_id_recipient', uploadList=uploadList)
            currentRowValidationResults['haml_id_recipient'] = validateUniqueEntryInList(query=dataRow['haml_id_recipient'], searchList=uploadFileList, allowPartialMatch=True, columnName='haml_id_recipient')
            currentRowValidationResults['prozone'] = validateBoolean(query=dataRow['prozone'], columnName='prozone')
            currentRowValidationResults['availability'] = validateBoolean(query=dataRow['availability'], columnName='availability')
            currentRowValidationResults['gender_recipient'] = validateMaleFemale(query=dataRow['gender_recipient'], columnName='gender_recipient')
            currentRowValidationResults['age_recipient_tx'] = validateNumber(query=dataRow['age_recipient_tx'], columnName='age_recipient_tx')

            validationErrors.append(currentRowValidationResults)

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

def createValidationReport(uploadFileName=None,errors=None, inputWorkbookData=None, bucket=None, token=None, url=None, validatorType=None):
    print('Creating a validation Report.')

    # TODO: Assign a new filename to show this is a validation report.
    reportFileName = uploadFileName + '.xlsx'

    outputWorkbook, outputWorkbookbyteStream = createExcelValidationReport(errors=errors, inputWorkbookData=inputWorkbookData)

    createConvertedUploadObject(newUploadFileType='XLSX', token=token, url=url, previousUploadFileName=uploadFileName)
    setValidationStatus(uploadFileName=reportFileName, isValid=True, validationFeedback='Download this report for Detailed Validation Results.'
        , validatorType=validatorType,token=token,url=url)

    writeFileToS3(newFileName=reportFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)