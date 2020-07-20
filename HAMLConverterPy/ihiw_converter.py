
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

    def __init__(self, csvFile=None, manufacturer=None, xmlFile=None):
        self.csvFile = csvFile
        #self.csvText = csvText
        self.manufacturer = manufacturer
        self.xmlFile = xmlFile
        self.xmlText = None
        self.xmlData = None
        # There are localization settings in the output files.
        # Different files are delimited by commas and semicolons. Different files use . or , as a decimal.
        # This needs to be accounted for.
        self.delimiter = None
        #self.decimal = None
        self.dateFormat = '%d-%m-%Y'

    def formatRunDate(self, RunDate):
        # format the date to the correct haml style.
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

    def DetermineDateFormat(self, dateString):
        print('Determining Date format of this string:' + dateString)
        self.dateFormat = None
        potentialDateFormats=['%d-%m-%Y', '%Y-%m-%d', '%d-%b-%Y']
        for dateFormat in potentialDateFormats:
            try:
                dateObject = datetime.datetime.strptime(dateString, dateFormat)
                print('Hooray, ' + dateString + ' IS this format:' + str(dateFormat))
                self.dateFormat=dateFormat
            except Exception as e:
                print(dateString + ' is not this format:' + str(dateFormat))
        if(self.dateFormat is None):
            print('Failed at determining date format! ')

    def DetermineDelimiter(self, ):
        print('Determining delimiter.')
        tryDelimiters=[',',';','\t']

        for delimiter in tryDelimiters:
            if(self.delimiter is None):
                try:
                    print('Checking if this file has a (' + str(delimiter) + ') delimiter')
                    # Copy the file object so we don't use up the buffer. This is important when it's reading from S3 streams.
                    copyInputFile = copy.deepcopy(self.csvFile)
                    OLReader = pd.read_csv(copyInputFile, index_col=False, sep=delimiter, engine="python")
                    OLReader = OLReader.loc[:,~OLReader.columns.str.contains('^Unnamed')]  # eliminate empty columns at the end

                    if(len(OLReader.columns.tolist()) > 3):
                        # If I find multiple columns, I hope this is sufficient.
                        print('This is a (' + str(delimiter) + ') delimited file.')
                        self.delimiter=delimiter
                except Exception as e:
                    print('Exception when parsing the file using a (' + str(delimiter) + ') delimiter. Guess that is not correct.')
        if(self.delimiter is None):
            print('I can not find the delimiter. Look into this problem.')

    def DetermineManufacturer(self,):
        col_OneLambda = ['PatientID', 'SampleIDName', 'RunDate', 'CatalogID', 'BeadID', 'Specificity', 'RawData','NC1BeadID','PC1BeadID', 'NC2BeadID','PC2BeadID', 'Rxn']
        col_Immucor = ['Sample_ID', 'Patient_Name', 'Lot_ID', 'Run_Date', 'Allele', 'Raw_Value', 'Assignment']
        OLReader = ''
        if not self.manufacturer.strip():
            print('Determining Manufacturer, csv file=' + str(self.csvFile))
            try:
                #print('Checking if it is a Immucor File:')
                # Copy the file object so we don't use up the buffer. This is important when it's reading from S3 streams.
                copyInputFile = copy.deepcopy(self.csvFile)
                #print('This is the copied object:' + str(copyInputFile))

                #pd.read_csv(io.BytesIO(obj['Body'].read()))
                OLReader = pd.read_csv(copyInputFile,index_col = False,sep=self.delimiter,engine="python")                     #try with , separator
                OLReader = OLReader.loc[:, ~OLReader.columns.str.contains('^Unnamed')]                          #eliminate empty columns at the end

                colnames = [str(c.strip('"').strip().replace(' ','_')) for c in OLReader.columns.tolist()]      #list colnames
                OLReader.columns = colnames

                if (set(colnames) & set(col_Immucor)): # Check if there is an intersection of the sets. Overlapping is good.
                    self.manufacturer = 'Immucor'
                elif(set(colnames) & set(col_OneLambda)):
                    self.manufacturer = 'OneLambda'
                else:
                    print('Cannot determine manufacturer! No matching column names.')
                    self.manufacturer = None
            except Exception as e:
                #print('Exception Parsing Immucor file:' + str(e))
                print('Exception determining column names. Cannot determine manufacturer!' + str(e))

        return(self.manufacturer,OLReader)
    
    #########
    # Get bead value
    #########
    def GetBeadValue(self,NC2BeadID, BeadID, SampleIDName, SampleID,RawData):
        if BeadID == NC2BeadID and SampleIDName == SampleID:
            # Some localizations allow a comma in these as a decimal format. Just make it a period.
            BeadValue = str(RawData).replace(',','.')
        else:
            BeadValue = 0
        return BeadValue

    #########
    # Prettify xml
    ######### 
    def prettyPrintXml(self,):
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
    def ProcessOneLambda(self,OLReader):
        #print('OneLambda to xml...',OLReader.head())
        print('OneLambda to xml...')
      
        col_OneLambda = {'PatientID':-1, 'SampleIDName':-1, 'RunDate':-1, 'CatalogID':-1,'BeadID':-1, 'Specificity':-1, 'RawData':-1, 'NC2BeadID':-1,'PC2BeadID':-1, 'Rxn':-1}
                
        # Determine where the columns are, position
        colnames = [c.strip('"') for c in OLReader.columns.tolist()] #list colnames file
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
        patientID=''
        sampleID = ''
        catalogID = ''

        #rowlength = OLReader.shape[0]
        for row in OLReader.itertuples():
            if(readerState=='negative_control'):
                negativeControlRow = row
                readerState='positive_control'
            elif(readerState=='positive_control'):
                positiveControlRow = row
                readerState = 'bead_values'

                # If the patientID or sampleIDhave changed, this is a new patient-antibody-assessment.
                # TODO: Consider writing each sample to an individual HAML file. This would need to create child elements for each HAML.
                if (row.SampleIDName.strip() != sampleID or str(row.PatientID).strip() != patientID):
                    sampleID = str(row.SampleIDName).strip()
                    patientID = str(row.PatientID).strip()
                    print('Converting a new sampleID:' + str(sampleID) + ' and patientID:' + str(
                        patientID) + ' and catalogID:' + str(catalogID))

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
                    print('Found a new bead catalog: ' + str(catalogID))

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
                    Ranking=0

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
    ########
    # Parse Immucor
    ########
    def ProcessImmucor(self,OLReader):
        print('Immucor to xml...')

        # TODO: These rankings are assigned based on whether the bead is positive. Is 8/6/2 arbitrary? I do not know where that came from.
        switcher = {'Positive':8, 'Weak':6, 'Negative':2}
        col_Immucor = {'Sample_ID':-1, 'Patient_Name':-1, 'Lot_ID':-1, 'Run_Date':-1,'Allele':-1, 'Raw_Value':-1, 'Assignment ':-1}
        #// Determine where the columns are
        colnames = OLReader.columns.tolist()
        for c in range(0,len(colnames)): 
            name = colnames[c]
            col_Immucor[name] =  c 
            
        #for each sample id/row start converting
        data = ET.Element("haml",xmlns='urn:HAML.Namespace')

        patientID=''
        sampleID = ''
        catalogID = ''

        for row in OLReader.itertuples():
            # If the patientID or sampleID have changed, this is a new patient-antibody-assessment.
            # TODO: Consider writing each sample to an individual HAML file. This would need to create child elements for each HAML.
            if (str(row.Sample_ID).strip() != sampleID or str(row.Patient_Name).strip() != patientID):
                sampleID = str(row.Sample_ID).strip()
                patientID = str(row.Patient_Name).strip()
                print('Converting a new sampleID:' + str(sampleID) + ' and patientID:' + str(
                    patientID) + ' and catalogID:' + str(catalogID))

                sample_test_date = datetime.datetime.strptime(row.Run_Date, "%d-%m-%Y").strftime("%Y-%m-%d")
                # For each new patient, we need to add the patient-antibody-assessment and solid-phase-panel nodes
                patientAntibodyAssmtElement = ET.SubElement(data, 'patient-antibody-assessment',
                    {'sampleID': str(sampleID),
                     'patientID': str(patientID),
                     'reporting-centerID': 'ReportingCenterID',
                     # TODO No reporting center in the input file. Should we pass that in somehow?
                     'sample-test-date': self.formatRunDate(sample_test_date),
                     #'negative-control-MFI': str(int(round(float(str(row.RawData).replace(',', '.'))))),
                     #'positive-control-MFI': str(int(round(float(str(row.RawData).replace(',', '.')))))
                     })
            # If the catalogID has changed, this is a new solid-phase-panel. But we also need this for any new sampleID or patientID
            if (row.Sample_ID.strip() != sampleID or str(row.Patient_Name).strip() != patientID or row.Lot_ID.strip() != catalogID):
                catalogID = row.Lot_ID.strip()
                print('Found a new bead catalog: ' + str(catalogID))

                current_row_panel = ET.SubElement(patientAntibodyAssmtElement, 'solid-phase-panel',
                    {'kit-manufacturer': self.manufacturer,
                    'lot': catalogID
                    })

            if row.Sample_ID is not None:
                Ranking = 2  #default value, this is negative
                beadAssignment=str(row.Assignment).strip()
                if beadAssignment == 'Positive':
                    Ranking = switcher['Positive']
                elif beadAssignment == 'Weak':
                    Ranking = switcher['Weak']
                elif beadAssignment == 'Negative':
                    Ranking = switcher['Negative']
                else:
                    raise Exception('Problem, What is this bead assignment? I expected Positive/Negative:' + str(beadAssignment))
                # TODO: Heterodimers are split here. It seems the A and B have the same MFI. Should we combine them into one bead element?
                current_row_panel_bead = ET.SubElement(current_row_panel,'bead',
                {'HLA-allele-specificity':str(row.Allele),
                    'raw-MFI':str(row.Raw_Value).replace(',','.'),
                    'Ranking':str(Ranking),
                })

        self.xmlData = ET.tostring(data)
        self.prettyPrintXml()


    def convert(self):
        global manufacturer
        self.DetermineDelimiter()
        manufacturer, Table = self.DetermineManufacturer()
        print('manufacturer', manufacturer)
        if manufacturer == 'OneLambda':
            print('manufacturer', manufacturer)
            self.ProcessOneLambda(Table)
        elif manufacturer == 'Immucor':
            print('manufacturer', manufacturer)
            self.ProcessImmucor(Table)
        else:
            print('Not known manufacturer, unable to convert file')
            return False


if __name__ == '__main__':

    csvFile = sys.argv[1]
    #manufacturer = sys.argv[2]
    manufacturer = ''
    xmlFile = sys.argv[3]
    #xmlFile = None

    print('csvFile:' + csvFile)
    print('manufacturer:' + manufacturer)
    print('xmlFile:' + str(xmlFile))

    converter = Converter(csvFile=csvFile,manufacturer=manufacturer,xmlFile=xmlFile)
    converter.convert()

    print('Done. Results written to ' + str(xmlFile))