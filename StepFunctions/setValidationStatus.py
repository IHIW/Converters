from IhiwRestAccess import setValidationStatus
import urllib

def set_validation_status_handler(event, context):
    print('EVENT:')
    print(str(event))

    # Some default JSON to help with debugging, this will be replaced by the event payload
    uploadDetails = {}
    uploadDetails['is_valid'] = False
    uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the step function flowchart.'
    uploadDetails['validator_type'] = 'SET_VALIDATION_STATUS'

    try:
        # Fetching the upload detail bundle from the step function payload
        if "Input" in event and "Payload" in event['Input']:
            uploadDetails = event['Input']['Payload']
        else:
            print(str(uploadDetails['validation_feedback']))
            return uploadDetails

        uploadFileName = uploadDetails['file_name']

        decodedKey = urllib.parse.unquote_plus(uploadFileName)

        url = uploadDetails['url']
        token = uploadDetails['token']

        isValid = uploadDetails['is_valid']
        validationFeedback = uploadDetails['validation_feedback']
        validatorType = uploadDetails['validator_type']

        print('isValid=' + str(isValid))
        print('validationFeedback=' + str(validationFeedback))

        setValidationStatus(uploadFileName=decodedKey, isValid=isValid, validationFeedback=validationFeedback, validatorType=validatorType, token=token, url=url)

    except Exception as e:
        uploadDetails['validation_feedback'] = 'Cannot fetch the data about the upload file I need to set the validation status:' + str(e)
        print(uploadDetails['validation_feedback'])
        return uploadDetails

    return event