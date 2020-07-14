# Writing  uses the xlsxwriter module.
# Reading uses the xlrd module.
# They're not really related to eachother, but this is how I got it to work.
from xlrd import open_workbook
from xlrd.sheet import ctype_text
import xlsxwriter
import io

def parseExcelFileWithColumns(excelFile=None, columnNames=None):
    # Parse and validate excel file against a list of expected column names.
    # Return: A list of dictionaries representing a line of data. Keys are the column headers
    # TODO: Also return the original headers so we can maintain the original order if necessary.
    # TODO: Also return some error messages. This might be a dictionary of some sort. But i want to know what
    #  line and column they are in.

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
    xlWorkbook = openWorkbook(excelFile)

    # Get the first sheet.
    sheetNames = xlWorkbook.sheet_names()
    if(len(sheetNames) > 1):
        # TODO: Handle multiple sheets. Might be necessary in the future.
        print('Warning! Multiple sheets were detected in this workbook. There should only be one sheet.')
        print('Sheet Names', sheetNames)
    xlSheet = xlWorkbook.sheet_by_name(sheetNames[0])
    print('Sheet name: %s' % xlSheet.name)

    # First row contains the headers. Make sure we have all the expected headers.
    headerRow = xlSheet.row(0)
    # Empty List. this stores the column # in THE EXCEL FILE where the data lives.
    # Because the excel file might have data in different order for some reason.
    excelColumnIndexes=[None] * len(columnNames)

    for excelColumnIndex, cell in enumerate(headerRow):
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
            print('Error when parsing input excel document. The excel file does not contain this column:' + str(columnNames[iteratorIndex]))
            # TODO: Returning None is not correct here. I'm supposed to be returning some better values than this.
            #  This happens if a column is missing. I have to put on the report that there is no value for this.
            return None

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

    return (dataEntries, headerRow)

def parseExcelFile(excelFile=None):
    # I'm determining the headers on the fly here, instead of validating against a list of expected headers.
    if(excelFile is None):
        print('No excel file was provided! I cannot parse nothing!')
        return None


    # list->set->list will get the unique values in a list. No duplicates.
    # Convert to lowercase and sort.
    #columnNames = list(set([x.lower() for x in columnNames]))
    #columnNames.sort()

    print('Opening and Parsing excel file:' + str(excelFile))
    print('It is of type:' + str(type(excelFile)))
    #print('column names:' + str(columnNames))

    # Store a dictionary for each excel row
    dataEntries=[]

    # Open the workbook
    xlWorkbook = openWorkbook(excelFile)

    # Get the first sheet.
    sheetNames = xlWorkbook.sheet_names()
    if(len(sheetNames) > 1):
        # TODO: Handle multiple sheets. Might be necessary in the future.
        print('Warning! Multiple sheets were detected in this workbook. There should only be one sheet.')
        print('Sheet Names', sheetNames)
    xlSheet = xlWorkbook.sheet_by_name(sheetNames[0])
    print('Sheet name: %s' % xlSheet.name)

    # First row contains the headers. Make sure we have all the expected headers.
    headerRow = xlSheet.row(0)
    # Empty List. this stores the column # in THE EXCEL FILE where the data lives.
    # Because the excel file might have data in different order for some reason.
    columnNames = []

    # TODO: What happens if excel files have multiple columns with the same name? That might not be detected by this.
    for excelColumnIndex, cell in enumerate(headerRow):
        cellType = ctype_text.get(cell.ctype, 'unknown type')
        if(cellType != 'text'):
            print('Warning! I expected the column header to be of type "text" but instead it is:' + cellType)
        excelColumnName = str(cell.value)
        columnNames.append(excelColumnName)

    # Iterate and Store the row data.
    # Skip the first row, those are headers.
    for rowIndex in range(1, xlSheet.nrows):
        #print('Processing excel row (0-based):' + str(rowIndex))
        currentDataRow = {}

        for columnIndex in range(0, xlSheet.ncols):
            cell = xlSheet.cell(rowIndex, columnIndex)  # Get cell object by row, col
            columnName = columnNames[columnIndex]
            cellValue = cell.value
            cellType = ctype_text.get(cell.ctype, 'unknown type')
            currentDataRow[columnName] = cellValue
        dataEntries.append(currentDataRow)

    return dataEntries

def openWorkbook(excelFile):
    # print('Opening Workbook...')
    if (type(excelFile) == str):
        xlWorkbook = open_workbook(excelFile)
    elif (type(excelFile) == bytes):
        xlWorkbook = open_workbook(file_contents=excelFile)
    else:
        print('I do not know what type of file this is:' + str(type(excelFile)))
    # print('Workbook was opened.')
    return xlWorkbook

def createBytestreamExcelOutputFile():
    # Warning: I think you still  need to call workbook.close() after you're done modifying the file. Don't know what bugs this will cause.
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    return (workbook, output)

def getColumnNumberAsString(base0ColumnNumber=None):
    # A method to get an excel letter representing the column numbers from a 0-based column index
    if(base0ColumnNumber is None or base0ColumnNumber<0):
        return '?'
    base1ColumnNumber= int(base0ColumnNumber)+1
    columnIndex = ""
    while base1ColumnNumber > 0:
        base1ColumnNumber, remainder = divmod(base1ColumnNumber - 1, 26)
        columnIndex = chr(65 + remainder) + columnIndex
    return columnIndex

def createExcelValidationReport(errors=None, inputWorkbookData=None):
    outputWorkbook, outputWorkbookbyteStream = createBytestreamExcelOutputFile()

    # TODO: Support multiple sheets. This is just a single sheet.
    outputWorksheet = outputWorkbook.add_worksheet()
    # Define Styles
    headerStyle = outputWorkbook.add_format({'bold': True})
    errorStyle = outputWorkbook.add_format({'bg_color': 'red'})
    # Write headers on new sheet.
    sheetHeaders = inputWorkbookData[0].keys()
    print('These are the headers:' + str(sheetHeaders))
    for headerIndex, header in enumerate(sheetHeaders):
        cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex) + '1'
        outputWorksheet.write(cellIndex, header, headerStyle)
    # Loop input Workbook data
    for dataLineIndex, dataLine in enumerate(inputWorkbookData):
        #print('Copying this line:' + str(dataLine))

        for headerIndex, header in enumerate(sheetHeaders):
            cellIndex = getColumnNumberAsString(base0ColumnNumber=headerIndex) + str(dataLineIndex + 2)

            # Was there an error in this cell? Highlight it red and add error message
            if (header in errors[dataLineIndex].keys() and len(str(errors[dataLineIndex][header]))>0):
                outputWorksheet.write(cellIndex, dataLine[header], errorStyle)
                outputWorksheet.write_comment(cellIndex, errors[dataLineIndex][header])
            else:
                outputWorksheet.write(cellIndex, dataLine[header])

    # Widen the columns a bit so we can read them.
    outputWorksheet.set_column('A:' + getColumnNumberAsString(len(sheetHeaders) - 1), 30)
    # Freeze the header row.
    outputWorksheet.freeze_panes(1, 0)
    outputWorkbook.close()

    return (outputWorkbook, outputWorkbookbyteStream)
