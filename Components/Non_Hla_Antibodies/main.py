from sys import exc_info
import argparse
from os.path import split, join
#from io import BytesIO
from Common import IhiwRestAccess
#from Common.ParseExcel import createBytestreamExcelOutputFile
#from Common.S3_Access import writeFileToS3, createProjectZipFile
#from Common.IhiwRestAccess import getProjectID

from Components.Non_Hla_Antibodies.NonHlaAntibodiesValidator import validateNonHlaAntibodiesDataMatrix
from Components.Non_Hla_Antibodies.NonHlaAntibodiesProjectReport import createNonHlaAntibodiesReport

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--validator", required=True, help="validator type", type=str)
    parser.add_argument("-ex", "--excel", required=False, help="input excel file", type=str)
    parser.add_argument("-up", "--upload", required=False, help="upload file name", type=str)
    parser.add_argument("-b", "--bucket", required=False, help="S3 Bucket Name", type=str )
    parser.add_argument("-i", "--input", required=False, help="Input Folder", type=str)

    return parser.parse_args()

def testValidateNonHlaAntibodies(args=None):
    print('Starting up the NonHlaAntibodies validator.')

    nonHlaProjectNumber = IhiwRestAccess.getProjectID(projectName='non_hla_antibodies')

    (validationResults, outputReportWorkbook) = validateNonHlaAntibodiesDataMatrix(excelFile=args.excel, projectIDs=[nonHlaProjectNumber])
    print('Validation Results:\n' + str(validationResults))

    head, tail = split(args.excel)
    reportFileName = tail.replace('.xlsx', '.Validation_Report.xlsx')

    reportLocalFilePath = join(head, reportFileName)
    print('Saving to ' + str(reportLocalFilePath))
    outputReportWorkbook.save(reportLocalFilePath)


def testCreateNonHlaAntibodiesProjectReport(args=None):
    projectID = 404

    url=IhiwRestAccess.getUrl()
    token=IhiwRestAccess.getToken(url=url)

    createNonHlaAntibodiesReport(token=token,url=url, bucket=args.bucket, projectIDs=[projectID])


if __name__=='__main__':
    try:
        args=parseArgs()
        validatorType =args.validator
        if(validatorType=='NON_HLA_ANTIBODIES'):
            testValidateNonHlaAntibodies(args=args)
        elif(validatorType=='NON_HLA_ANTIBODIES_PROJECT_REPORT'):
            testCreateNonHlaAntibodiesProjectReport(args=args)
        else:
            print('I do not understand the validator type.')


    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise
