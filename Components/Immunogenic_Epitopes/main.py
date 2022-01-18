from sys import exc_info
import argparse
from os.path import split, join
from io import BytesIO

#from Common.IhiwRestAccess import setValidationStatus, getProjectID
from Common import IhiwRestAccess
from Common.ParseExcel import createBytestreamExcelOutputFile
from Common.S3_Access import writeFileToS3
#from Common.ParseExcel import writeExcelToFile
from Components.Immunogenic_Epitopes.ImmunogenicEpitopesValidator import validateEpitopesDataMatrix
from Components.Immunogenic_Epitopes.ImmunogenicEpitopesProjectReport import createProjectZipFile, createImmunogenicEpitopesReport

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--validator", required=True, help="validator type", type=str)
    parser.add_argument("-ex", "--excel", required=False, help="input excel file", type=str)
    parser.add_argument("-up", "--upload", required=False, help="upload file name", type=str)
    parser.add_argument("-b", "--bucket", required=False, help="S3 Bucket Name", type=str )
    parser.add_argument("-i", "--input", required=False, help="Input Folder", type=str)

    return parser.parse_args()

def testValidateImmunogenicEpitopes(args=None):
    print('Starting up the immuno epitopes methods.')

    immunogenicEpitopeProjectNumber = getProjectID(projectName='immunogenic_epitopes')
    dqImmunogenicityProjectNumber = getProjectID(projectName='dq_immunogenicity')

    (validationResults, outputReportWorkbook) = validateEpitopesDataMatrix(excelFile=args.excel, isImmunogenic=True, projectIDs=[immunogenicEpitopeProjectNumber, dqImmunogenicityProjectNumber])
    print('Validation Results:\n' + str(validationResults))

    head, tail = split(args.excel)
    reportFileName = tail.replace('.xlsx', '.Validation_Report.xlsx')

    reportLocalFilePath = join(head, reportFileName)
    print('Saving to ' + str(reportLocalFilePath))
    outputReportWorkbook.save(reportLocalFilePath)


def testValidateNonImmunogenicEpitopes(excelFile=None):
    print('Starting up the non immunogenic epitopes methods.')

    nonImmunogenicEpitopeProjectNumber = getProjectID(projectName='non_immunogenic_epitopes')
    (validationResults, outputReportWorkbook) = validateEpitopesDataMatrix(excelFile=excelFile, isImmunogenic=False, projectIDs=[nonImmunogenicEpitopeProjectNumber])
    print('Validation Results:\n' + str(validationResults))

    validationFeedback = ''
    for validationError in validationResults:
        #for validationColumnName in validationErrorRow.keys():
        #currentValidationResult = validationErrorRow[validationColumnName]
        if(validationError is not None and len(validationError) > 0):
            validationFeedback = validationFeedback + validationError + ';\n'

    head, tail = split(excelFile)
    reportFileName = tail + '.Validation_Report.xlsx'


    # Write to S3 (commented for testing)
    reportStreamData=createBytestreamExcelOutputFile(workbookObject=outputReportWorkbook)
    #writeFileToS3(newFileName=reportFileName, bucket=args.bucket, s3ObjectBytestream=reportStreamData)

    # Write to local file
    reportLocalFilePath = join(head, reportFileName)
    print('Saving to ' + str(reportLocalFilePath))
    outputReportWorkbook.save(reportLocalFilePath)


def testSetValidationResults(args=None):
    uploadFileName = args.upload
    isValid = False
    validationFeedback = ('In data column hml_id_donor I could not find an uploaded file with the name (2_1590401697183_HML_good.hml.1.0.1.xml); ' +
        'In data column hml_id_recipient I could not find an uploaded file with the name (fake.hml); ' +
        'In data column haml_id_recipient_pre_tx I could not find an uploaded file with the name (2_1590401779132_HAML_HamlFromNewConverter.xml); ' +
        'In data column haml_id_recipient_post_tx I could not find an uploaded file with the name (2_1590401779132_HAML_HamlFromNewConverter.xml); ' +
        'In data column hml_id_donor I could not find an uploaded file with the name (2_1590401697183_HML_good.hml.1.0.1.xml); ' +
        'In data column hml_id_recipient For file entry (good.hml.1.0.1.hml), 2 matching files were found:(1497_1589832668946_HML_good.hml.1.0.1.hml) , (1497_1590413494993_HML_good.hml.1.0.1.hml) ,; ' +
        'In data column haml_id_recipient_pre_tx I could not find an uploaded file with the name (2_1590401816855_HAML_HLAM_Fusion.csv); ' +
        'In data column haml_id_recipient_post_tx I could not find an uploaded file with the name (2_1590401779132_HAML_HamlFromNewConverter.xml); ' +
        'In data column hml_id_donor I could not find an uploaded file with the name (2_1590401697183_HML_good.hml.1.0.1.xml); ' +
        'In data column hml_id_recipient I could not find an uploaded file with the name (2_1590401697183_HML_good.hml.1.0.1.xml); ' +
        'In data column haml_id_recipient_pre_tx I could not find an uploaded file with the name (2_1590401816855_HAML_HLAM_Fusion.csv); ' +
        'In data column haml_id_recipient_post_tx I could not find an uploaded file with the name (2_1590401816855_HAML_HLAM_Fusion.csv); ' +
        'In data column hml_id_donor I could not find an uploaded file with the name (2_1590401697183_HML_good.hml.1.0.1.xml); ' +
        'In data column hml_id_recipient I could not find an uploaded file with the name (2_1590401697183_HML_good.hml.1.0.1.xml); ' +
        'In data column haml_id_recipient_pre_tx I could not find an uploaded file with the name (2_1590401816855_HAML_HLAM_Fusion.csv.haml); ' +
        'In data column haml_id_recipient_post_tx I could not find an uploaded file with the name (2_1590401816855_HAML_HLAM_Fusion.csv); ')
    validatorType='IMMUNOGENIC_EPITOPES'
    validationResult = setValidationStatus(uploadFileName=uploadFileName, isValid=isValid, validationFeedback=validationFeedback, validatorType=validatorType)
    #print('ValidationResult=' + str(validationResult))

    if (validationResult):
        print('Validation status for uploadFileName' + str(uploadFileName) + ' was set successfully to ' + str(isValid) + '.')
    else:
        print('FAILED to set validation status!')

