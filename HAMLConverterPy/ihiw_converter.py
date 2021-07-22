import argparse
import os,sys
import xml.etree.ElementTree as ET #using System.Xml;
import xml.etree
from lxml import etree
import pandas as pd
import datetime
import boto3
import io
import csv
import copy

####################
# CONVERTER CLASS
####################
''' <summary>
    /// Script was converted to Python by Teresa Tavella
    /// University of Bologna
    /// https://github.com/TessaTi/IHIW_Converter_py
    
    /// Determines the manufacturer of the input file.
    /// The manufacturer can be Immucor or OneLambda.
    /// Immucor provides a file delimited with ",".
    /// OneLambda provides a file delimited with ";".
    /// In order to determine the manufacturer all columns must be present.
    /// If no manufacturer can be determined the manufacturer string will be empty.
    ///<summary>
 '''

class Converter(object):

    def __init__(self, csvFileName=None, manufacturer=None, xmlFile=None):
        self.csvFileName = csvFileName
        self.manufacturer = manufacturer
        self.allFieldsQuoted = None
        self.xmlFile = xmlFile
        self.xmlText = None
        self.xmlData = None
        # There are localization settings in the output files.
        # Different files are delimited by commas and semicolons. Different files use . or , as a decimal.
        # This needs to be accounted for.
        self.delimiter = None
        #self.decimal = None
        self.dateFormat = '%d-%m-%Y'
        self.validationFeedback=''

    def formatRunDate(self, RunDate=None):
        # format the date to the correct haml (ISO) style.
        # Parse the date
        try:
            dateObject = datetime.datetime.strptime(RunDate, self.dateFormat)
            formattedRunDate = dateObject.strftime("%Y-%m-%d")
            return formattedRunDate
        except Exception as e:
            print('Could not format the date properly:' + str(e))
            self.DetermineDateFormat(RunDate)
            if (self.dateFormat is not None):
                dateObject = datetime.datetime.strptime(RunDate, self.dateFormat)
                formattedRunDate = dateObject.strftime("%Y-%m-%d")
                return formattedRunDate
            else:
                print('Cannot interpret date format! ' + RunDate)
                return None

    def DetermineDateFormat(self, dateString=None):
        print('Determining Date format of this string:' + dateString)
        self.dateFormat = None
        # TODO: Is there a more flexible way to do this? This breaks regularly with new date formats.
        # TODO: Warning: It's very easy to mis-interpret days and months here.
        # TODO: We can try to parse the whole document....to find a date > 12
        potentialDateFormats=['%d-%m-%Y', '%Y-%m-%d', '%d-%b-%Y','%m/%d/%Y','%d.%m.%Y','%d. %m. %Y']
        for dateFormat in potentialDateFormats:
            try:
                dateObject = datetime.datetime.strptime(dateString, dateFormat)
                print('I believe that ' + dateString + ' is indeed this format:' + str(dateFormat))
                self.dateFormat=dateFormat
            except Exception as e:
                pass
                #print(dateString + ' is not this format:' + str(dateFormat))
        if(self.dateFormat is None):
            print('Failed at determining date format! ')
            raise Exception('Could not determine Date Format of this string:' + str(dateString))

    def determineFormatAndManufacturer(self):
        print('Determining File Format and Manufacturer')

        # Possible delimiters
        tryDelimiters=[',',';','\t']
        for delimiter in tryDelimiters:
            if (self.delimiter is None):

                # Pandas CSV reader likes to specify the quoting behavior. Sometimes in CSV files all the columns are quoted, sometimes they aren't.
                # Lets check both cases.
                for checkAllFieldsQuoted in [True, False]:
                    try:
                        print('Checking if this file has a (' + str(delimiter) + ') delimiter,  checkAllFieldsQuoted=' + str(checkAllFieldsQuoted))
                        pandasCsvReader = readCsvFile(csvFileName=self.csvFileName, delimiter=delimiter, allFieldsQuoted=checkAllFieldsQuoted)
                        self.determineManufacturer(pandasCsvReader=pandasCsvReader)
                        print('Manufacturer:' + str(self.manufacturer))
                        if(self.manufacturer is not None):
                            # That worked! Remember these settings
                            self.delimiter=delimiter
                            self.allFieldsQuoted=checkAllFieldsQuoted
                            break
                    except Exception as e:
                        print('Exception when reading Csv File (delimiter=' + str(delimiter) + ' allFieldsQuoted=' + str(checkAllFieldsQuoted) + '):' + str(e))

    def determineManufacturer(self, pandasCsvReader=None):
        colOneLambda = ['PatientID', 'SampleIDName', 'RunDate', 'CatalogID', 'BeadID', 'Specificity', 'RawData','NC1BeadID','PC1BeadID', 'NC2BeadID','PC2BeadID', 'Rxn']
        colImmucor = ['Sample ID', 'Patient ID', 'Lot ID', 'Run Date', 'Allele', 'Assignment', 'Raw Value']

        if(self.manufacturer is None):

            # Get the columns from the csvReader:
            # These replaces are to get rid of space characters.
            # The \ufeff" character seems to indicate the encoding of the file.
            # The proper solution is to switch the codec the file is decoded in, but instead I'm doing a replace, because it's easier.
            colnames = [str(c.strip('"').strip().replace(' ', '_').replace('\ufeff"','')) for c in pandasCsvReader.columns.tolist()]
            print('I found these columns (N='+ str(len(colnames)) + ') :' + str(colnames))

            # Check if there is an intersection of the sets. Overlapping is good.
            # Does this work? think this will break if there are any overlapping column names. But there arent!
            if (set(colnames) & set(colImmucor)):
                self.manufacturer = 'Immucor'
                print('This is an Immucor File.')
            elif (set(colnames) & set(colOneLambda)):
                self.manufacturer = 'OneLambda'
                print('This is a One Lambda File.')
            else:
                print('Cannot determine manufacturer based on those column names.')

    #########
    # Get bead value
    #########
    def GetBeadValue(self,NC2BeadID=None, BeadID=None, SampleIDName=None, SampleID=None,RawData=None):
        if BeadID == NC2BeadID and SampleIDName == SampleID:
            # Some localizations allow a comma in these as a decimal format. Just make it a period.
            BeadValue = str(RawData).replace(',','.')
        else:
            BeadValue = 0
        return BeadValue

    #########
    # Prettify xml
    ######### 
    def prettyPrintXml(self):
        # Generate xml text
        xmlText = self.xmlData.decode()
        self.xmlText = xmlText

        if(self.xmlText is not None and len(self.xmlText) > 0):
            #print('***xml Text:\n' + str(self.xmlText))
            rootElement = etree.fromstring(self.xmlText)
            prettyPrintText=etree.tostring(rootElement, pretty_print=True).decode()
            if(prettyPrintText is not None and len(prettyPrintText) > 0):
                self.xmlText = prettyPrintText

            if (self.xmlFile is not None):
                elementTree = etree.ElementTree(rootElement)
                elementTree.write(self.xmlFile, pretty_print=True, encoding='utf-8')
            else:
                print('Not writing xml text to file, because None was provided for xmlFile parameter')


    #################
    # Parse OneLambda
    #################
    def ProcessOneLambda(self, pandasCsvReader=None):
        #print('OneLambda to xml...',OLReader.head())
        print('OneLambda to xml...')
        # TODO return validation feedback.
        validationFeedback = ''

        try:

            col_OneLambda = {'PatientID':-1, 'SampleIDName':-1, 'RunDate':-1, 'CatalogID':-1,'BeadID':-1, 'Specificity':-1, 'RawData':-1, 'NC2BeadID':-1,'PC2BeadID':-1, 'Rxn':-1}

            # Determine where the columns are, position
            colnames = [c.strip('"') for c in pandasCsvReader.columns.tolist()] #list colnames file
            for c in range(0,len(colnames)):
                name = colnames[c]
                col_OneLambda[name] =  c

            # Data is the root element.
            data = ET.Element("haml",xmlns='urn:HAML.Namespace')
            # OLReader is a pandas DataFrame.
            # Each row is a namedtuple
            # The first row contains the negative control info.
            # The second row contains positive control info.

            # State variable to iterate through. States cycle through negative_control->positive_control->bead_values
            readerState = 'negative_control'
            negativeControlRow=None
            positiveControlRow=None
            patientID='!!!'
            sampleID = '!!!'
            catalogID = ''

            #rowlength = OLReader.shape[0]
            for line, row in enumerate(pandasCsvReader.itertuples(), 1):
                if(readerState=='negative_control'):
                    negativeControlRow = row
                    readerState='positive_control'
                elif(readerState=='positive_control'):
                    positiveControlRow = row
                    readerState = 'bead_values'

                    currentRowSampleIDName=str(row.SampleIDName).strip()
                    currentRowPatientID=str(row.PatientID).strip()

                    # In one case the user submitted data that was missing sampleIDs. This shouldn't be accepted.
                    #print('delimiter =(' + self.delimiter + ')')
                    #print('sampleIDName= ' + str(row.SampleIDName))
                    if(currentRowSampleIDName is None or len(currentRowSampleIDName) == 0 or currentRowSampleIDName=='nan'):
                        # row.SampleIDName='?'
                        currentRowSampleIDName = '?'
                        feedbackText = 'Empty SampleIDName found, please provide SampleIDName in every row.'
                        # Only report this once.
                        if(feedbackText not in validationFeedback):
                            validationFeedback += feedbackText + ' Row=' + str(row.Index) + ';\n'

                    if (currentRowPatientID is None or len(currentRowPatientID) == 0 or currentRowPatientID=='nan'):
                        currentRowPatientID = '?'
                        feedbackText = 'Empty PatientID found, please provide PatientID in every row.'
                        # Only report this once.
                        if (feedbackText not in validationFeedback):
                            validationFeedback += feedbackText + ' Row=' + str(row.Index) + ';\n'


                    # If the patientID or sampleIDhave changed, this is a new patient-antibody-assessment.
                    # TODO: Consider writing each sample to an individual HAML file. This would need to create child elements for each HAML.
                    if (currentRowSampleIDName != sampleID or currentRowPatientID != patientID):
                        sampleID = currentRowSampleIDName
                        patientID = currentRowPatientID
                        #print('Converting a new sampleID:' + str(sampleID) + ' and patientID:' + str(
                        #    patientID) + ' and catalogID:' + str(catalogID))

                        # For each new patient, we need to add the patient-antibody-assessment and solid-phase-panel nodes
                        patientAntibodyAssmtElement = ET.SubElement(data, 'patient-antibody-assessment',
                            {'sampleID': str(sampleID),
                             'patientID': str(patientID),
                             'reporting-centerID': 'ReportingCenterID',
                             # TODO No reporting center in the input file. Should we pass that in somehow?
                             'sample-test-date': self.formatRunDate(row.RunDate),
                             'negative-control-MFI': str(int(round(float(str(negativeControlRow.RawData).replace(',', '.'))))),
                             'positive-control-MFI': str(int(round(float(str(positiveControlRow.RawData).replace(',', '.')))))
                             # Problem: I dont have these data yet. I should print this after assigning positive and negative rows.
                             })
                    # If the catalogID has changed, this is a new solid-phase-panel. But we also need this for any new sampleID or patientID
                    if (str(row.SampleIDName).strip() != sampleID or str(row.PatientID).strip() != patientID or str(row.CatalogID).strip() != catalogID):
                        catalogID = str(row.CatalogID).strip()
                        #print('Found a new bead catalog: ' + str(catalogID))

                        current_row_panel = ET.SubElement(patientAntibodyAssmtElement, 'solid-phase-panel',
                              {'kit-manufacturer': self.manufacturer,
                               'lot': catalogID
                               })

                elif(readerState=='bead_values'):
                    if row.PatientID is None:
                        # If we get here then there actually might be a problem.
                        print('Reached the end of the input csv, breaking the loop. This means there was a newline at the end of the .csv, possibly malformed data.')
                        break

                    else:
                        # TODO: Are they going to be delimited by something other than commas? Is that possible?
                        Specs = row.Specificity.split(",")
                        Raw = int(round(float(str(row.RawData).replace(',','.'))))
                        # TODO: We're not assigning the ranking correctly.
                        #  A better strategy is to load all the MFIs and give them a ranking. Before writing the values. Add this logic.
                        #Ranking=0
                        Ranking = str(int(row.Rxn))

                        # What locus is this data row for?
                        locusDataRow=''
                        for currentLocus in Specs:
                            if(currentLocus != '-'):
                                if(locusDataRow==''):
                                    # The only (or first) locus encountered.
                                    locusDataRow=currentLocus
                                else:
                                    # The second locus encountered for the heterodimer.
                                    locusDataRow=locusDataRow+ '~' + currentLocus
                            else:
                                pass

                        current_row_panel_bead = ET.SubElement(current_row_panel,'bead',
                            {'HLA-allele-specificity':str(locusDataRow),
                                'raw-MFI':str(Raw),
                                'Ranking':str(Ranking),
                            })


            # create a new XML file with the results
            self.xmlData = ET.tostring(data)
            self.prettyPrintXml()
        except Exception as e:
            validationFeedback+= 'Exception when reading file:' + str(e) + ';\n'
        return validationFeedback

    ########
    # Parse Immucor
    ########
    def ProcessImmucor(self, pandasCsvReader=None, reportingCenterID='?'):
        print('Immucor to xml...')
        # TODO: Do I add validation feedback anywhere?
        validationFeedback=''

        # TODO: These rankings are assigned based on whether the bead is positive. Is 8/6/2 arbitrary? I do not know where that came from.
        switcher = {'Positive':8, 'Weak':6, 'Negative':2}
        immucorColumnNames = {'Sample ID':-1, 'Patient ID':-1, 'Lot ID':-1, 'Run Date':-1, 'Allele':-1, 'Assignment':-1, 'Raw Value':-1}
        #// Determine where the columns are
        colnames = pandasCsvReader.columns.tolist()
        for c in range(0,len(colnames)): 
            name = colnames[c]
            immucorColumnNames[name] = c

        # Parse Data
        # Structure = csvData[sampleID][patientID][runDate][lotID][allele] = (assignment, rawMFI)
        csvData = {}

        for row in pandasCsvReader.itertuples():
            # If the patientID or sampleID have changed, this is a new patient-antibody-assessment.
            if(not hasattr(row,'Sample_ID')):
                validationFeedback += ('Sample_ID was Missing!;\n')
                sampleID = '??'
            else:
                sampleID = str(row.Sample_ID).strip()
            if(not hasattr(row,'Patient_ID')):
                validationFeedback += ('Patient_ID was not found!;\n')
                patientID = '??'
            else:
                patientID = str(row.Patient_ID).strip()

            if (not hasattr(row, 'Run_Date')):
                validationFeedback += ('Run_Date was not found!;\n')
                sampleTestDate = '01/01/1900'
            else:
                sampleTestDate = str(row.Run_Date).strip()

            if (hasattr(row, 'Lot_ID')):
                lotID = str(row.Lot_ID).strip()
            elif (hasattr(row, 'LotID')):
                lotID = str(row.LotID).strip()
            else:
                validationFeedback += ('Lot_ID was not found!;\n')
                lotID = '??'

            allele = str(row.Allele).strip()

            if (hasattr(row, 'Assignment')):
                assignment = str(row.Assignment).strip()
            else:
                validationFeedback += ('Assignment was not found!;\n')
                assignment = '??'

            rawMfi = str(row.Raw_Value).strip()
            try:
                beadID = str(row.Bead_ID).strip()
            except Exception as e:
                beadID = None

            print('Stored Bead ID ' + str(beadID))

            # Initiate some data structure
            if sampleID not in csvData:
                csvData[sampleID]={}
            if patientID not in csvData[sampleID]:
                csvData[sampleID][patientID]={}
            if sampleTestDate not in csvData[sampleID][patientID]:
                csvData[sampleID][patientID][sampleTestDate]={}
            if lotID not in csvData[sampleID][patientID][sampleTestDate]:
                csvData[sampleID][patientID][sampleTestDate][lotID]={}

            # In the case of heterodimers, we must pair alleles.
            if(allele.startswith('DPA1') or allele.startswith('DPB1') or allele.startswith('DQA1') or allele.startswith('DQB1')):
                #print ('Heterodimer allele:' + str(allele))

                unpairedAlleles = [alleleName for alleleName in csvData[sampleID][patientID][sampleTestDate][lotID] if '_UNPAIRED' in alleleName]
                #print('UNPAIRED alleles:' + str(unpairedAlleles))

                # TODO: Could modify this to check all unpaired alleles instead of just the first...
                if(len(unpairedAlleles)==0):
                    # This is the first of a pair. Hopefully.
                    csvData[sampleID][patientID][sampleTestDate][lotID][allele+'_UNPAIRED'] = (beadID, assignment, rawMfi)
                elif(len(unpairedAlleles)==1):
                    # This entry should pair with previous unpaired allele. Double check beadId, MFI and assignment to be sure.
                    if(csvData[sampleID][patientID][sampleTestDate][lotID][unpairedAlleles[0]] ==  (beadID, assignment, rawMfi) ):
                        # print('MATCH!' + str(unpairedAlleles[0]) + ' : ' + str(allele))
                        # Remove the unpaired allele and store the paired one.
                        csvData[sampleID][patientID][sampleTestDate][lotID].pop(unpairedAlleles[0])
                        csvData[sampleID][patientID][sampleTestDate][lotID][unpairedAlleles[0].replace('_UNPAIRED','~') + allele] = (beadID, assignment, rawMfi)

                    else:
                        validationFeedback += ('Trouble when matching heterodimer alleles, these do not match!:'+ str(unpairedAlleles[0]) + ' : ' + str(allele)  + ';\n')
                        #raise Exception('These alleles are unmatched!:'+ str(unpairedAlleles[0]) + ' : ' + str(allele) )
                else:
                    pass
                    validationFeedback += ('Trouble when matching heterodimer alleles, multiple unmatched alleles found!:'+ str(unpairedAlleles) + ';\n')
            else:
                # These beads do not represent heterodimers. Store normally.
                csvData[sampleID][patientID][sampleTestDate][lotID][allele] = (beadID, assignment, rawMfi)

        # Write XML from that data.
        # TODO: Consider writing each sample to an individual HAML file. This would need to create child elements for each HAML.
        # for each sample id/row start converting
        data = ET.Element("haml", xmlns='urn:HAML.Namespace')
        # Structure = csvData[sampleID][patientID][runDate][lotID][allele] = (assignment, rawMFI)

        # Each sampleID/patientID combination gets a patient-antibody-assessment element
        for sampleID in csvData:
            for patientID in csvData[sampleID]:
                for runDate in csvData[sampleID][patientID]:

                    # Get the PC and NC MFIs
                    # TODO: there may be an edge-case bug here. If there are multiple lot IDs we might have multiple postive and negative control MFIs, may be hidden
                    for lotID in csvData[sampleID][patientID][runDate]:
                        if('NC' in csvData[sampleID][patientID][runDate][lotID]):
                            ncMfi = csvData[sampleID][patientID][runDate][lotID]['NC'][1]
                        else:
                            ncMfi = '-1'
                            validationFeedback += 'Missing negative control for lot ' + str(lotID) + ';\n'
                        if('PC' in csvData[sampleID][patientID][runDate][lotID]):
                            pcMfi = csvData[sampleID][patientID][runDate][lotID]['PC'][1]
                        else:
                            pcMfi = '-1'
                            validationFeedback += 'Missing postive control for lot ' + str(lotID) + ';\n'

                    patientAntibodyAssmtElement = ET.SubElement(data, 'patient-antibody-assessment',
                        {'sampleID': str(sampleID),
                         'patientID': str(patientID),
                         'reporting-centerID': str(reportingCenterID),
                         # TODO No reporting center in the input file. Should we pass that in somehow?
                         'sample-test-date': self.formatRunDate(runDate),
                         'negative-control-MFI': str(ncMfi),
                         'positive-control-MFI': str(pcMfi)
                         })

                    # If the catalogID has changed, this is a new solid-phase-panel. But we also need this for any new sampleID or patientID
                    for lotID in csvData[sampleID][patientID][runDate]:
                        current_row_panel = ET.SubElement(patientAntibodyAssmtElement, 'solid-phase-panel',
                            {'kit-manufacturer': self.manufacturer,
                            'lot': lotID
                            })

                        for allele in csvData[sampleID][patientID][runDate][lotID]:

                            baedID, beadAssignment, rawMfi = csvData[sampleID][patientID][runDate][lotID][allele]

                            # Skip if it's NC or PC, we already printed those values.
                            if(allele=='NC' and beadAssignment=='NC') or (allele=='PC' and beadAssignment=='PC'):
                                #print('Skipping this positive/negative control bead.')
                                pass
                            else:
                                #print('Checking Bead assignment:' + str(beadAssignment))
                                try:
                                    ranking = switcher[beadAssignment]
                                except Exception as e:
                                    validationFeedback += ('I do not understand this bead assignment, I expected Positive/Negative:' + str(beadAssignment) + ';\n')
                                    ranking = 2  # default value, this is negative

                                current_row_panel_bead = ET.SubElement(current_row_panel, 'bead',
                                    {'HLA-allele-specificity': str(allele),
                                    'raw-MFI': str(rawMfi).replace(',', '.'),
                                    'Ranking': str(ranking),
                                    })


        self.xmlData = ET.tostring(data)
        self.prettyPrintXml()
        return validationFeedback


    def convert(self):
        # This should be theoretically easy. But it's not really,
        # TODO: Because there are inconsistencies in the formats of the input files:
        # Things that We must detect and react to:
        # 1) Manufacturer, the Immucor and One Lambda kits use different column names in their export files.
        # 2) Delimiter. Exporters do not use a consistent delimiter, I must detect if csv are separated by comma, semicolon, tab, Other?
        # 3) Field Quoting. Sometimes the csv files use quotes around every text field, sometimes they don't. CSV readers need to know the quoting behavior.
        # 4) Decimals. Sometimes they use a "." sometimes they use ",". Different countries use different formats
        # 5) Date formats. One Lambda software at least uses the local settings for date formats. We're accepting a few formats here but we should limit it to only ISO format (YYYY-MM-DD)
        # 6) Control Bead Formats. How do the manufacturers specify what the control beads are? This varies among files from the same manufacturer, and seems to be based on user settings?
        # 7) Specificity formats. For One Lambda it seems to be a comma-separated list. QUESTION FOR HAML FORMAT: What do we do when there are multiple shared specificities for a bead?


        self.determineFormatAndManufacturer()
        print('Done Determining File Format. delimiter=(' + str(self.delimiter) + ') allFieldsQuoted=(' + str(self.allFieldsQuoted) + ') manufacturer=(' + str(self.manufacturer) + ')')

        pandasCsvReader = readCsvFile(csvFileName=self.csvFileName, delimiter=self.delimiter, allFieldsQuoted=self.allFieldsQuoted)

        if(self.delimiter is None or self.allFieldsQuoted is None or self.manufacturer is None):
            self.validationFeedback=('Could not determine the format of the input File!\nSomething is strange about the csv file:\n'
                + 'delimiter=(' + str(self.delimiter) + ')\nallFieldsQuoted=(' + str(self.allFieldsQuoted) + ')\nmanufacturer=(' + str(self.manufacturer) + ')')
        elif self.manufacturer == 'OneLambda':
            self.validationFeedback=self.ProcessOneLambda(pandasCsvReader=pandasCsvReader)
        elif self.manufacturer == 'Immucor':
            self.validationFeedback=self.ProcessImmucor(pandasCsvReader=pandasCsvReader)
        else:
            print('Not known manufacturer, unable to convert file')
            return False
    '''
    def convert(self):
        global manufacturer
        self.DetermineDelimiter()
        manufacturer, Table = self.DetermineManufacturer()
        #print('manufacturer', manufacturer)
        if manufacturer == 'OneLambda':
            print('manufacturer', manufacturer)
            self.validationFeedback=self.ProcessOneLambda(Table)
        elif manufacturer == 'Immucor':
            print('manufacturer', manufacturer)
            self.validationFeedback=self.ProcessImmucor(Table)
        else:
            print('Not known manufacturer, unable to convert file')
            return False
    '''


