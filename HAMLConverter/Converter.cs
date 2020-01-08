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
            int patientID, sampleIDName, runDate, catalogID, beadID, specificity, rawData, nC2BeadID, pC2BeadID, rxn;
            patientID = -1;
            sampleIDName = -1;
            runDate = -1;
            catalogID = -1;
            beadID = -1;
            specificity = -1;
            rawData = -1;
            nC2BeadID = -1;
            pC2BeadID = -1;
            rxn = -1;
            // 
            // Determine where the columns are
            // 
            for (int i = 0, loopTo = currentRow.Length - 1; i <= loopTo; i++)
            {
                switch (currentRow[i])
                {
                    case "PatientID":
                        {
                            patientID = i;
                            break;
                        }

                    case "SampleIDName":
                        {
                            sampleIDName = i;
                            break;
                        }

                    case "RunDate":
                        {
                            runDate = i;
                            break;
                        }

                    case "CatalogID":
                        {
                            catalogID = i;
                            break;
                        }

                    case "BeadID":
                        {
                            beadID = i;
                            break;
                        }

                    case "Specificity":
                        {
                            specificity = i;
                            break;
                        }

                    case "RawData":
                        {
                            rawData = i;
                            break;
                        }

                    case "NC2BeadID":
                        {
                            nC2BeadID = i;
                            break;
                        }

                    case "PC2BeadID":
                        {
                            pC2BeadID = i;
                            break;
                        }

                    case "Rxn":
                        {
                            rxn = i;
                            break;
                        }
                }
            }
            // 
            // Immucor mapping
            // 
            stream.Position = 0;
            var iMReader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
            iMReader.TextFieldType = FieldType.Delimited;
            iMReader.SetDelimiters(",");
            int sample_ID, patient_Name, lot_ID, run_Date, allele, raw_Value, assignment;

            sample_ID = -1;
            patient_Name = -1;
            lot_ID = -1;
            run_Date = -1;
            allele = -1;
            raw_Value = -1;
            assignment = -1;
            try
            {
                currentRow = iMReader.ReadFields();
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
                                sample_ID = i;
                                break;
                            }

                        case "Patient Name":
                            {
                                patient_Name = i;
                                break;
                            }

                        case "Lot ID":
                            {
                                lot_ID = i;
                                break;
                            }

                        case "Run Date":
                            {
                                run_Date = i;
                                break;
                            }

                        case "Allele":
                            {
                                allele = i;
                                break;
                            }

                        case "Raw Value":
                            {
                                raw_Value = i;
                                break;
                            }

                        case "Assignment"                            // Uitkomst: Positive, Negative of weak
                 :
                            {
                                assignment = i;
                                break;
                            }
                    }
                }

                iMReader.Close();
                oLReader.Close();

                if (patientID > -1 & sampleIDName > -1 & runDate > -1 & catalogID > -1 & beadID > -1 & specificity > -1 & rawData > -1 & nC2BeadID > -1 & pC2BeadID > -1 & rxn > -1)
                    _manufacturer = "OneLambda"; // HLA Fusion, One Lambda, Sanbio
                else if (sample_ID > -1 & patient_Name > -1 & lot_ID > -1 & run_Date > -1 & allele > -1 & raw_Value > -1 & assignment > -1)
                    _manufacturer = "Immucor";   // MatchIt, Lifecodes
            }
        }
        catch (Exception ex)
        {
        }
    }

    public void ProcessOneLambda(string center)
    {
        string sampleID;

        var stream = new MemoryStream(_file);
        var reader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
        reader.TextFieldType = FieldType.Delimited;
        reader.SetDelimiters(";");
        string[] currentRow;
        currentRow = reader.ReadFields();
        int patientID = default(int), sampleIDName = default(int), runDate = default(int), catalogID = default(int), beadID = default(int), specificity = default(int), rawData = default(int), nC2BeadID = default(int), pC2BeadID = default(int), rxn = default(int);
        int negMFI = default(int), posMFI = default(int);
        // 
        // Determine where the columns are
        // 
        for (int i = 0, loopTo = currentRow.Length - 1; i <= loopTo; i++)
        {
            switch (currentRow[i])
            {
                case "PatientID":
                    {
                        patientID = i;
                        break;
                    }

                case "SampleIDName":
                    {
                        sampleIDName = i;
                        break;
                    }

                case "RunDate":
                    {
                        runDate = i;
                        break;
                    }

                case "CatalogID":
                    {
                        catalogID = i;
                        break;
                    }

                case "BeadID":
                    {
                        beadID = i;
                        break;
                    }

                case "Specificity":
                    {
                        specificity = i;
                        break;
                    }

                case "RawData":
                    {
                        rawData = i;
                        break;
                    }

                case "NC2BeadID":
                    {
                        nC2BeadID = i;
                        break;
                    }

                case "PC2BeadID":
                    {
                        pC2BeadID = i;
                        break;
                    }

                case "Rxn":
                    {
                        rxn = i;
                        break;
                    }
            }
        }

        currentRow = reader.ReadFields();
        sampleID = currentRow[sampleIDName];

        var xmlStream = new MemoryStream();
        using (var xmlBuilder = XmlWriter.Create(xmlStream))
        {
            xmlBuilder.WriteStartDocument();
            xmlBuilder.WriteStartElement("haml");
            while (!reader.EndOfData)
            {
                xmlBuilder.WriteStartElement("patient-antibody-assessment");
                xmlBuilder.WriteElementString("sampleID", sampleID);
                xmlBuilder.WriteElementString("patientID", currentRow[patientID]);
                xmlBuilder.WriteElementString("reporting-centerID", center);
                xmlBuilder.WriteElementString("sample-test-datetime", currentRow[runDate]);

                xmlBuilder.WriteStartElement("solid-phase-panel");
                xmlBuilder.WriteElementString("kit-manufacturer", _manufacturer);
                xmlBuilder.WriteElementString("lot", currentRow[catalogID]);

                while (!reader.EndOfData && (sampleID ?? "") == (currentRow[sampleIDName] ?? ""))
                {
                    var specs = currentRow[specificity].Split(",");
                    int raw = Conversions.ToInteger(currentRow[rawData]);
                    if ((currentRow[beadID] ?? "") == (currentRow[nC2BeadID] ?? ""))
                        negMFI = raw;
                    if ((currentRow[beadID] ?? "") == (currentRow[pC2BeadID] ?? ""))
                        posMFI = raw;
                    foreach (string singleSpec in specs)
                    {
                        if ((singleSpec ?? "") != "-")
                        {
                            xmlBuilder.WriteStartElement("bead");
                            xmlBuilder.WriteElementString("HLA-allele-specificity", singleSpec);
                            xmlBuilder.WriteElementString("raw-MFI", Conversions.ToString(raw));
                            xmlBuilder.WriteElementString("Ranking", currentRow[rxn]);
                            xmlBuilder.WriteEndElement(); // Bead
                        }
                    }

                    currentRow = reader.ReadFields();
                }

                xmlBuilder.WriteEndElement(); // solid-phase-panel

                xmlBuilder.WriteElementString("negative-control-MFI", Conversions.ToString(negMFI));
                xmlBuilder.WriteElementString("positive-control-MFI", Conversions.ToString(posMFI));

                xmlBuilder.WriteEndElement(); // patient-antibody-assessment

                if (!reader.EndOfData)
                    sampleID = currentRow[sampleIDName];// Next sample
            }

            xmlBuilder.WriteEndElement(); // haml
            xmlBuilder.WriteEndDocument();
        }
        // 
        // Put the stream into the _xmlFile variable
        // 
        _xmlFile = xmlStream.ToArray();
    }


    public void ProcessImmucor(string center)
    {
        string sampleID;

        var stream = new MemoryStream(_file);
        var reader = new Microsoft.VisualBasic.FileIO.TextFieldParser(stream);
        reader.TextFieldType = FieldType.Delimited;
        reader.SetDelimiters(",");
        string[] currentRow;
        currentRow = reader.ReadFields();
        int sample_ID = default(int), patient_Name = default(int), lot_ID = default(int), run_Date = default(int), allele = default(int), raw_Value = default(int), assignment = default(int);
        int negMFI = default(int), posMFI = default(int);
        // 
        // Determine where the columns are
        // 
        for (int i = 0, loopTo = currentRow.Length - 1; i <= loopTo; i++)
        {
            switch (currentRow[i])
            {
                case "Sample ID":
                    {
                        sample_ID = i;
                        break;
                    }

                case "Patient Name"                         // Temporay, waiting for a proper patient ID
         :
                    {
                        patient_Name = i;
                        break;
                    }

                case "Lot ID":
                    {
                        lot_ID = i;
                        break;
                    }

                case "Run Date":
                    {
                        run_Date = i;
                        break;
                    }

                case "Allele":
                    {
                        allele = i;
                        break;
                    }

                case "Raw Value":
                    {
                        raw_Value = i;
                        break;
                    }

                case "Assignment"                           // Positive, Negative of weak
         :
                    {
                        assignment = i;
                        break;
                    }
            }
        }

        currentRow = reader.ReadFields();
        sampleID = currentRow[sample_ID];

        var xmlStream = new MemoryStream();
        using (var xmlBuilder = XmlWriter.Create(xmlStream))
        {
            xmlBuilder.WriteStartDocument();
            xmlBuilder.WriteStartElement("haml");
            while (!reader.EndOfData)
            {
                xmlBuilder.WriteStartElement("patient-antibody-assessment");
                xmlBuilder.WriteElementString("sampleID", sampleID);
                xmlBuilder.WriteElementString("patientID", currentRow[patient_Name]);
                xmlBuilder.WriteElementString("reporting-centerID", center);
                xmlBuilder.WriteElementString("sample-test-datetime", currentRow[run_Date]);

                xmlBuilder.WriteStartElement("solid-phase-panel");
                xmlBuilder.WriteElementString("kit-manufacturer", _manufacturer);
                xmlBuilder.WriteElementString("lot", currentRow[lot_ID]);

                while (!reader.EndOfData && (sampleID ?? "") == (currentRow[sample_ID] ?? ""))
                {
                    xmlBuilder.WriteStartElement("bead");
                    xmlBuilder.WriteElementString("HLA-allele-specificity", currentRow[allele]);
                    xmlBuilder.WriteElementString("raw-MFI", currentRow[raw_Value]);
                    int ranking;
                    switch (currentRow[assignment])
                    {
                        case "Positive":
                            {
                                ranking = 8;
                                break;
                            }

                        case "Weak":
                            {
                                ranking = 6;
                                break;
                            }

                        case "Negative":
                            {
                                ranking = 2;
                                break;
                            }

                        default:
                            {
                                ranking = 2;
                                break;
                            }
                    }
                    xmlBuilder.WriteElementString("Ranking", Conversions.ToString(ranking));
                    // Temporary solution for missing Pos/Neg:
                    if (Conversions.ToDouble(currentRow[raw_Value]) < negMFI)
                        negMFI = Conversions.ToInteger(currentRow[raw_Value]);
                    if (Conversions.ToDouble(currentRow[raw_Value]) > posMFI)
                        posMFI = Conversions.ToInteger(currentRow[raw_Value]);
                    xmlBuilder.WriteEndElement(); // Bead

                    currentRow = reader.ReadFields();
                }

                xmlBuilder.WriteEndElement(); // solid-phase-panel
                // Temporary solution for missing Pos/Neg:
                xmlBuilder.WriteElementString("negative-control-MFI", Conversions.ToString(negMFI));
                xmlBuilder.WriteElementString("positive-control-MFI", Conversions.ToString(posMFI));

                xmlBuilder.WriteEndElement(); // patient-antibody-assessment

                if (!reader.EndOfData)
                    sampleID = currentRow[sample_ID];// Next sample
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

