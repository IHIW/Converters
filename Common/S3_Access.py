import boto3
from boto3 import client
s3 = client('s3')

def writeFileToS3(s3ObjectBytestream=None, newFileName=None, bucket=None):
    print('Writing a file to S3:' + str(newFileName) + ' to bucket: ' + str(bucket))
    # print('The bytestream is of this type:' + str(type(s3ObjectBytestream)))
    try:
        s3 = boto3.resource("s3")
        print('saving file:' + str(newFileName))
        # This is valid in the case of XL spreadsheets, which are io.BytesIO streams. different stream types might break this.
        body = s3ObjectBytestream.getvalue()
        s3.Bucket(bucket).put_object(Key=newFileName, Body=body)
        print('Done saving file.')
    except Exception as e:
        print('Problem saving file!\n' + str(e))
