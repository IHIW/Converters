from sys import exc_info
import argparse

from Common import IhiwRestAccess
from Common.S3_Access import createProjectZipFile
from Components.FamilyHaplotypes.FamilyHaplotypesProjectReport import createFamilyHaplotypeReport


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--validator", required=True, help="validator type", type=str)
    parser.add_argument("-b", "--bucket", required=False, help="S3 Bucket Name", type=str )

    return parser.parse_args()

def testCreateFamilyHaplotypeProjectReport(args=None):
    print('Testing the Reference Cell Lines Project Report')
    projectID = 390

    url=IhiwRestAccess.getUrl()
    token=IhiwRestAccess.getToken(url=url)
    
    createFamilyHaplotypeReport(bucket=args.bucket, url=url, token=token, projectIDs=[projectID], fileTypeFilter=['HML','OTHER','PED','INFO_CSV'])
    createProjectZipFile(bucket=args.bucket, url=url, token=token, projectIDs=[projectID], fileTypeFilter=['HML','OTHER','PED','INFO_CSV'])


if __name__=='__main__':
    try:
        args=parseArgs()
        validatorType =args.validator
        if(validatorType=='FAMILY_HAPLOTYPE_PROJECT_REPORT'):
            testCreateFamilyHaplotypeProjectReport(args=args)
        else:
            print('I do not understand the validator type.')

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise