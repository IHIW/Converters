from io import StringIO
import sys
import datetime

# pip install git+https://github.com/nmdp-bioinformatics/pyglstring
# pyglstring is a repository of sanity checks written by Bob Milius at NMDP/CIBMTR. Handy.
try:
    from glstring import check
except Exception as e:
    print('Warning, package glstring is not available.')

# TODO: Many of these methods can be simplified/refactored. Make a method to check if something is an element in a list
# TODO: Add the "required" flag to many of these methods.

def validateUniqueEntryInList(query=None, searchList=None, allowPartialMatch=True, columnName='?', delimiter=None, required=True):
    # Return an empty string if there is a single file found.
    # Or else return text describing the problem.
    query = str(query).strip()
    validationText = ''

    if(len(query)<1):
        if(not required):
            return ''
        else:
            return 'No data provided for column ' + str(columnName)

    # Sometimes the query is a list separated by commas or something.
    if delimiter is None:
        queryList = [query]
    else:
        queryList = query.split(delimiter)

    # This loop is iterating for multiple query texts,  separated by a comma
    for queryText in queryList:
        matchList = []
        queryText = str(queryText).strip()

        # This loop iterates the existing files, to see if the query matches them.
        for searchTerm in searchList:
            #print('Checking (' + queryText + '),(' + searchTerm + ')')
            if(queryText == searchTerm):
                #print('Match (' + queryText + '),(' + searchTerm + ')')
                matchList.append(searchTerm)
            elif(allowPartialMatch and queryText in searchTerm):
                # Partial match are usually good enough. This will catch files that have been changed by the management website.
                #print('Partial Match (' + queryText + '),(' + searchTerm + ')')
                matchList.append(searchTerm)
            else:
                # no match.
                pass

        if(len(matchList) == 1):
            # Perfect. only a single file was found.
            pass
        elif(len(matchList) == 0):
            validationText = validationText + 'In data column ' + str(columnName) + ' I could not find an uploaded file with the name (' + str(queryText) + ')\n'
        else:
            # We will sometimes find 2 entries for a single file. This is the case for converted HAML files.
            # They are called "ABCD.csv" and "ABCD.csv.haml"
            # We should allow this.
            # TODO: These uploads have a parent/child relationship. I should be checking this instead of by the text filename.
            # TODO: This no longer works with the new filename relationship, need to prioritize checking by parent/child.
            # TODO: I'm not sure if necessary, since I'm only really looking at the HAML files in the validator.
            if(len(matchList) == 2 and (matchList[0] in matchList[1] or matchList[1] in matchList[0])):
                print('In data column ' + str(columnName) + ' For file entry (' + str(queryText) + '), '
                    + str(len(matchList)) + ' matching files were found, and they appear to be the same converted file:('
                    + str(matchList[0] + '),(' + matchList[1]) + ')')
                pass

            else:
                resultsText = 'In data column ' + str(columnName) + ' For file entry (' + str(queryText) + '), ' + str(len(matchList)) + ' matching files were found:('
                for match in matchList:
                    resultsText += match + ') , ('
                resultsText = resultsText[0:len(resultsText) - 2] + ''
                validationText = validationText + resultsText + '\n'
    return validationText

def validateTextExists(query=None, columnName='?'):
    if(query is None or len(query) < 1):
        return 'No data provided for column ' + str(columnName)
    else:
        return ''

