from io import StringIO
import sys

# pip install git+https://github.com/nmdp-bioinformatics/pyglstring
from glstring import check

def validateUniqueEntryInList(query=None, searchList=None, allowPartialMatch=True, columnName='?'):
    # Return an empty string if there is a single file found.
    # Or else return text describing the problem.

    # Sometimes there is extra whitespace in the excel entries.
    query = query.strip()
    matchList = []
    for searchTerm in searchList:
        #print('Checking (' + query + '),(' + searchTerm + ')')
        if(query == searchTerm):
            #print('Match (' + query + '),(' + searchTerm + ')')
            matchList.append(searchTerm)
        elif(allowPartialMatch and query in searchTerm):
            # Partial match are usually good enough. This will catch files that have been changed by the management website.
            #print('Partial Match (' + query + '),(' + searchTerm + ')')
            matchList.append(searchTerm)
        else:
            # no match.
            pass

    if(len(matchList) == 1):
        # Perfect. only a single file was found.
        return ''
    elif(len(matchList) == 0):
        return 'In data column ' + str(columnName) + ' I could not find an uploaded file with the name (' + str(query) + ')'
    else:
        # We will sometimes find 2 entries for a single file. This is the case for converted HAML files.
        # They are called "ABCD.csv" and "ABCD.csv.haml"
        # We should allow this.
        if(len(matchList) == 2 and (matchList[0] in matchList[1] or matchList[1] in matchList[0])):
            print('In data column ' + str(columnName) + ' For file entry (' + str(query) + '), '
                + str(len(matchList)) + ' matching files were found, and they appear to be the same converted file:('
                + str(matchList[0] + '),(' + matchList[1]) + ')')
            return ''

        else:
            resultsText = 'In data column ' + str(columnName) + ' For file entry (' + str(query) + '), ' + str(len(matchList)) + ' matching files were found:('
            for match in matchList:
                resultsText += match + ') , ('
            resultsText = resultsText[0:len(resultsText) - 2] + ''
            return resultsText

def validateBoolean(query=None, columnName='?'):
    queryText=str(query).lower()
    # Try to be flexible on this one.
    if queryText in ['y','n','true','false','1','0', '1.0','0.0']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Yes/No Boolean value.')

def validateMaleFemale(query=None, columnName='?'):
    # Expecting a binary sex, either M or F.
    # For data standards reasons, not for any political or gender identity reasons.
    # TODO: Make this method more flexible, allow non-binary gender identities.
    queryText = str(query).lower()
    if queryText in ['m', 'f', 'male', 'female']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Male/Female value.')

def validateNumber(query=None, columnName='?'):
    try:
        convertedNumber = float(query)
        return ''
    except Exception:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Number.')

def validateHlaGenotypeEntry(query=None, searchList=None, allowPartialMatch=None, columnName=None, uploadList=None):
    # For these projects, and HLA Genotype can be one of 3 things
    # 1) A filename of an HML file.
    # 2) A HML ID.
    # 3) A GL String
    print('Checking this HLA Genotype:' + str(query))

    # Is it a filename? These will be HML files, with extension XML or HML.
    if (str(query).lower().endswith('.xml') or str(query).lower().endswith('.hml')):
        print(str(query) + ' looks like a file name.')
        listValidationResult=validateUniqueEntryInList(query=query, searchList=searchList, allowPartialMatch=allowPartialMatch, columnName=columnName)
        print('list validation results:' + str(listValidationResult))
        return listValidationResult
    # Otherwise, is it in our HML-ID list?
    print('Checking HML ID.')
    hmlIdList = getHmlIDsListFromUploads(uploadList=uploadList)
    if(query in hmlIdList):
        print(str(query) + ' is in the HML ID list! Next, check if it is unique.')
        hmlIdValidationResults=validateUniqueEntryInList(query=query, searchList=hmlIdList, allowPartialMatch=False, columnName=columnName)
        print('hml validation results:' + str(hmlIdValidationResults))
        return hmlIdValidationResults

    # If not, validate GL String.
    print('Checking if this is a sane glstring:' + str(query))
    glStringValidationResults = validateGlString(glString=query)
    print('glstring validation results:' + str(glStringValidationResults))
    return glStringValidationResults



    # Does it match a filename on our list?


    #if(listValidationResult == ''):
    # list validation will return empty string if it's valid, return it.

    # Then we're done.
    # Does it match one of our HMLIDs?
        # Then we're done.
    # Check a GL String
        # Return results.

    return 'NOT SURE THE RESULTS HERE!'



def getHmlIDsListFromUploads(uploadList=None):
    # TODO: Implement this. Get each upload
    # Only wanna do this once, check if it's "None" first.
    return []



def createFileListFromUploads(uploads=None):
    fileNameList = []
    for upload in uploads:
        #print('upload:' + str(upload))
        fileName =upload['fileName']
        fileType = upload['type']
        #print('uploadFileName=' + fileName)
        #if(fileType=='HAML'):
        #    # TODO: Shouldn't need to do this if the upload entry has been created for the converted .haml file
        #    fileNameList.append(fileName + '.haml')
        #else:
        #    fileNameList.append(fileName)
        fileNameList.append(fileName)

    return fileNameList

def validateGlString(glString=None):
    print('validating Gl String:' + str(glString))
    with Capturing() as output:
        # TODO: This is not working. I need to borrow the main method logic from the GL String modulet

        check.main()
    output=list(output)

    validationResults=''
    for validationLineIndex in range(0,len(output)):
        glStringValidationLine=output[validationLineIndex]

        #print('GLSTRING****' + str(glStringValidationLine))
        if ('WARNING' in glStringValidationLine.upper()):
            print('I DETECTED A Warning!')
            validationResults += (glStringValidationLine) + '\n'


    if(len(validationResults) == 0):
        return validationResults
    else:
        return 'GLString (' + str(glString) + ') had these validation problem:\n' + validationResults

# Borrowed code to capture standard out
# https://stackoverflow.com/questions/16571150/how-to-capture-stdout-output-from-a-python-function-call
class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = StringIO()
        return self
    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio    # free up some memory
        sys.stdout = self._stdout