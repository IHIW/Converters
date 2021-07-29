from IhiwRestAccess import getCredentials, getUrl, getToken, getUploadIfExists

def prepare_validation_handler(event, context):
    print('Preparing Validation...')

    uploadDetails= {}

    # Get some info about the upload
    if "Input" in event and "detail" in event['Input'] and "requestParameters" in event['Input']['detail'] and "key" in \
            event['Input']['detail']['requestParameters']:
        file_name = event['Input']['detail']['requestParameters']['key']
        file_name_components = file_name.split(".")
        file_ending = file_name_components[len(file_name_components) - 1].upper()
        uploadDetails['file_ending'] = str(file_ending)
        uploadDetails['file_name'] = str(file_name)
        bucket_name = event['Input']['detail']['requestParameters']['bucketName']
        uploadDetails['bucket'] = str(bucket_name)
    else:
        uploadDetails['file_name'] = "UNKNOWN"
        uploadDetails['file_ending'] = "UNKNOWN"
        uploadDetails['bucket']= "UNKNOWN"

    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)
    if(url is None or token is None or len(url)==0 or len(token)==0):
        print('Unable to fetch URL and Token from Config File.')
        uploadDetails['url']= "UNKNOWN"
        uploadDetails['token']= "UNKNOWN"
    else:
        uploadDetails['url']=str(url)
        uploadDetails['token']=str(token)

    # Wrapper, exception handling
    try:
        uploadFile = getUploadIfExists(token=token, url=url, fileName=file_name)
        uploadDetails['id'] = str(uploadFile['id'])
        uploadDetails['project_name'] = str(uploadFile['project']['name'])
        uploadDetails['project_id'] = str(uploadFile['project']['id'])
        uploadDetails['upload_type'] = str(uploadFile['type'])

    except Exception as e:
        print('Exception fetching uploaded object:' + str(e))
        uploadDetails['id'] = "UNKNOWN"
        uploadDetails['project_name'] = "UNKNOWN"
        uploadDetails['project_id'] = "UNKNOWN"
        uploadDetails['upload_type'] = "UNKNOWN"

    return uploadDetails