def validateBoolean(query=None, columnName='?', required=True):
    queryText=str(query).lower().strip()

    if(not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''
    # Try to be flexible on this one.
    if queryText in ['y','n','true','false','1','0', '1.0','0.0', 'unknown']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Yes/No Boolean value.')

def validateDate(query=None, columnName='?', dateFormat='%Y-%m-%d', required=True):
    queryText = str(query).lower().strip()
    if(not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    try:
        dateObject = datetime.datetime.strptime(query, dateFormat)
    except Exception as e:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not match the expected date format (' + str(dateFormat) + ')')
    return ''

def validateBloodGroup(query=None, columnName='?', required=True):
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    # Easiest to just list the blood types, there aren't very many.
    # Potential problem: these won't look right: ("A positive", "Type A", Apos)
    validBloodGroups = ['A','B','O','AB', 'UNKNOWN']
    if(str(query).upper() in validBloodGroups):
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not seem to be a valid blood type.')

def validateRejectionType(query=None, columnName='?', required=True):
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    validRejectionTypes = ['ANTIBODY MEDIATED (ABMR)','CELLULAR','MIXED','OTHER / UNKNOWN']
    if(str(query).upper() in validRejectionTypes):
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not seem to be a valid rejection type.')

def validateDiseaseAetiology(query=None, columnName='?', required=True):
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    validDiseaseAetiologies = ['IMMUNE','NON-IMMUNE','UNKNOWN']
    if(str(query).upper() in validDiseaseAetiologies):
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not seem to be a valid disease aetiology.')


def validateDonorSourceType(query=None, columnName='?', required=True):
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    validDonorSourceTypes = ['DCD', 'DBD', 'LIVINGDIRECTED', 'LIVINGUNRELATED', 'LIVINGRELATED', 'LIVINGUNKNOWN', 'PKE','OTHER']
    if(str(query).upper().replace(' ','').replace('(','').replace(')','') in validDonorSourceTypes):
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not seem to be a valid donor source type.')

def validateProzoneType(query=None, columnName='?'):
    validProzoneTypes = ['EDTA', 'DTT', 'DILUTION', 'HEAT', 'OTHER']
    if(str(query).upper() in validProzoneTypes):
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not seem to be a valid prozone type.')

def validateOrganCategory(query=None, columnName='?', required=True):
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    validOrganCategories = ['KIDNEY', 'HEART', 'LUNG', 'PANCREAS', 'KPD', 'LIVER', 'OTHER']
    if(str(query).upper() in validOrganCategories):
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not seem to be a valid organ type.')

def validateOrganStatus(query=None, columnName='?', required=True):
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''
    validOrganCategories = ['STABLE GRAFT FUNCTION', 'REJECTION','GRAFT LOSS','UNKNOWN']
    if(str(query).upper() in validOrganCategories):
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not seem to be a valid organ status.')

def validateMaleFemale(query=None, columnName='?', required=True):
    # Expecting a binary sex, either M or F.
    # We're evaluating chromosomes, not making statements about valid genders.
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    if queryText in ['m', 'f', 'male', 'female', 'unknown']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Male/Female value.')

def validateNumber(query=None, columnName='?', required=True):
    queryText = str(query).lower().strip()
    if (not required and queryText in ['','unknown','na','n/a','(n/a)']):
        return ''

    try:
        convertedNumber = float(query)
        return ''
    except Exception:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Number.')

def validateHlaGenotypeEntry(query=None, searchList=None, allowPartialMatch=None, columnName=None, uploadList=None):
    # For these projects, and HLA Genotype can be one of 3 things
    # 1) A filename of an HML file.
    # 2) A HML ID. (TODO:Implement checking lists of HML ids for a single entry.)
    # 3) A GL String
    #print('Checking this HLA Genotype:' + str(query))

    # If we find a single file entry, we are done. Not filtering by file extension, because user may have submitted just the file ID without extension.
    listValidationResult=validateUniqueEntryInList(query=query, searchList=searchList, allowPartialMatch=allowPartialMatch, columnName=columnName, delimiter=',')
    if(listValidationResult==''):
        # This entry maps to an individual file. Done.
        return listValidationResult
    else:
        pass
        #print(str(query) + ' did not map to a single file, results:' + str(listValidationResult))

    # TODO: Implement the list of HML IDs.
    hmlIdValidationResults = 'Could not find file with matching HML ID'

    # I could not find matching File or HMLID, so let's validate GL String.
    #print('Checking if this is a sane glstring:' + str(query))
    glStringValidationResults = validateGlString(glString=query)
    #glStringValidationResults = '' # Temporary results from glstring validator, because it does not work yet

    #print('glstring validation results:' + str(glStringValidationResults))
    if(glStringValidationResults==''):
        # No issues detected with GL String, it looks valid enough..
        return glStringValidationResults


    combinedValidationResults = listValidationResult + '\n' + hmlIdValidationResults + '\n' + glStringValidationResults
    return combinedValidationResults

def getHmlIDsListFromUploads(uploadList=None):
    # TODO: Implement this. Get each upload
    # Only wanna do this once, check if it's "None" first.
    return []

def createFileListFromUploads(uploads=None, fileTypeFilter=None,  projectFilter=None):
    # TODO: also optionally filter based on files submitted by lab members
    if not isinstance(projectFilter, list):
        projectFilter = [projectFilter]
    fileNameList = []
    for upload in uploads:
        #print('upload:' + str(upload))
        fileName =upload['fileName']
        fileType = upload['type']
        fileProject = str(upload['project']['id'])

        if((fileTypeFilter is None or fileType==fileTypeFilter)
            and (projectFilter is None or fileProject in projectFilter)):
            fileNameList.append(fileName)

    #print('Uploads of file type ' + str(fileTypeFilter) + ':' + str(fileNameList))

    return fileNameList

def validateGlStrings(glStrings=None):
    # Validate GL Strings individually.
    if(glStrings is None):
        return False, 'GL Strings were None, some error has apparently occurred in validation'
    elif(len(glStrings) == 0):
        return (True, 'No GL Strings were found.')
    else:
        isValid = True
        validationFeedback = ''
        for glString in glStrings:
            glStringValidationResults = validateGlString(glString=glString)
            #print('GLString(' + glString + ') has these validation results (' + glStringValidationResults+ ')')
            if(len(glStringValidationResults) > 0):
                isValid = False
                if(len(validationFeedback)>0):
                    validationFeedback += ', '
                validationFeedback += glStringValidationResults

        if(isValid and len(validationFeedback)==0):
            validationFeedback = 'Valid GLStrings'

        return isValid, validationFeedback

def validateGlString(glString=None):
    #print('validating Gl String:' + str(glString))
    # Check if it's undefined, or not formatted like a GL String.
    if(glString is None or len(glString)<2):
        return 'GLString (' + str(glString) + ') is Not defined.'
    elif(not str(glString).startswith('HLA-')):
        return '(' + str(glString) + ') does not look like a GL String.'

    validationFeedback = ''

    #  We need the print output to detect validation errors. Capture it.
    with Capturing() as output:
        #print("Checking locus blocks...")
        locusblocks, duplicates = check.locus_blocks(glString)
        for locusblock in locusblocks:
            print(locusblock)
        if len(locusblocks) > 1:
            if len(duplicates) == 0:
                print("OK: no loci found in more than one locus block")
            else:
                if len(duplicates) == 1:
                    print("WARNING: Locus found in more than 1 locus block:", duplicates)
                else:
                    print("WARNING: Loci found in more than 1 locus block:", duplicates)
        else:
            print("Nothing to check: Only one locus block")
        print()

        check.printchecked(check.genotype_lists(glString), 'genotype lists')
        check.printchecked(check.genotypes(glString), 'genotypes')
        check.printchecked(check.allele_lists(glString), 'allele lists')

    output = list(output)
    #print('At the end of validation I found output with length ' + str(len(output)))

    for validationLineIndex in range(0,len(output)):
        glStringValidationLine=output[validationLineIndex]

        #print('GLSTRING****' + str(glStringValidationLine))
        if ('WARNING' in glStringValidationLine.upper()):
            #print('I DETECTED A Warning!')
            validationFeedback += (glStringValidationLine) + '\n'

    if(len(validationFeedback) == 0):
        return validationFeedback
    else:
        return 'GLString (' + str(glString) + ') had these validation problem:\n' + validationFeedback

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

