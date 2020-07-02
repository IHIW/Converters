def writeFileToS3(fileBinaryObject=None, newFileName=None):
    print('Writing a file to S3:' + str(newFileName))

    #            s3 = boto3.resource("s3")
        #print('saving file:' + str(xmlOutput))
        #s3.Bucket(bucket).put_object(Key=xmlOutput, Body=encoded_string)