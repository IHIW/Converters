import io
import boto3
from boto3 import client
s3 = client('s3')

def writeFileToS3(s3ObjectBytestream=None,  newFileName=None, bucket=None):
    # xlOutputWorkbook is a xlwt.Workbook. We're saving it to a bytestream and writing it to S3.
    print('Writing a file to S3:' + str(newFileName))

    #s3ObjectBytestream = io.BytesIO()
    #xlOutputWorkbook.save(s3ObjectBytestream)
    #print('s3 object:' + str(s3ObjectBytestream))
    #s3ObjectBytestream.seek(0)

    s3 = boto3.resource("s3")
    print('saving file:' + str(newFileName))
    s3.Bucket(bucket).put_object(Key=newFileName, Body=s3ObjectBytestream.getvalue())