def testWriteFileS3(args=None):
    print('Opening Input Workbook...')
    excelFile=args.excel
    inputWorkbookData = parseExcelFile(excelFile=excelFile)
    if(inputWorkbookData is None or len(inputWorkbookData) < 1):
        print('I failed to open the input workbook data. Cannot continue.')
        return None
    else:
        pass
        print('Workbook was opened, this is the data:' + str(inputWorkbookData))

    # Some test errors. The column headers with errors are stored for each line
    errors = [{'prozone_post_tx':'This cell is missing data'},{'availability_pre_tx':'File is wrong format or whatever.'}]

    # Create output files
    outputWorkbook, outputWorkbookbyteStream = createExcelValidationReport(errors=errors, inputWorkbookData=inputWorkbookData)

    # Write the Excel File to S3 storage.
    writeFileToS3(newFileName=args.upload, bucket=args.bucket, s3ObjectBytestream=outputWorkbookbyteStream)

def testCreateSchemaFilesS3(args=None):
    inputFolder = args.input
    bucket = args.bucket
    print('Uploading schema files from ' + str(inputFolder) + ' to bucket ' + str(bucket))

    schemaRemoteOutputFolder = 'schema'
    # Write it to S3.
    for fileName in ['hml-1.0.1.xsd', 'IHIW-haml_version_w0_3_3.xsd']:
        localPath = join(inputFolder, fileName)
        remotePath = join(schemaRemoteOutputFolder, fileName)
        print('writing file ' + str (localPath) + ' to remote ' + str(remotePath))
        fileByteStream = open(localPath,'rb')
        bytesIOObject = BytesIO(fileByteStream.read())

        #writeFileToS3(newFileName=remotePath, bucket=bucket, s3ObjectBytestream=bytesIOObject)



def testCreateImmunogenicEpitopesProjectReport(args=None):
    print('Creating Immunogenic Epitopes Project Report')
    #createImmunogenicEpitopesReport(bucket=args.bucket)

    url=IhiwRestAccess.getUrl()
    token=IhiwRestAccess.getToken(url=url)
    immuEpsProjectID = IhiwRestAccess.getProjectID(projectName='immunogenic_epitopes')
    nonImmuEpsProjectID = IhiwRestAccess.getProjectID(projectName='non_immunogenic_epitopes')
    dqEpsProjectID = IhiwRestAccess.getProjectID(projectName='dq_immunogenicity')

    #createProjectZipFile(bucket=args.bucket, url=url, token=token, projectIDs=[immuEpsProjectID,nonImmuEpsProjectID,dqEpsProjectID])

    createImmunogenicEpitopesReport(bucket=args.bucket, projectIDs=[dqEpsProjectID])
    createImmunogenicEpitopesReport(bucket=args.bucket, projectIDs=[immuEpsProjectID])


if __name__=='__main__':
    try:
        args=parseArgs()
        validatorType =args.validator
        if(validatorType=='IMMUNOGENIC_EPITOPES'):
            testValidateImmunogenicEpitopes(args=args)
        elif (validatorType == 'NON_IMMUNOGENIC_EPITOPES'):
            testValidateNonImmunogenicEpitopes(excelFile=args.excel)
        elif (validatorType == 'IMMUNOGENIC_EPITOPES_PROJECT_REPORT'):
            testCreateImmunogenicEpitopesProjectReport(args=args)
        elif(validatorType=='SET_VALIDATION_RESULTS'):
            testSetValidationResults(args=args)
        elif (validatorType == 'WRITE_FILE_S3'):
            testWriteFileS3(args=args)
        elif(validatorType=='CREATE_SCHEMA_FILES'):
            testCreateSchemaFilesS3(args=args)
        else:
            print('I do not understand the validator type.')


    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise
