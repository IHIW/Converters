using System;
using System.IO;
using System.Xml;
using Microsoft.VisualBasic.CompilerServices;
using Microsoft.VisualBasic.FileIO;

public partial class Converter
{
    private byte[] _file;
    private string _manufacturer;
    private byte[] _xmlFile;

    public Converter(byte[] file)
    {
        _file = file;
    }

    public string Manufacturer
    {
        get
        {
            return _manufacturer;
        }
        set
        {
            _manufacturer = value;
        }
    }

    public byte[] XmlFile
    {
        get
        {
            return _xmlFile;
        }
    }
    /// <summary>
    /// Determines the manufacturer of the input file.
    /// The manufacturer can be Immucor or OneLambda.
    /// Immucor provides a file delimited with ",".
    /// OneLambda provides a file delimited with ";".
    /// In order to determine the manufacturer all columns must be present.
    /// If no manufacturer can be determined the manufacturer string will be empty.
    /// </summary>
    public void DetermineManufacturer()
    {
        try
        {
            _manufacturer = string.Empty;
            // 
            // OneLambda mapping
            // 
            var stream = new MemoryStream(_file);
            stream.Position = 0;
            var OLReader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
            OLReader.TextFieldType = FieldType.Delimited;
            OLReader.SetDelimiters(";");
            string[] currentRow;
            currentRow = OLReader.ReadFields();
            int PatientID, SampleIDName, RunDate, CatalogID, BeadID, Specificity, RawData, NC2BeadID, PC2BeadID, Rxn;
            PatientID = -1;
            SampleIDName = -1;
            RunDate = -1;
            CatalogID = -1;
            BeadID = -1;
            Specificity = -1;
            RawData = -1;
            NC2BeadID = -1;
            PC2BeadID = -1;
            Rxn = -1;
            // 
            // Determine where the columns are
            // 
            for (int i = 0, loopTo = currentRow.Length - 1; i <= loopTo; i++)
            {
                switch (currentRow[i])
                {
                    case "PatientID":
                        {
                            PatientID = i;
                            break;
                        }

                    case "SampleIDName":
                        {
                            SampleIDName = i;
                            break;
                        }

                    case "RunDate":
                        {
                            RunDate = i;
                            break;
                        }

                    case "CatalogID":
                        {
                            CatalogID = i;
                            break;
                        }

                    case "BeadID":
                        {
                            BeadID = i;
                            break;
                        }

                    case "Specificity":
                        {
                            Specificity = i;
                            break;
                        }

                    case "RawData":
                        {
                            RawData = i;
                            break;
                        }

                    case "NC2BeadID":
                        {
                            NC2BeadID = i;
                            break;
                        }

                    case "PC2BeadID":
                        {
                            PC2BeadID = i;
                            break;
                        }

                    case "Rxn":
                        {
                            Rxn = i;
                            break;
                        }
                }
            }
            // 
            // Immucor mapping
            // 
            stream.Position = 0;
            var IMReader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
            IMReader.TextFieldType = FieldType.Delimited;
            IMReader.SetDelimiters(",");
            int Sample_ID, Patient_Name, Lot_ID, Run_Date, Allele, Raw_Value, Assignment;

            Sample_ID = -1;
            Patient_Name = -1;
            Lot_ID = -1;
            Run_Date = -1;
            Allele = -1;
            Raw_Value = -1;
            Assignment = -1;
            try
            {
                currentRow = IMReader.ReadFields();
            }
            catch (Exception ex)
            {
            }
            // Do nothing, it is not possible to read the file with this delimiter.
            finally
            {
                // 
                // Determine where the columns are
                // 
                for (int i = 0, loopTo = currentRow.Length - 1; i <= loopTo; i++)
                {
                    switch (currentRow[i])
                    {
                        case "Sample ID":
                            {
                                Sample_ID = i;
                                break;
                            }

                        case "Patient Name":
                            {
                                Patient_Name = i;
                                break;
                            }

                        case "Lot ID":
                            {
                                Lot_ID = i;
                                break;
                            }

                        case "Run Date":
                            {
                                Run_Date = i;
                                break;
                            }

                        case "Allele":
                            {
                                Allele = i;
                                break;
                            }

                        case "Raw Value":
                            {
                                Raw_Value = i;
                                break;
                            }

                        case "Assignment"                            // Uitkomst: Positive, Negative of weak
                 :
                            {
                                Assignment = i;
                                break;
                            }
                    }
                }

                IMReader.Close();
                OLReader.Close();

                if (PatientID > -1 & SampleIDName > -1 & RunDate > -1 & CatalogID > -1 & BeadID > -1 & Specificity > -1 & RawData > -1 & NC2BeadID > -1 & PC2BeadID > -1 & Rxn > -1)
                    _manufacturer = "OneLambda"; // HLA Fusion, One Lambda, Sanbio
                else if (Sample_ID > -1 & Patient_Name > -1 & Lot_ID > -1 & Run_Date > -1 & Allele > -1 & Raw_Value > -1 & Assignment > -1)
                    _manufacturer = "Immucor";   // MatchIt, Lifecodes
            }
        }
        catch (Exception ex)
        {
        }
    }

