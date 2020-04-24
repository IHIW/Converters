from sys import exc_info
from SchemaValidation import validateAgainstSchema
from MiringValidation import validateMiring
from NmdpPortalValidation import validateNmdpPortal
from HamlValidation import validateHaml
from ValidationCommon import setValidationStatus

# Test methods for running the lambda function.

def testSchemaValidation():

    # Just a demo. First we validate a good HML document against the hml schema:
    schemaPath = 'schema/hml-1.0.1.xsd'
    xmlPath = 'xml/good.hml.1.0.1.xml'
    print('Validating XML: ' + str(xmlPath) + '\nagainst Schema: ' + str(schemaPath) + '\n')
    schemaText = open(schemaPath, 'rb').read()
    xmlText = open(xmlPath, 'rb').read()
    print(validateAgainstSchema(schemaText=schemaText, xmlText=xmlText) + '\n')

    # Then validate a bad hml document, and print the errors. Same thing.
    schemaPath = 'schema/hml-1.0.1.xsd'
    xmlPath = 'xml/bad.hml.1.0.1.xml'
    print('Validating XML: ' + str(xmlPath) + '\nagainst Schema: ' + str(schemaPath) + '\n')
    schemaText = open(schemaPath, 'rb').read()
    xmlText = open(xmlPath, 'rb').read()
    print(validateAgainstSchema(schemaText=schemaText, xmlText=xmlText) + '\n')

    # Try it with haml.
    schemaPath = 'schema/IHIW-haml_version_w0_3_3.xsd'
    xmlPath = 'xml/1497_1586843147576_HAML_BenTestMatchit.csv.haml'
    print('Validating XML: ' + str(xmlPath) + '\nagainst Schema: ' + str(schemaPath) + '\n')
    schemaText = open(schemaPath, 'rb').read()
    xmlText = open(xmlPath, 'rb').read()
    print(validateAgainstSchema(schemaText=schemaText, xmlText=xmlText) + '\n')

def testNmdpValidation():

    # Just a demo. First we validate a good HML document against the hml schema:
    xmlPath = 'xml/good.hml.1.0.1.xml'
    print('Validating Nmdp Gateway,  XML: ' + str(xmlPath) + '\n')
    xmlText = open(xmlPath, 'rb').read()
    print(validateNmdpPortal(xmlText=xmlText) + '\n')

def testSetValidationResults():
    uploadFileName = '1497_1587729544244_HML_bad.hml.1.0.1.xml'
    isValid = False
    validationFeedback = 'According to NMDP rules it is fine.'
    validatorType='NMDP'
    validationResult = setValidationStatus(uploadFileName=uploadFileName, isValid=isValid, validationFeedback=validationFeedback, validatorType=validatorType)
    #print('ValidationResult=' + str(validationResult))

    if (validationResult):
        print('Validation status for uploadFileName' + str(uploadFileName) + ' was set successfully to ' + str(isValid) + '.')
    else:
        print('FAILED to set validation status!')

if __name__=='__main__':
    try:
        #testSchemaValidation()
        #testNmdpValidation()
        testSetValidationResults()

        pass

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise