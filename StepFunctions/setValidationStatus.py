from IhiwRestAccess import setValidationStatus
import urllib

def set_validation_status_handler(event, context):
    print('EVENT:')
    print(str(event))

    hamlKey = event['Input']['Payload']['Input']['Payload']['file_name']
    decodedKey = urllib.parse.unquote_plus(hamlKey)
    #print('hamlKey:' + str(hamlKey))

    token = event['Input']['Payload']['Input']['Payload']['token']
    url = event['Input']['Payload']['Input']['Payload']['url']
    #print('token=' + str(token))

    isValid= event['Input']['Payload']['is_valid']
    validationText=event['Input']['Payload']['validation_text']
    print('isValid=' + str(isValid))
    print('validationText=' + str(validationText))

    #setValidationStatus(token=token, url=url, isValid=isValid, validationFeedback=validationText)
    setValidationStatus(uploadFileName=decodedKey, isValid=isValid, validationFeedback=validationText, validatorType='POSITIVE_BEADS', token=token, url=url)

    return event