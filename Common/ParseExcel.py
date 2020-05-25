from xlrd import open_workbook
# We might need this in case they don't use xlsx format
#from xlrd.book import open_workbook_xls
from xlrd.sheet import ctype_text

def parseExcelFile(excelFile=None, columnNames=None):
    if(excelFile is None):
        print('No excel file was provided! I cannot parse nothing!')
        return None
    if(columnNames is None or len(columnNames) < 1):
        print('No column names were provided! I cannot parse the excel file.')
        return None

    # list->set->list will get the unique values in a list. No duplicates.
    # Convert to lowercase and sort.
    columnNames = list(set([x.lower() for x in columnNames]))
    columnNames.sort()

    print('Opening and Parsing excel file:' + str(excelFile))
    print('It is of type:' + str(type(excelFile)))
    print('column names:' + str(columnNames))

    # Store a dictionary for each excel row
    dataEntries=[]

    # Open the workbook
    #print('Opening Workbook...')
    if(type(excelFile)==str):
        xlWorkbook = open_workbook(excelFile)
    elif(type(excelFile)==bytes):
        xlWorkbook = open_workbook(file_contents=excelFile)
    else:
        print('I do not know what type of file this is:' + str(type(excelFile)))
    #print('Workbook was opened.')

    # Get the first sheet.
    sheetNames = xlWorkbook.sheet_names()
    if(len(sheetNames) > 1):
        # TODO: Handle multiple sheets. Might be necessary in the future.
        print('Warning! Multiple sheets were detected in this workbook. There should only be one sheet.')
        print('Sheet Names', sheetNames)
    xlSheet = xlWorkbook.sheet_by_name(sheetNames[0])
    print('Sheet name: %s' % xlSheet.name)

    # First row contains the headers. Make sure we have all the expected headers.
    row = xlSheet.row(0)
    # Empty List. this stores the column # in THE EXCEL FILE where the data lives.
    # Because the excel file might have data in different order for some reason.
    excelColumnIndexes=[None] * len(columnNames)

    for excelColumnIndex, cell in enumerate(row):
        cellType = ctype_text.get(cell.ctype, 'unknown type')
        if(cellType != 'text'):
            print('Warning! I expected the column header to be of type "text" but instead it is:' + cellType)

        excelColumnName = str(cell.value).lower()
        try:
            columnIndex = columnNames.index(excelColumnName)
        except ValueError:
            return ('Error when parsing input excel document. Spreadsheet has an extra column:' + str(excelColumnName))

        excelColumnIndexes[columnIndex] = excelColumnIndex
        #print('column name:' + excelColumnName)
        #print('column number in excel document:' + str(excelColumnIndex))
        #print('column number in sorted input column list:' + str(columnIndex))

    # Check that found all columns. The indexes should not be None, because they were found in the excel document.
    # TODO: What happens if excel files have multiple columns with the same name? That might not be detected by this.
    for iteratorIndex, excelColumnIndex in enumerate(excelColumnIndexes):
        if(excelColumnIndex is None):
            return ('Error when parsing input excel document. The excel file does not contain this column:' + str(columnNames[iteratorIndex]))

    print('All column headers were found in the excel file.')

    # Iterate and Store the row data.
    # Skip the first row, those are headers.
    for rowIndex in range(1, xlSheet.nrows):
        #print('Processing excel row (0-based):' + str(rowIndex))
        currentDataRow = {}

        for columnIndex in range(0, xlSheet.ncols):
            cell = xlSheet.cell(rowIndex, columnIndex)  # Get cell object by row, col
            columnName = columnNames[excelColumnIndexes.index(columnIndex)]
            cellValue = cell.value
            cellType = ctype_text.get(cell.ctype, 'unknown type')
            #print('column ' + columnName + ' has data of type ' + str(cellType) + ' and value ' + str(cellValue))
            currentDataRow[columnName] = cellValue
        dataEntries.append(currentDataRow)

    return dataEntries