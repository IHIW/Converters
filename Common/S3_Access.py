import boto3
from boto3 import client
import io
s3 = client('s3')

def writeFileToS3(s3ObjectBytestream=None, newFileName=None, bucket=None):
    print('Writing a file to S3:' + str(newFileName) + ' to bucket: ' + str(bucket))
    # print('The bytestream is of this type:' + str(type(s3ObjectBytestream)))
    try:
        s3 = boto3.resource("s3")
        print('saving file:' + str(newFileName))
        #print('bytestream has this type:' + str(type(s3ObjectBytestream)))
        # Some bytestream-like objects are different than others. Handle it nicely.
        if (type(s3ObjectBytestream) is io.BytesIO):
            body = s3ObjectBytestream.getvalue()
        else:
            body = s3ObjectBytestream
        # This is valid in the case of XL spreadsheets, which are io.BytesIO streams. different stream types might break this.
        #body = s3ObjectBytestream.getvalue()
        # This is for openpyxl bytestreams
        #body=s3ObjectBytestream
        s3.Bucket(bucket).put_object(Key=newFileName, Body=body)
        print('Done saving file.')
    except Exception as e:
        print('Problem saving file!\n' + str(e))

def getUploadListFromS3(bucket=None):
    print('Getting upload list from bucket:' + str(bucket))
    try:
        s3 = boto3.resource("s3")

        objectList = s3.Bucket(bucket).objects.all()

        print('Done getting Upload List.')

        return objectList
    except Exception as e:
        print('Problem saving file!\n' + str(e))


def revalidateUpload(bucket=None, uploadFilename=None):
    print('Touching the upload ' + str(uploadFilename) + ' in bucket ' + str(bucket))
    try:
        # TODO: Understand the difference between Resource and Client
        s3Resource = boto3.resource("s3")
        s3Client = client('s3')

        # Read ByteSteam
        fileObject = s3Client.get_object(Bucket=bucket, Key=uploadFilename)
        byteStream = fileObject["Body"].read()

        # Put the object back where I found it
        # TODO: Copying the object to itself, in place, does not trigger the cloudtrail, and the step functions.  "Put" does work
        s3Resource.Bucket(bucket).put_object(Key=uploadFilename, Body=byteStream)

    except Exception as e:
        print('Problem Revalidating Upload:\n' + str(e))