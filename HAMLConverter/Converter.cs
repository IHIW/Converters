using System;
using System.IO;
using System.Xml;
using Microsoft.VisualBasic.CompilerServices;

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

    public byte[] xmlFile
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
            _manufacturer = String.Empty;
            // 
            // OneLambda mapping
            // 
            var stream = new MemoryStream(_file);
            stream.Position = 0;
            var oLReader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
            oLReader.TextFieldType = FieldType.Delimited;
            oLReader.SetDelimiters(";");
            string[] currentRow;
            currentRow = oLReader.ReadFields();
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
                    _Manufacturer = "OneLambda"; // HLA Fusion, One Lambda, Sanbio
                else if (Sample_ID > -1 & Patient_Name > -1 & Lot_ID > -1 & Run_Date > -1 & Allele > -1 & Raw_Value > -1 & Assignment > -1)
                    _Manufacturer = "Immucor";   // MatchIt, Lifecodes
            }
        }
        catch (Exception ex)
        {
        }
    }

    public void ProcessOneLambda(string Center)
    {
        string SampleID;

        var stream = new MemoryStream(_File);
        var Reader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
        Reader.TextFieldType = FieldType.Delimited;
        Reader.SetDelimiters(";");
        string[] currentRow;
        currentRow = Reader.ReadFields();
        int PatientID = default(int), SampleIDName = default(int), RunDate = default(int), CatalogID = default(int), BeadID = default(int), Specificity = default(int), RawData = default(int), NC2BeadID = default(int), PC2BeadID = default(int), Rxn = default(int);
        int NegMFI = default(int), PosMFI = default(int);
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
        using (var xmlBuilder = XmlWriter.Create(xmlStream))
        {
            xmlBuilder.WriteStartDocument();
            xmlBuilder.WriteStartElement("haml");
            while (!Reader.EndOfData)
            {
                xmlBuilder.WriteStartElement("patient-antibody-assessment");
                xmlBuilder.WriteElementString("sampleID", SampleID);
                xmlBuilder.WriteElementString("patientID", currentRow[PatientID]);
                xmlBuilder.WriteElementString("reporting-centerID", Center);
                xmlBuilder.WriteElementString("sample-test-datetime", currentRow[RunDate]);

                xmlBuilder.WriteStartElement("solid-phase-panel");
                xmlBuilder.WriteElementString("kit-manufacturer", _Manufacturer);
                xmlBuilder.WriteElementString("lot", currentRow[CatalogID]);

                while (!Reader.EndOfData && (SampleID ?? "") == (currentRow[SampleIDName] ?? ""))
                {
                    var Specs = currentRow[Specificity].Split(",");
                    int Raw = Conversions.ToInteger(currentRow[RawData]);
                    if ((currentRow[BeadID] ?? "") == (currentRow[NC2BeadID] ?? ""))
                        NegMFI = Raw;
                    if ((currentRow[BeadID] ?? "") == (currentRow[PC2BeadID] ?? ""))
                        PosMFI = Raw;
                    foreach (string SingleSpec in Specs)
                    {
                        if ((SingleSpec ?? "") != "-")
                        {
                            xmlBuilder.WriteStartElement("bead");
                            xmlBuilder.WriteElementString("HLA-allele-specificity", SingleSpec);
                            xmlBuilder.WriteElementString("raw-MFI", Conversions.ToString(Raw));
                            xmlBuilder.WriteElementString("Ranking", currentRow[Rxn]);
                            xmlBuilder.WriteEndElement(); // Bead
                        }
                    }

                    currentRow = Reader.ReadFields();
                }

                xmlBuilder.WriteEndElement(); // solid-phase-panel

                xmlBuilder.WriteElementString("negative-control-MFI", Conversions.ToString(NegMFI));
                xmlBuilder.WriteElementString("positive-control-MFI", Conversions.ToString(PosMFI));

                xmlBuilder.WriteEndElement(); // patient-antibody-assessment

                if (!Reader.EndOfData)
                    SampleID = currentRow[SampleIDName];// Next sample
            }

            xmlBuilder.WriteEndElement(); // haml
            xmlBuilder.WriteEndDocument();
        }
        // 
        // Put the stream into the _xmlFile variable
        // 
        _xmlFile = xmlStream.ToArray();
    }


    public void ProcessImmucor(string Center)
    {
        string SampleID;

        var stream = new MemoryStream(_File);
        var Reader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
        Reader.TextFieldType = FieldType.Delimited;
        Reader.SetDelimiters(",");
        string[] currentRow;
        currentRow = Reader.ReadFields();
        int Sample_ID = default(int), Patient_Name = default(int), Lot_ID = default(int), Run_Date = default(int), Allele = default(int), Raw_Value = default(int), Assignment = default(int);
        int NegMFI = default(int), PosMFI = default(int);
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
        using (var xmlBuilder = XmlWriter.Create(xmlStream))
        {
            xmlBuilder.WriteStartDocument();
            xmlBuilder.WriteStartElement("haml");
            while (!Reader.EndOfData)
            {
                xmlBuilder.WriteStartElement("patient-antibody-assessment");
                xmlBuilder.WriteElementString("sampleID", SampleID);
                xmlBuilder.WriteElementString("patientID", currentRow[Patient_Name]);
                xmlBuilder.WriteElementString("reporting-centerID", Center);
                xmlBuilder.WriteElementString("sample-test-datetime", currentRow[Run_Date]);

                xmlBuilder.WriteStartElement("solid-phase-panel");
                xmlBuilder.WriteElementString("kit-manufacturer", _Manufacturer);
                xmlBuilder.WriteElementString("lot", currentRow[Lot_ID]);

                while (!Reader.EndOfData && (SampleID ?? "") == (currentRow[Sample_ID] ?? ""))
                {
                    xmlBuilder.WriteStartElement("bead");
                    xmlBuilder.WriteElementString("HLA-allele-specificity", currentRow[Allele]);
                    xmlBuilder.WriteElementString("raw-MFI", currentRow[Raw_Value]);
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
                    xmlBuilder.WriteElementString("Ranking", Conversions.ToString(Ranking));
                    // Temporary solution for missing Pos/Neg:
                    if (Conversions.ToDouble(currentRow[Raw_Value]) < NegMFI)
                        NegMFI = Conversions.ToInteger(currentRow[Raw_Value]);
                    if (Conversions.ToDouble(currentRow[Raw_Value]) > PosMFI)
                        PosMFI = Conversions.ToInteger(currentRow[Raw_Value]);
                    xmlBuilder.WriteEndElement(); // Bead

                    currentRow = Reader.ReadFields();
                }

                xmlBuilder.WriteEndElement(); // solid-phase-panel
                // Temporary solution for missing Pos/Neg:
                xmlBuilder.WriteElementString("negative-control-MFI", Conversions.ToString(NegMFI));
                xmlBuilder.WriteElementString("positive-control-MFI", Conversions.ToString(PosMFI));

                xmlBuilder.WriteEndElement(); // patient-antibody-assessment

                if (!Reader.EndOfData)
                    SampleID = currentRow[Sample_ID];// Next sample
            }

            xmlBuilder.WriteEndElement(); // haml
            xmlBuilder.WriteEndDocument();
        }
        // 
        // Put the stream into the _xmlFile variable
        // 
        _xmlFile = xmlStream.ToArray();
    }
}

