from boto3 import client
s3 = client('s3')
#from lxml import etree
from sys import exc_info
import json
import urllib

# For importing common methods, may be in the same directory when deployed as a package
try:
    from IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, getUploadByFilename
    from ParseExcel import parseExcelFile
    from Validation import validateUniqueEntryInList, validateBoolean, validateNumber, validateMaleFemale
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common.IhiwRestAccess import getUrl, getToken, getUploads, setValidationStatus, getUploadByFilename
    from Common.ParseExcel import parseExcelFile
    from Common.Validation import validateUniqueEntryInList, validateBoolean, validateNumber, validateMaleFemale

def immunogenic_epitope_handler(event, context):
    print('I found the immunogenic epitope validation handler.')
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        content = json.loads(event['Records'][0]['Sns']['Message'])

        bucket = content['Records'][0]['s3']['bucket']['name']
        excelKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        print('Excel Filename:' + excelKey)

        # Determine file type
        if (str(excelKey).lower().endswith('.xls') or str(excelKey).lower().endswith('.xlsx')):
            fileType = 'EXCEL'
        else:
            fileType = 'UNKNOWN'

        validationResults = None
        # Get the Schema file
        if (fileType == 'EXCEL'):
            print('This is an excel file with the name:' + str(excelKey))

            url = getUrl()
            token = getToken(url=url)

            # Is it for our project?
            uploadFile = getUploadByFilename(fileName=excelKey,url=url, token=token)
            print('I found this upload object:' + str(uploadFile))
            projectName=uploadFile['project']['name']
            print('The upload is for this project:' + str(projectName))
            # TODO: Checking by the name of the project is probably not the best. It changes between Staging and Production.
            if(projectName == 'Definition of immunogenic epitopes'):
                print('This is the Immunogenic Epitopes project!')

                fileType = uploadFile['type']
                if(fileType != 'PROJECT_DATA_MATRIX'):
                    print('the file type ' + str(fileType) + ' is not a project data matrix, i will not validate it.')
                else:
                    excelFileObject = s3.get_object(Bucket=bucket, Key=excelKey)
                    print('Just got the excel file:' + str(excelFileObject))
                    # read() provides a stream of bytes. The excel reader can accept this automatically, we pass that instead of filename.
                    excelData = excelFileObject["Body"].read()
                    # print('Data:' + str(excelData))

                    # Perform the validation.
                    validationResults = validateEpitopesDataMatrix(excelFile=excelData)
                    print('validation results were retrieved, attempting to set status.')
                    print('ValidationResults:(\n' + str(validationResults) + '\n)')

                    # Request the management app to update the validation status for this file.

                    setValidationStatus(uploadFileName=excelKey, isValid=(validationResults == 'Valid'),
                                        validationFeedback=validationResults, url=url, token=token,
                                        validatorType='IMMUNOGENIC_EPITOPES')

            else:
                print('This is Not the Immunogenic Epitopes project! I will not validate it.')




        else:
            print(excelKey + ' is not an excel file so I will not validate it.')

        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)



def validateEpitopesDataMatrix(excelFile=None):
    print('Validating Epitopes Data Matrix:' + str(excelFile))

    immunogenicEpitopeColumnNames = [
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

    excelData = parseExcelFile(excelFile=excelFile, columnNames=immunogenicEpitopeColumnNames)

    if(type(excelData) is str):
        # If it returned a string then it's an error message. Something is wrong with the data.
        return('Invalid Excel Document: ' + str(excelData))
    elif(type(excelData) is list):
        print('So far so good after parsing excel file, ' + str(len(excelData)) + ' entries found.')
    else:
        return('Something went wrong when parsing Excel data. Investigate why this is not a list:' + str(excelData))

    # If it's a list then we did a great job. Double check that it has at least one entry.
    if(len(excelData)<1):
        return('No data was found in the input excel file. Did you put any data in there?')

    url = getUrl()
    token = getToken(url=url)

    if(token==None):
        return('Could not aquire a login token.')

    try:
        uploadList = getUploads(token=token, url=url)
        uploadFileList = createFileListFromUploads(uploads=uploadList)
    except Exception as e:
        print('Exception when getting list of uploads:\n' + str(e) + '\n' + str(exc_info()))
        return ('Exception when getting list of uploads:\n' + str(e) )

    # Get list of upload HML IDs.
    # TODO: Check based on HML IDs as well. For now, just use filenames.
    #existingHMLIDs = getHMLIDs()

    # Do more specific validation of the columns. Check that each column is valid.
    validationFeedback = ''
    for dataRow in excelData:
        # findUniqueFile returns an empty string if a single file was found.
        validationFeedback += validateUniqueEntryInList(query=dataRow['hml_id_donor'], searchList=uploadFileList, allowPartialMatch=True, columnName='hml_id_donor')
        validationFeedback += validateUniqueEntryInList(query=dataRow['hml_id_recipient'], searchList=uploadFileList, allowPartialMatch=True, columnName='hml_id_recipient')
        validationFeedback += validateUniqueEntryInList(query=dataRow['haml_id_recipient_pre_tx'], searchList=uploadFileList, allowPartialMatch=True, columnName='haml_id_recipient_pre_tx')
        validationFeedback += validateUniqueEntryInList(query=dataRow['haml_id_recipient_post_tx'], searchList=uploadFileList, allowPartialMatch=True, columnName='haml_id_recipient_post_tx')
        validationFeedback += validateBoolean(query=dataRow['prozone_pre_tx'], columnName='prozone_pre_tx')
        validationFeedback += validateBoolean(query=dataRow['prozone_post_tx'], columnName='prozone_post_tx')
        validationFeedback += validateBoolean(query=dataRow['availability_pre_tx'], columnName='availability_pre_tx')
        validationFeedback += validateBoolean(query=dataRow['availability_post_tx'], columnName='availability_post_tx')
        validationFeedback += validateNumber(query=dataRow['months_post_tx'], columnName='months_post_tx')
        validationFeedback += validateMaleFemale(query=dataRow['gender_recipient'], columnName='gender_recipient')
        validationFeedback += validateNumber(query=dataRow['age_recipient_tx'], columnName='age_recipient_tx')
        validationFeedback += validateBoolean(query=dataRow['pregnancies_recipient'], columnName='pregnancies_recipient')
        validationFeedback += validateBoolean(query=dataRow['immune_suppr_post_tx'], columnName='immune_suppr_post_tx')

    if len(validationFeedback) < 1:
        return 'Valid'
    else:
        return validationFeedback

def createFileListFromUploads(uploads=None):
    fileNameList = []
    for upload in uploads:
        #print('upload:' + str(upload))
        fileName =upload['fileName']
        fileType = upload['type']
        #print('uploadFileName=' + fileName)
        #if(fileType=='HAML'):
        #    # TODO: Shouldn't need to do this if the upload entry has been created for the converted .haml file
        #    fileNameList.append(fileName + '.haml')
        #else:
        #    fileNameList.append(fileName)
        fileNameList.append(fileName)

    return fileNameList






