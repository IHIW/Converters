from boto3 import client
#import json
#import urllib


try:
    import IhiwRestAccess
    import S3_Access
    import ParseXml

except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common import IhiwRestAccess
    from Common import S3_Access
    from Common import ParseXml

s3 = client('s3')
from sys import exc_info

import zipfile
import io
from time import sleep