def readCsvFile(csvFileName=None, delimiter=None, allFieldsQuoted=False):
    #print('Reading csv File:' + str(csvFileName))

    # Copying the file is necessary to work on S3 environment.
    copyInputFile = copy.deepcopy(csvFileName)

    try:
        if(allFieldsQuoted):
            # this seems to work for one lambda files
            #print('Opening file with every quoted field:')
            pandasCsvReader = pd.read_csv(copyInputFile, index_col=False, sep=delimiter, quoting=csv.QUOTE_ALL)

        else:
            #print('Opening file, undefined quote behavior.')
            # Copy the file object so we don't use up the buffer. This is important when it's reading from S3 streams.
            pandasCsvReader = pd.read_csv(copyInputFile, index_col=False, sep=delimiter, engine="python")

        pandasCsvReader = pandasCsvReader.loc[:,~pandasCsvReader.columns.str.contains('^Unnamed')]  # eliminate empty columns at the end

        return pandasCsvReader

    except Exception as e:
        print('Exception when reading csv file ' + str(csvFileName) + ' : ' + str(e))
        raise(e)

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--csv", help="xml file to validate", type=str, required=True)
    parser.add_argument("-x", "--xml", help="xml(haml) file to write output to.", type=str, required=True)

    return parser.parse_args()


if __name__ == '__main__':

    args = parseArgs()
    csvFile = args.csv
    xmlFile = args.xml

    print('csvFile:' + csvFile)
    print('xmlFile:' + str(xmlFile))

    converter = Converter(csvFileName=csvFile, manufacturer=None, xmlFile=xmlFile)
    converter.convert()

    print('Validation Feedback:' + str(converter.validationFeedback))


    print('Done. Results written to ' + str(xmlFile))