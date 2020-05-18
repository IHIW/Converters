def validateUniqueEntryInList(query=None, searchList=None, allowPartialMatch=True, columnName='?'):
    # Return an empty string if there is a single file found.
    # Or else return text describing the problem.
    matchList = []
    for searchTerm in searchList:
        # Might be a partial sequence match
        if( (query == searchTerm) or (allowPartialMatch and query in searchTerm)):
            matchList.append(searchTerm)

    if(len(matchList) == 1):
        # Perfect. only a single file was found.
        return ''
    elif(len(matchList) == 0):
        return 'In data column ' + str(columnName) + ' I Could not find an uploaded file with the name (' + str(query) + ')\n'
    else:
        resultsText = 'In data column ' + str(columnName) + ' For file entry (' + str(query) + '), ' + str(len(matchList)) + ' matching files were found:('
        for match in matchList:
            resultsText += match + ') , ('
        resultsText = resultsText[0:len(resultsText) - 2] + '\n'
        return resultsText

def validateBoolean(query=None, columnName='?'):
    # Try to be flexible on this one.
    queryText=str(query).lower()
    if queryText in ['y','n','true','false']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Yes/No Boolean value.\n')

def validateMaleFemale(query=None, columnName='?'):
    # Expecting a binary sex, either M or F.
    # For data standards reasons, not for any political or gender identity reasons.
    # TODO: Make this method more flexible, allow non-binary gender identities.
    queryText = str(query).lower()
    if queryText in ['m', 'f', 'male', 'female']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Male/Female value.\n')


def validateNumber(query=None, columnName='?'):
    try:
        convertedNumber = float(query)
        return ''
    except Exception:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Number.\n')

