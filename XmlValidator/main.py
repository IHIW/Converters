from sys import exc_info
import argparse

try:
    import Common.IhiwRestAccess as IhiwRestAccess
    import XmlValidator.NmdpPortalValidation as NmdpPortalValidation
    import XmlValidator.MiringValidation as MiringValidation
    import XmlValidator.SchemaValidation as SchemaValidation
except Exception:
    import IhiwRestAccess
    import NmdpPortalValidation
    import MiringValidation
    import SchemaValidation

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
    print(SchemaValidation.validateAgainstSchema(schemaText=schemaText, xmlText=xmlText) + '\n')

def testNmdpValidation():
    # Just a demo. First we validate a good HML document against the hml schema:
    #xmlPath = 'XmlValidator/xml/good.hml.1.0.1.xml'
    xmlPath='/home/bmatern/UMCU/Test Files/HML/TestMiring.xml'
    #xmlPath='/home/bmatern/UMCU/Test Files/HML/TestMiringBackup.BrokenNMDP.xml'
    #xmlPath='/home/bmatern/UMCU/Test Files/HML/LONGNAMELONGNAMELONGNAMELONGNAMELONGNAMELONGNAMELONGNAME.xml'
    print('Validating Nmdp Gateway,  XML: ' + str(xmlPath) + '\n')
    xmlText = open(xmlPath, 'r').read().strip()
    #print(validateNmdpPortal(xmlText=xmlText) + '\n')
    validationResultXml = NmdpPortalValidation.validateNmdpPortal(xmlText=xmlText)


    print('validationResultsXml:' + validationResultXml + '\n')
    isValid, validationFeedbackText = NmdpPortalValidation.parseNmdpXml(xmlText=validationResultXml)

    print('isValid:' + str(isValid))
    print('validationFeedbackText:\n' + str(validationFeedbackText))


def testMiringValidation():
    # Just a demo. First we validate a good HML document against the hml schema:
    xmlPath = 'XmlValidator/xml/TestMiring.xml'
    print('Validating MIRING,  XML: ' + str(xmlPath) + '\n')
    xmlText = open(xmlPath, 'rb').read()
    validationResultXml = MiringValidation.validateMiring(xmlText=xmlText)

    #print('validationResultsXml:' + validationResultXml + '\n')
    isValid, validationFeedbackText = MiringValidation.parseMiringXml(xmlText=validationResultXml)

    print('isValid:' + str(isValid))
    print('validationFeedbackText:\n' + str(validationFeedbackText))


def testSetValidationResults():
    uploadFileName = '1_1592339213839_HAML_HLAM_Fusion.csv'
    isValid = True
    validationFeedback = 'According to NMDP rules it is fine.'
    validatorType='LOL'
    validationResult = IhiwRestAccess.setValidationStatus(uploadFileName=uploadFileName, isValid=isValid, validationFeedback=validationFeedback, validatorType=validatorType)
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

        #testSchemaValidation(xmlFileName=xmlFilename, schemaFileName=schemaFileName)
        #testMiringValidation()
        testNmdpValidation()
        #testSetValidationResults()
        pass

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise