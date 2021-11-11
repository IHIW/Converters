from sys import exc_info
import argparse
from os.path import split, join
from io import BytesIO

#from Common.IhiwRestAccess import setValidationStatus, getProjectID
#from Common.ParseExcel import createBytestreamExcelOutputFile
#from Common.S3_Access import writeFileToS3
#from Common.ParseExcel import writeExcelToFile
#from Components.Immunogenic_Epitopes.ImmunogenicEpitopesValidator import validateEpitopesDataMatrix
#from Components.Immunogenic_Epitopes.ImmunogenicEpitopesProjectReport import createImmunogenicEpitopesReport
from Components.Reference_CellLines.NgsReferenceCellLinesProjectReport import createReferenceCellLinesReport


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--validator", required=True, help="validator type", type=str)
    parser.add_argument("-b", "--bucket", required=False, help="S3 Bucket Name", type=str )

    return parser.parse_args()


def testCreateReferenceCellLineProjectReport(args=None):
    print('Testing the Reference Cell Lines Project Report')
    createReferenceCellLinesReport(bucket=args.bucket)

if __name__=='__main__':
    try:
        args=parseArgs()
        validatorType =args.validator
        if(validatorType=='REFERENCE_CELL_LINE_PROJECT_REPORT'):
            testCreateReferenceCellLineProjectReport(args=args)
        else:
            print('I do not understand the validator type.')


    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise
