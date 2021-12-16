from sys import exc_info

def default_validation_handler(event, context):
    # Simple Stuff. If the data looks OK, just call the file valid.
    print('I found the Default validation handler.')
    uploadDetails={}

    try:
        # Fetching the upload detail bundle from the step function payload
        if "Input" in event and "Payload" in event['Input']:
            uploadDetails = event['Input']['Payload']
            uploadDetails['is_valid'] = True
            uploadDetails['validation_feedback'] = 'No Validator exists for this file type. Thanks for uploading your data!'
            uploadDetails['validator_type'] = 'DEFAULT'

        else:
            uploadDetails['is_valid'] = False
            uploadDetails['validation_feedback'] = 'The input event payload does not seem to contain the expected upload data. Something went wrong in the default validation part of the step function flow.'
            uploadDetails['validator_type'] = 'DEFAULT'
            print(str(uploadDetails['validation_feedback']))
            return uploadDetails

    except Exception as e:
        exceptionText = 'Exception:\n' + str(e) + '\n' + str(exc_info())
        print(exceptionText)
        uploadDetails['is_valid'] = False
        uploadDetails['validation_feedback'] = exceptionText
        uploadDetails['validator_type'] = 'DEFAULT'

    return uploadDetails


