from sys import exc_info
import argparse

from Common import IhiwRestAccess
from Common.S3_Access import createProjectZipFile
from Components.Reference_CellLines.NgsReferenceCellLinesProjectReport import createReferenceCellLinesReport


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--validator", required=True, help="validator type", type=str)
    parser.add_argument("-b", "--bucket", required=False, help="S3 Bucket Name", type=str )

    return parser.parse_args()


'''
def testReferenceCellLinesData(args):
    url = IhiwRestAccess.getUrl()
    token = IhiwRestAccess.getToken(url=url)

    immuEpsProjectID = 394

    
    '''


def testCreateReferenceCellLineProjectReport(args=None):
    print('Testing the Reference Cell Lines Project Report')
    projectID = 394

    url=IhiwRestAccess.getUrl()
    token=IhiwRestAccess.getToken(url=url)

    createProjectZipFile(bucket=args.bucket, url=url, token=token, projectIDs=[projectID], fileTypeFilter=['HML','OTHER'])

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
