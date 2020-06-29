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
        return 'In data column ' + str(columnName) + ' I could not find an uploaded file with the name (' + str(query) + '); '
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
            resultsText = resultsText[0:len(resultsText) - 2] + '; '
            return resultsText

def validateBoolean(query=None, columnName='?'):
    queryText=str(query).lower()
    # Try to be flexible on this one.
    if queryText in ['y','n','true','false','1','0', '1.0','0.0']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Yes/No Boolean value.; ')

def validateMaleFemale(query=None, columnName='?'):
    # Expecting a binary sex, either M or F.
    # For data standards reasons, not for any political or gender identity reasons.
    # TODO: Make this method more flexible, allow non-binary gender identities.
    queryText = str(query).lower()
    if queryText in ['m', 'f', 'male', 'female']:
        return ''
    else:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Male/Female value.; ')

def validateNumber(query=None, columnName='?'):
    try:
        convertedNumber = float(query)
        return ''
    except Exception:
        return ('In data column ' + str(columnName) + ' the text (' + str(query) + ') does not look like a Number.; ')

