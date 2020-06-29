from sys import exc_info
from SchemaValidation import validateAgainstSchema
from MiringValidation import validateMiring
from NmdpPortalValidation import validateNmdpPortal
from HamlValidation import validateHaml
import argparse

try:
    from IhiwRestAccess import setValidationStatus
except Exception:
    from Common.IhiwRestAccess import setValidationStatus

# Test methods for running the lambda function.
def parseArgs():
    parser = argparse.ArgumentParser()
    #parser.add_argument("-v", "--verbose", help="verbose operation", action="store_true")
    #parser.add_argument("-ex", "--excel", required=False, help="input excel file", type=str)
    #parser.add_argument("-up", "--upload", required=False, help="upload file name", type=str)
    parser.add_argument("-x", "--xml",  help="xml file to validate", type=str)
    parser.add_argument("-s", "--schema", help="schema file to validate against", type=str)

    return parser.parse_args()

def testSchemaValidation(xmlFileName=None, schemaFileName=None):
    # Just a demo. First we validate a good HML document against the hml schema:
    # Test Cases, try passing these to the method:
    # schemaPath = 'schema/hml-1.0.1.xsd'
    # xmlPath = 'xml/good.hml.1.0.1.xml'
    # schemaPath = 'schema/hml-1.0.1.xsd'
    # xmlPath = 'xml/bad.hml.1.0.1.xml'
    # schemaPath = 'schema/IHIW-haml_version_w0_3_3.xsd'
    # xmlPath = 'xml/OutputImmucor.haml'
    print('Validating XML: ' + str(xmlFileName) + '\nagainst Schema: ' + str(schemaFileName) + '\n')
    schemaText = open(schemaFileName, 'rb').read()
    xmlText = open(xmlFileName, 'rb').read()
    print(validateAgainstSchema(schemaText=schemaText, xmlText=xmlText) + '\n')

def testNmdpValidation():
    # Just a demo. First we validate a good HML document against the hml schema:
    xmlPath = 'xml/good.hml.1.0.1.xml'
    print('Validating Nmdp Gateway,  XML: ' + str(xmlPath) + '\n')
    xmlText = open(xmlPath, 'rb').read()
    print(validateNmdpPortal(xmlText=xmlText) + '\n')


def testMiringValidation():
    # Just a demo. First we validate a good HML document against the hml schema:
    xmlPath = 'xml/good.hml.1.0.1.xml'
    print('Validating MIRING,  XML: ' + str(xmlPath) + '\n')
    xmlText = open(xmlPath, 'rb').read()
    print(validateMiring(xmlText=xmlText) + '\n')


def testSetValidationResults():
    uploadFileName = '1_1592339213839_HAML_HLAM_Fusion.csv'
    isValid = True
    validationFeedback = 'According to NMDP rules it is fine.'
    validatorType='LOL'
    validationResult = setValidationStatus(uploadFileName=uploadFileName, isValid=isValid, validationFeedback=validationFeedback, validatorType=validatorType)
    #print('ValidationResult=' + str(validationResult))

    if (validationResult):
        print('Validation status for uploadFileName' + str(uploadFileName) + ' was set successfully to ' + str(isValid) + '.')
    else:
        print('FAILED to set validation status!')

if __name__=='__main__':
    try:
        args = parseArgs()
        xmlFilename = args.xml
        schemaFileName = args.schema

        testSchemaValidation(xmlFileName=xmlFilename, schemaFileName=schemaFileName)
        #testNmdpValidation()
        #testSetValidationResults()
        pass

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise