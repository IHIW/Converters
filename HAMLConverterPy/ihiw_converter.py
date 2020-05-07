
import os,sys
import xml.etree.ElementTree as ET #using System.Xml;
import xml.etree
from lxml import etree
import pandas as pd
import datetime
import boto3
import io
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

    def __init__(self, csvFile, manufacturer, xmlFile):
        self.file = csvFile
        self.manufacturer = manufacturer
        self.xmlFile = xmlFile

    
    def DetermineManufacturer(self,):
        col_OneLambda = ['PatientID', 'SampleIDName', 'RunDate', 'CatalogID', 'BeadID', 'Specificity', 'RawData','NC1BeadID','PC1BeadID', 'NC2BeadID','PC2BeadID', 'Rxn']
        col_Immucor = ['Sample_ID', 'Patient_Name', 'Lot_ID', 'Run_Date', 'Allele', 'Raw_Value', 'Assignment']
        OLReader = ''
        try: 
            if not self.manufacturer.strip():
                print('inside manuf', manufacturer)
                try:
                	#pd.read_csv(io.BytesIO(obj['Body'].read()))
                    OLReader = pd.read_csv(io.Bytes(self.file['Body'].read()),index_col = False,sep=",",engine="python")                     #try with , separator
                    OLReader = OLReader.loc[:, ~OLReader.columns.str.contains('^Unnamed')]                          #eliminate empty columns at the end
                   
                    colnames = [str(c.strip('"').strip().replace(' ','_')) for c in OLReader.columns.tolist()]      #list colnames 
                    OLReader.columns = colnames
                    
                    if (set(colnames) & set(col_Immucor)):
                        self.manufacturer = 'Immucor'                                                               # MatchIt, Lifecodes
                except:
                    OLReader = pd.read_csv(io.Bytes(self.file['Body'].read()),index_col = False,sep=";",engine="python")                     #try with ; separator  
                    OLReader = OLReader.loc[:, ~OLReader.columns.str.contains('^Unnamed')]                          #eliminate empty columns at the end 

                    colnames = [str(c.strip('"')) for c in OLReader.columns.tolist()]                               #list colnames file
                    OLReader.columns = colnames
                    
                    if (set(colnames) & set(col_OneLambda)): 
                        self.manufacturer = 'OneLambda' 
                
                
        except ValueError:
            print('Unable to identify manufacturer')
        return(self.manufacturer,OLReader)
    
    #########
    # Get bead value
    #########
    def GetBeadValue(self,NC2BeadID, BeadID, SampleIDName, SampleID,RawData):
        if BeadID == NC2BeadID and SampleIDName == SampleID:
            BeadValue = RawData
        else:
            BeadValue = 0
        return

    #########
    # Prettify xml
    ######### 
    def prettyPrintXml(self,):
        assert self.xmlFile is not None
        parser = etree.XMLParser(resolve_entities=False, strip_cdata=False)
        document = etree.parse(self.xmlFile, parser)
        document.write(self.xmlFile, pretty_print=True, encoding='utf-8')

    #################
    # Parse OneLambda
    #################
    def ProcessOneLambda(self,OLReader):
        print('OneLambda to xml...',OLReader.head())
      
        col_OneLambda = {'PatientID':-1, 'SampleIDName':-1, 'RunDate':-1, 'CatalogID':-1,'BeadID':-1, 'Specificity':-1, 'RawData':-1, 'NC2BeadID':-1,'PC2BeadID':-1, 'Rxn':-1}
                
        #// Determine where the columns are, position 
        colnames = [c.strip('"') for c in OLReader.columns.tolist()] #list colnames file
        for c in range(0,len(colnames)): 
            name = colnames[c]
            col_OneLambda[name] =  c 
        
        #for each sample id/row start converting
        data = ET.Element("haml",xmlns='urn:HAML.Namespace')
        rowlength = OLReader.shape[0]
        for row in OLReader.itertuples():
        
            SampleID = row.SampleIDName
            Positive = self.GetBeadValue( row.PC2BeadID, col_OneLambda['BeadID'], col_OneLambda['SampleIDName'], SampleID, col_OneLambda['RawData'])
            Negative = self.GetBeadValue( row.NC2BeadID, col_OneLambda['BeadID'], col_OneLambda['SampleIDName'], SampleID, col_OneLambda['RawData'])

            sample_test_date= datetime.datetime.strptime(row.RunDate, "%d/%m/%Y").strftime("%Y-%m-%d")   
            current_row = ET.SubElement(data,'patient-antibody-assessment',
                             {'sampleID':str(row.SampleIDName),
                              'patientID':str(row.PatientID),
                              'reporting-centerID':'Center',
                              'sample-test-date':sample_test_date,
                              'negative-control-MFI': str(Negative),
                              'positive-control-MFI': str(Positive),
                              })
            current_row_panel = ET.SubElement(current_row,'solid-phase-panel',
                            {'kit-manufacturer':manufacturer,
                            'lot':row.CatalogID
                            })
            
            if row.SampleIDName is not None:
                
                Specs = row.Specificity.split(",")
                Raw = row.RawData
                for SingleSpec in Specs:
                    current_row_panel_bead = ET.SubElement(current_row,'bead',
                            {'HLA-allele-specificity':str(SingleSpec),
                            'raw-MFI':str(Raw),
                            'Ranking':str(row.Rxn),
                            })

        # create a new XML file with the results
        mydata = ET.tostring(data)       
        myfile = open(self.xmlFile, "wb")
        myfile.write(mydata)
        self.prettyPrintXml()
    ########
    # Parse Immucor
    ########
    def ProcessImmucor(self,OLReader):
        print('Immucor to xml...')

        switcher = {'Positive':8, 'Weak':6, 'Negative':2}
        col_Immucor = {'Sample_ID':-1, 'Patient_Name':-1, 'Lot_ID':-1, 'Run_Date':-1,'Allele':-1, 'Raw_Value':-1, 'Assignment ':-1}
        #// Determine where the columns are
        colnames = OLReader.columns.tolist()
        for c in range(0,len(colnames)): 
            name = colnames[c]
            col_Immucor[name] =  c 
            
        #for each sample id/row start converting
        data = ET.Element("haml",xmlns='urn:HAML.Namespace')

        for row in OLReader.itertuples():
            SampleID = row.Sample_ID
            sample_test_date= datetime.datetime.strptime(row.Run_Date, "%d-%m-%Y").strftime("%Y-%m-%d")   
            current_row = ET.SubElement(data,'patient-antibody-assessment',
                                {'sampleID':str(SampleID),
                                'patientID':str(row.Patient_Name),
                                'reporting-centerID':'Center',
                                'sample-test-date':sample_test_date,
                                })
            current_row_panel = ET.SubElement(current_row,'solid-phase-panel',
                                {'kit-manufacturer':self.manufacturer,
                                'lot':str(row.Lot_ID),
                                })

            if row.Sample_ID is not None:
                Ranking = 2  #default value
                if row.Assignment == 'Positive':
                    Ranking = switcher['Positive']
                elif row.Assignment == 'Weak':
                    Ranking = switcher['Weak']
                elif row.Assignment == 'Negative':
                    Ranking = switcher['Negative']    
                current_row_panel_bead = ET.SubElement(current_row,'bead',
                        {'HLA-allele-specificity':str(row.Allele),
                          'raw-MFI':str(row.Raw_Value),
                          'Ranking':str(Ranking),
                        })
        # create a new XML file with the results
        
        mydata = ET.tostring(data)
        myfile = open(self.xmlFile, "wb")
        myfile.write(mydata)
        self.prettyPrintXml()

    
if __name__ == '__main__':

    csvFile = sys.argv[1]
    manufacturer = sys.argv[2]
    xmlfile = sys.argv[3]

    print('csvFile:' + csvFile)
    print('manufacturer:' + manufacturer)
    print('xmlfile:' + xmlfile)

    converter = Converter(csvFile,manufacturer,xmlfile)
    Manufacturer,Table = converter.DetermineManufacturer()
    print('manufacturer', Manufacturer)
    if Manufacturer == 'OneLambda':
        print('Manufacturer', Manufacturer)
        converter.ProcessOneLambda(Table)
    elif Manufacturer == 'Immucor':
        print('Manufacturer', Manufacturer)
        converter.ProcessImmucor(Table)
    else: 
        print('Not known manufacturer, unable to convert file')