    public void ProcessOneLambda(string Center)
    {
        string SampleID;

        var stream = new MemoryStream(_file);
        var Reader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
        Reader.TextFieldType = FieldType.Delimited;
        Reader.SetDelimiters(";");
        string[] currentRow;
        currentRow = Reader.ReadFields();
        int PatientID = default(int), SampleIDName = default(int), RunDate = default(int), CatalogID = default(int), BeadID = default(int), Specificity = default(int), RawData = default(int), NC2BeadID = default(int), PC2BeadID = default(int), Rxn = default(int);
        // Dim NegMFI, PosMFI As Integer
        // 
        // Determine where the columns are
        // 
        for (int i = 0, loopTo = currentRow.Length - 1; i <= loopTo; i++)
        {
            switch (currentRow[i])
            {
                case "PatientID":
                    {
                        PatientID = i;
                        break;
                    }

                case "SampleIDName":
                    {
                        SampleIDName = i;
                        break;
                    }

                case "RunDate":
                    {
                        RunDate = i;
                        break;
                    }

                case "CatalogID":
                    {
                        CatalogID = i;
                        break;
                    }

                case "BeadID":
                    {
                        BeadID = i;
                        break;
                    }

                case "Specificity":
                    {
                        Specificity = i;
                        break;
                    }

                case "RawData":
                    {
                        RawData = i;
                        break;
                    }

                case "NC2BeadID":
                    {
                        NC2BeadID = i;
                        break;
                    }

                case "PC2BeadID":
                    {
                        PC2BeadID = i;
                        break;
                    }

                case "Rxn":
                    {
                        Rxn = i;
                        break;
                    }
            }
        }

        currentRow = Reader.ReadFields();
        SampleID = currentRow[SampleIDName];

        var xmlStream = new MemoryStream();
        using (var XmlBuilder = new XmlTextWriter(xmlStream, null))
        {
            XmlBuilder.WriteStartDocument();
            XmlBuilder.WriteStartElement("haml");
            // XmlBuilder.WriteStartElement("haml", "http://tempuri.org/HAML.xsd")
            // XmlBuilder.WriteAttributeString("xmlns", "xsi", Nothing, "http://www.w3.org/2001/XMLSchema-instance")
            // XmlBuilder.WriteAttributeString("xsi", "noNamespaceSchemaLocation", Nothing, "IHIW-haml_version_w0_3_3.xsd")
            // XmlBuilder.WriteAttributeString("version", "1.0.0")

            while (!Reader.EndOfData)
            {
                XmlBuilder.WriteStartElement("patient-antibody-assessment");
                XmlBuilder.WriteAttributeString("sampleID", SampleID);
                XmlBuilder.WriteAttributeString("patientID", currentRow[PatientID]);
                XmlBuilder.WriteAttributeString("reporting-centerID", Center);

                DateTime RundateAsDate = Conversions.ToDate(currentRow[RunDate]);
                XmlBuilder.WriteAttributeString("sample-test-date", RundateAsDate.ToString("yyyy/MM/dd"));

                int Positive = GetBeadValue(_file, Conversions.ToInteger(currentRow[PC2BeadID]), BeadID, SampleIDName, SampleID, RawData);
                int Negative = GetBeadValue(_file, Conversions.ToInteger(currentRow[NC2BeadID]), BeadID, SampleIDName, SampleID, RawData);
                XmlBuilder.WriteAttributeString("negative-control-MFI", Conversions.ToString(Negative));
                XmlBuilder.WriteAttributeString("positive-control-MFI", Conversions.ToString(Positive));

                XmlBuilder.WriteStartElement("solid-phase-panel");
                XmlBuilder.WriteAttributeString("kit-manufacturer", _manufacturer);
                XmlBuilder.WriteAttributeString("lot", currentRow[CatalogID]);

                while (!Reader.EndOfData && (SampleID ?? "") == (currentRow[SampleIDName] ?? ""))
                {
                    var Specs = currentRow[Specificity].Split(",");
                    int Raw = Conversions.ToInteger(currentRow[RawData]);
                    // If currentRow(BeadID) = currentRow(NC2BeadID) Then
                    // NegMFI = Raw
                    // End If
                    // If currentRow(BeadID) = currentRow(PC2BeadID) Then
                    // PosMFI = Raw
                    // End If
                    foreach (string SingleSpec in Specs)
                    {
                        if ((SingleSpec ?? "") != "-")
                        {
                            XmlBuilder.WriteStartElement("bead");
                            XmlBuilder.WriteAttributeString("HLA-allele-specificity", SingleSpec);
                            XmlBuilder.WriteAttributeString("raw-MFI", Conversions.ToString(Raw));
                            XmlBuilder.WriteAttributeString("Ranking", currentRow[Rxn]);
                            XmlBuilder.WriteEndElement(); // Bead
                        }
                    }

                    currentRow = Reader.ReadFields();
                }

                XmlBuilder.WriteEndElement(); // solid-phase-panel
                XmlBuilder.WriteEndElement(); // patient-antibody-assessment

                if (!Reader.EndOfData)
                    SampleID = currentRow[SampleIDName];// Next sample
            }

            XmlBuilder.WriteEndElement(); // haml
            XmlBuilder.WriteEndDocument();
        }
        // 
        // Put the stream into the _xmlFile variable
        // 
        _xmlFile = xmlStream.ToArray();
    }


