from boto3 import client
s3 = client('s3')
#from lxml import etree
from sys import exc_info, path
#import json
#import urllib

# For importing common methods, may be in the same directory when deployed as a package
try:
    from IhiwRestAccess import getHMLFilenames, getHMLIDs, getHAMLFilenames
    from ParseExcel import parseExcelFile
    from Validation import validateUniqueFileEntry, validateBoolean, validateNumber, validateMaleFemale
except Exception:
    from Common.IhiwRestAccess import getHMLFilenames, getHMLIDs, getHAMLFilenames
    from Common.ParseExcel import parseExcelFile
    from Common.Validation import validateUniqueEntryInList, validateBoolean, validateNumber, validateMaleFemale

def immunogenic_epitope_handler(event, context):
    print('I found the schema validation handler.')
    # This is the AWS Lambda handler function.
    try:
        # Get the uploaded file.
        #content = json.loads(event['Records'][0]['Sns']['Message'])

        #bucket = content['Records'][0]['s3']['bucket']['name']
        #xmlKey = urllib.parse.unquote_plus(content['Records'][0]['s3']['object']['key'], encoding='utf-8')
        #xmlFileObject = s3.get_object(Bucket=bucket, Key=xmlKey)
        #xmlText = xmlFileObject["Body"].read()


        validationResults='Valid'
        return str(validationResults)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)



def validateEpitopesDataMatrix(excelFile=None, columnNames=None):
    print('Validating Epitopes Data Matrix:' + excelFile)

    excelData = parseExcelFile(excelFile=excelFile, columnNames=columnNames)

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

    # Get a list of the upload HML files.
    existingHMLFilenames = getHMLFilenames()

    # Get list of upload HML IDs.
    # TODO: Check based on HML IDs as well. For now, just use filenames.
    #existingHMLIDs = getHMLIDs()

    # Get a list of the upload HAML files.
    existingHAMLFilenames = getHAMLFilenames()

    # Do more specific validation of the columns. Check that each column is valid.
    validationFeedback = ''
    for dataRow in excelData:
        # findUniqueFile returns an empty string if a single file was found.
        validationFeedback += validateUniqueEntryInList(query=dataRow['hml_id_donor'], searchList=existingHMLFilenames, allowPartialMatch=True, columnName='hml_id_donor')
        validationFeedback += validateUniqueEntryInList(query=dataRow['hml_id_recipient'], searchList=existingHMLFilenames, allowPartialMatch=True, columnName='hml_id_recipient')
        validationFeedback += validateUniqueEntryInList(query=dataRow['haml_id_recipient_pre_tx'], searchList=existingHAMLFilenames, allowPartialMatch=True, columnName='haml_id_recipient_pre_tx')
        validationFeedback += validateUniqueEntryInList(query=dataRow['haml_id_recipient_post_tx'], searchList=existingHAMLFilenames, allowPartialMatch=True, columnName='haml_id_recipient_post_tx')
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






