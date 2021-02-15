from os import makedirs, getcwd
from os.path import isdir, join
from sys import exc_info
import argparse

#from  import parseXml

try:
    import Common.IhiwRestAccess as IhiwRestAccess
    import Common.ParseXml as ParseXml
    import Common.Validation as Validation
    import XmlValidator.NmdpPortalValidation as NmdpPortalValidation
    import XmlValidator.MiringValidation as MiringValidation
    import XmlValidator.SchemaValidation as SchemaValidation
    import XmlValidator.HmlGlStringParser as HmlGlStringParser
except Exception:
    import IhiwRestAccess
    import ParseXml
    import Validation
    import NmdpPortalValidation
    import MiringValidation
    import SchemaValidation
    import HmlGlStringParser

# Test methods for running the lambda function.
def parseArgs():
    parser = argparse.ArgumentParser()
    #parser.add_argument("-v", "--verbose", help="verbose operation", action="store_true")
    #parser.add_argument("-ex", "--excel", required=False, help="input excel file", type=str)
    parser.add_argument("-up", "--upload", required=False, help="upload file name", type=str)
    parser.add_argument("-x", "--xml",  help="xml file to validate", type=str)
    parser.add_argument("-s", "--schema", help="schema file to validate against", type=str)
    parser.add_argument("-t", "--test", help="what kind of test should we perform", type=str)
    parser.add_argument("-o", "--output", help="output directory", type=str)

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


def testHmlParser(xmlFileName=None, outputDirectory=None):
    print('Testing the HML Parser with filename:' + str(xmlFileName))
    xmlText = open(xmlFileName, 'r').read()
    #print('xmlText:\n' + str(xmlText))

    hmlObject = ParseXml.parseXmlFromText(xmlText=xmlText)
    sampleIds = ParseXml.getSampleIDs(hml=hmlObject)
    hmlId = ParseXml.getHmlid(xmlText=xmlText)
    glStrings = ParseXml.getGlStrings(hml=hmlObject)
    print('I found this HMLID:' + str(hmlId))
    print('I found these SampleIDs:' + str(sampleIds))
    print('I found this glStrings:' + str(glStrings))

    glStringValidity, glStringValidationFeedback = Validation.validateGlStrings(glStrings=glStrings)
    print('glstringValidity:' + str(glStringValidity))
    print('glStringValidationFeedback:' + str(glStringValidationFeedback))

    # Write some data from the HML to file (These are named based on sample ID)
    hmlObject.tobiotype(outputDirectory, dtype='fasta', by='subject')
    xmlDirectory=join(getcwd(),'XmlValidator/xml')
    alignSequences=True
    isValid, validationResults = ParseXml.extrapolateConsensusFromVariants(hml=hmlObject, outputDirectory=outputDirectory, xmlDirectory=xmlDirectory, alignSequences=alignSequences)
    print('IsValid:' + str(isValid))
    print('validationResults:' + str(validationResults))


def testDeleteFile(uploadFileName=None, configFileName='XmlValidator/validation_config.yml' ):
    print('Deleting an upload with the name:' + str(uploadFileName))
    (user, password) = IhiwRestAccess.getCredentials(configFileName=configFileName)
    url = IhiwRestAccess.getUrl(configFileName=configFileName)
    print('URL=' + str(url))
    token = IhiwRestAccess.getToken(user=user, password=password, url=url)
    uploadId = IhiwRestAccess.getUploadIfExists(token=token, url=url, fileName=uploadFileName)
    print('I found this upload id:' + str(uploadId['id']))
    response = IhiwRestAccess.deleteUpload(token=token, url=url, uploadId=uploadId['id'])
    print('I found this response:' + str(response))


def testGetUpload(uploadFileName=None, configFileName='XmlValidator/validation_config.yml'):
    print('Getting an upload an upload with the name:' + str(uploadFileName))
    (user, password) = IhiwRestAccess.getCredentials(configFileName=configFileName)
    url = IhiwRestAccess.getUrl(configFileName=configFileName)
    print('URL=' + str(url))
    token = IhiwRestAccess.getToken(user=user, password=password, url=url)
    uploadId = IhiwRestAccess.getUploadIfExists(token=token, url=url, fileName=uploadFileName)
    print('I found this upload id:' + str(uploadId['id']))

if __name__=='__main__':
    try:
        args = parseArgs()
        xmlFilename = args.xml
        schemaFileName = args.schema

        currentTest = str(args.test.upper())
        print('CurrentTest:' + currentTest)
        print(str(type(currentTest)))

        outputDirectory = args.output
        if(outputDirectory is not None and not isdir(outputDirectory)):
            print('Creating output directory:' + str(outputDirectory))
            makedirs(outputDirectory)

        if (currentTest=='HMLPARSER'):
            testHmlParser(xmlFileName=xmlFilename, outputDirectory=outputDirectory)
        elif(currentTest=='DELETEFILE'):
            testDeleteFile(uploadFileName=args.upload)
        elif (currentTest == 'GETBYFILENAME'):
            testGetUpload(uploadFileName=args.upload)
        else:
            print('No test was specified(currentTest=' + currentTest + '), nothing to do.')


        #testSchemaValidation(xmlFileName=xmlFilename, schemaFileName=schemaFileName)
        #testMiringValidation()
        #testNmdpValidation()
        #testSetValidationResults()
        pass

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise