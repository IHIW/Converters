from IhiwRestAccess import getCredentials, getUrl, getToken, getUploadIfExists

def prepare_validation_handler(event, context):
    print('Preparing Validation...')
    # extract file ending
    if "Input" in event and "detail" in event['Input'] and "requestParameters" in event['Input']['detail'] and "key" in \
            event['Input']['detail']['requestParameters']:
        file_name = event['Input']['detail']['requestParameters']['key']
        file_name_components = file_name.split(".")
        file_ending = file_name_components[len(file_name_components) - 1].upper()
        event['file_ending'] = file_ending
        event['file_name'] = file_name
    else:
        event['file_ending'] = "UNKNOWN"

    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)
    if(url is None or token is None or len(url)==0 or len(token)==0):
        print('Unable to fetch URL and Token from Config File.')
        event['url']="UNKNOWN"
        event['token']="UNKNOWN"
    else:
        event['url']=url
        event['token']=token

    # Wrapper, exception handling
    try:
        uploadFile = getUploadIfExists(token=token, url=url, fileName=file_name)
        event['project_name'] = uploadFile['project']['name']
        event['project_id'] = uploadFile['project']['id']
        event['upload_type'] = uploadFile['type']

    except Exception as e:
        print('Exception fetching uploaded object:' + str(e))
        event['project_name'] = "UNKNOWN"
        event['project_id'] = "UNKNOWN"
        event['upload_type'] = "UNKNOWN"

    # some more init steps

    return event