    public void ProcessImmucor(string Center)
    {
        string SampleID;

        var stream = new MemoryStream(_file);
        var Reader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
        Reader.TextFieldType = FieldType.Delimited;
        Reader.SetDelimiters(",");
        string[] currentRow;
        currentRow = Reader.ReadFields();
        int Sample_ID = default(int), Patient_Name = default(int), Lot_ID = default(int), Run_Date = default(int), Allele = default(int), Raw_Value = default(int), Assignment = default(int);
        // Dim NegMFI, PosMFI As Integer
        // 
        // Determine where the columns are
        // 
        for (int i = 0, loopTo = currentRow.Length - 1; i <= loopTo; i++)
        {
            switch (currentRow[i])
            {
                case "Sample ID":
                    {
                        Sample_ID = i;
                        break;
                    }

                case "Patient Name"                         // Temporay, waiting for a proper patient ID
         :
                    {
                        Patient_Name = i;
                        break;
                    }

                case "Lot ID":
                    {
                        Lot_ID = i;
                        break;
                    }

                case "Run Date":
                    {
                        Run_Date = i;
                        break;
                    }

                case "Allele":
                    {
                        Allele = i;
                        break;
                    }

                case "Raw Value":
                    {
                        Raw_Value = i;
                        break;
                    }

                case "Assignment"                           // Positive, Negative of weak
         :
                    {
                        Assignment = i;
                        break;
                    }
            }
        }

        currentRow = Reader.ReadFields();
        SampleID = currentRow[Sample_ID];

        var xmlStream = new MemoryStream();
        using (var XmlBuilder = new XmlTextWriter(xmlStream, null))
        {
            XmlBuilder.WriteStartDocument();
            XmlBuilder.WriteStartElement("haml");
            // XmlBuilder.WriteStartElement("haml", "http://tempuri.org/HAML.xsd")
            // XmlBuilder.WriteAttributeString("xmlns", "xsi", Nothing, "http://www.w3.org/2001/XMLSchema-instance")
            // XmlBuilder.WriteAttributeString("xsi", "noNamespaceSchemaLocation", Nothing, "IHIW-haml_version_w0_3_3.xsd")
            // XmlBuilder.WriteAttributeString("version", "1.0.0")

            while (!Reader.EndOfData)
            {
                XmlBuilder.WriteStartElement("patient-antibody-assessment");
                XmlBuilder.WriteAttributeString("sampleID", SampleID);
                XmlBuilder.WriteAttributeString("patientID", currentRow[Patient_Name]);
                XmlBuilder.WriteAttributeString("reporting-centerID", Center);
                DateTime RundateAsDate = Conversions.ToDate(currentRow[Run_Date]);
                XmlBuilder.WriteAttributeString("sample-test-date", RundateAsDate.ToString("yyyy/MM/dd"));

                XmlBuilder.WriteStartElement("solid-phase-panel");
                XmlBuilder.WriteAttributeString("kit-manufacturer", _manufacturer);
                XmlBuilder.WriteAttributeString("lot", currentRow[Lot_ID]);

                while (!Reader.EndOfData && (SampleID ?? "") == (currentRow[Sample_ID] ?? ""))
                {
                    XmlBuilder.WriteStartElement("bead");
                    XmlBuilder.WriteAttributeString("HLA-allele-specificity", currentRow[Allele]);
                    XmlBuilder.WriteAttributeString("raw-MFI", currentRow[Raw_Value]);
                    int Ranking;
                    switch (currentRow[Assignment])
                    {
                        case "Positive":
                            {
                                Ranking = 8;
                                break;
                            }

                        case "Weak":
                            {
                                Ranking = 6;
                                break;
                            }

                        case "Negative":
                            {
                                Ranking = 2;
                                break;
                            }

                        default:
                            {
                                Ranking = 2;
                                break;
                            }
                    }
                    XmlBuilder.WriteAttributeString("Ranking", Conversions.ToString(Ranking));
                    XmlBuilder.WriteEndElement(); // Bead

                    currentRow = Reader.ReadFields();
                }

                XmlBuilder.WriteEndElement(); // solid-phase-panel

                XmlBuilder.WriteEndElement(); // patient-antibody-assessment

                if (!Reader.EndOfData)
                    SampleID = currentRow[Sample_ID];// Next sample
            }

            XmlBuilder.WriteEndElement(); // haml
            XmlBuilder.WriteEndDocument();
        }
        // 
        // Put the stream into the _xmlFile variable
        // 
        _xmlFile = xmlStream.ToArray();
    }

    private int GetBeadValue(byte[] Bestand, int SearchBeadID, int idxBeadID, int idxSampleIDName, string SampleID, int idxRawData)
    {
        var BeadValue = default(int);

        var stream = new MemoryStream(_file);
        var Reader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
        Reader.TextFieldType = FieldType.Delimited;
        Reader.SetDelimiters(";");
        string[] currentRow;
        currentRow = Reader.ReadFields(); // Skip the header.
        currentRow = Reader.ReadFields();
        while (!Reader.EndOfData)
        {
            if (Conversions.ToDouble(currentRow[idxBeadID]) == SearchBeadID && (currentRow[idxSampleIDName] ?? "") == (SampleID ?? ""))
                BeadValue = Conversions.ToInteger(currentRow[idxRawData]);
            currentRow = Reader.ReadFields();
        }

        return BeadValue;
    }
}

