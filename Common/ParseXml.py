import time
from os import getcwd, remove
from os.path import join

from Bio import SeqIO
from Bio.Align.Applications import ClustalOmegaCommandline
from lxml import etree
import xml.etree.ElementTree as ElementTree


'''
def getSampleIDs(hml=None):
    sampleIDs=[]
    for sample in hml.sample:
        sampleIDs.append(sample.id)
    return sampleIDs
'''
def getSampleIDs(xmlText=None):
    # TODO: do this in pyhml.
    sampleIds = set()

    xmlParser = etree.XMLParser()
    glString = ''
    try:
        xmlTree = etree.fromstring(xmlText, xmlParser)
        for sampleNode in xmlTree.iter("*"):
            if (str(sampleNode.tag) == str('{http://schemas.nmdp.org/spec/hml/1.0.1}sample')):

                sampleID = sampleNode.get('id')
                sampleIds.add(sampleID)


    except etree.XMLSyntaxError as err:
        print('Could not parse xml file!' + str(err))
        raise(err)
    return sorted(list(sampleIds))


def getHmlid(xmlText=None):
    # HMLID Is apparently not in the hml object, gotta parse it from the text.
    # TODO: parse the hmlid in pyhml
    #print('getting Hmlid')
    documentRoot = ElementTree.fromstring(xmlText)
    hmlIdNodes = documentRoot.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}hmlid')
    if(len(hmlIdNodes)==0):
        hmlId=None
    elif(len(hmlIdNodes)==1):
        hmlId = str(hmlIdNodes[0].get('root')  )
        try:
            hmlIdExtension = hmlIdNodes[0].get('extension')
            hmlId = hmlId + ':' + hmlIdExtension
        except Exception:
            print('No HmlID Extension was provided.')
    else:
        print('Warning! Multiple HMLIDs found, that should not happen!!')
        hmlId=None
    return hmlId

def getGlStrings(hml=None):
    # Collect all the glstrings from a document.
    glStrings=[]
    for sample in hml.sample:
        for typing in sample.typing:
            for alleleAssignment in typing.allele_assignment:
                for glString in alleleAssignment.glstring:
                    glStrings.append(glString)
    return glStrings

def parseXmlFromText(xmlText=None, tempDirectory=None, awsLambda=False):
    # TODO: pyHML is huge. Im moving the import here so it doesnt crash if I run without this import.
    print ('importing pyhml.....')
    import pyhml

    print('Parsing XML Text.')
    # Parse using pyhml
    # pyHml needs an actual file to work in. Write it.
    if(tempDirectory is None):
        if(awsLambda):
            tempDirectory='/tmp'
        else:
            tempDirectory = getcwd()

    # use a unique filename
    tempFileName = join(tempDirectory,'temp_' + str(time.time()) + '.xml')
    print('Temp Filename:' + str(tempFileName))
    with open(tempFileName,'w') as xmlOutputFile:
        xmlOutputFile.write(xmlText)
    hmlparser = pyhml.HmlParser(verbose=False, hmlversion='1.0.1')
    hml = hmlparser.parse(hml_file=tempFileName)
    remove(tempFileName)
    return hml

def loadReferencesFromFile(rawReferenceSequences=None, databaseVersion=None, xmlDirectory=None):
    if(databaseVersion in rawReferenceSequences.keys()):
        # Nothing to do. These were already loaded.
        return
    else:
        if (databaseVersion == '3370'):
            referenceInputFile = join(xmlDirectory, '3.37.0_FullLengthSequences.fasta')
        elif(databaseVersion=='3390'):
            referenceInputFile=join(xmlDirectory, '3.39.0_FullLengthSequences.fasta')
        elif(databaseVersion=='3400'):
            referenceInputFile=join(xmlDirectory, '3.40.0_FullLengthSequences.fasta')
        elif (databaseVersion in ['3441','3440']):
            referenceInputFile = join(xmlDirectory, '3.44.0_FullLengthSequences.fasta')
        elif (databaseVersion in ['3430']):
            referenceInputFile = join(xmlDirectory, '3.43.0_FullLengthSequences.fasta')
        elif(databaseVersion is None or databaseVersion==''):
            # TODO: Update this, handle it better if the reference database version is missing or not in this list
            referenceInputFile=join(xmlDirectory, '3.45.0_FullLengthSequences.fasta')
        else:
            raise Exception('Unknown IPD-IMGT/HLA database version:' + str(databaseVersion))

        rawReferenceSequences[databaseVersion]={}
        for record in SeqIO.parse(referenceInputFile, 'fasta'):
            rawReferenceSequences[databaseVersion][record.id]=record.seq

def extrapolateConsensusFromVariants(hml=None, outputDirectory=None, xmlDirectory=None, newline='\n', alignSequences=False):
    print('Extrapolating consensus from Variants')
    isValid = True
    validationFeedback = ''

    #TODO: For each consensus sequence block, instead of just writing the sequences, collect them. Then I can do a MSA in biopython automatically.
    rawReferenceSequences = {}
    for sample in hml.sample:
        for typingIndex, typing in enumerate(sample.typing):
            for consensusIndex, consensusSequence in enumerate(typing.consensus_sequence):
                # Dict for storing reference sequences for later use.
                referenceLookup={}
                # Dictionary identifiedSequences[refSeqId][sequenceDescription]=sequence
                identifiedSequences = {}

                # Load reference sequences from file
                for referenceDatabase in consensusSequence.reference_database:
                    databaseVersion = referenceDatabase.version.replace('.', '')
                    if databaseVersion is None:
                        # TODO: Provide Validation Feedback on this.
                        print('Warning! No reference Database Version was found! Please provide a reference database version.')
                    loadReferencesFromFile(rawReferenceSequences=rawReferenceSequences, databaseVersion=databaseVersion, xmlDirectory=xmlDirectory)
                    for referenceSequence in referenceDatabase.reference_sequence:
                        identifiedSequences[referenceSequence.id] = {}
                        startIndex = int(referenceSequence.start)
                        endIndex = int(referenceSequence.end)
                        if(endIndex <= startIndex):
                            #print('Warning! End index is bigger than start index!')
                            validationFeedback += 'End index is bigger than start index for reference sequence ' + str(referenceSequence.id) + ';' + newline
                            isValid=False

                        if(not referenceSequence.name.startswith('HLA-')):
                            # Sometimes "HLA-" is not included in the allele name.
                            # TODO: This might break on some genes like MICA..
                            #print('Modifying reference allele name from ' + referenceSequence.name + ' to HLA-' + referenceSequence.name)
                            referenceSequence.name = 'HLA-' + referenceSequence.name

                        if(referenceSequence.name in rawReferenceSequences[databaseVersion]):
                            # Full reference sequence
                            fullRefDescription = 'FullReference_' + referenceSequence.id + '_' + referenceSequence.name
                            fullSequence = str(rawReferenceSequences[databaseVersion][referenceSequence.name])
                            referenceLookup[referenceSequence.id] = fullSequence
                            identifiedSequences[referenceSequence.id][fullRefDescription] = fullSequence
                        else:
                            # We don't have this reference sequence available, cannot interpret..
                            validationFeedback += 'Warning! Reference sequence was not found. (Allele=' + str(referenceSequence.name) + '), (IPD-IMGT/HLA v' + databaseVersion + ');' + newline
                            isValid=False
                            fullRefDescription = 'ReferenceNotFound' + referenceSequence.id + '_' + referenceSequence.name
                            fullSequence = 'N'*(referenceSequence.end - referenceSequence.start)
                            referenceLookup[referenceSequence.id] = fullSequence
                            identifiedSequences[referenceSequence.id][fullRefDescription] = fullSequence

                        # TODO: Validate, Is it in the standard set of reference sequences? or just in full-length?
                for consensusSequenceBlock in consensusSequence.consensus_sequence_block:

                    startIndex = int(consensusSequenceBlock.start)
                    endIndex = int(consensusSequenceBlock.end)
                    if (endIndex <= startIndex):
                        validationFeedback += 'Warning! in consensus sequence block Start index is greater than end index!' + str(referenceSequence.id) + ';' + newline
                        isValid = False
                        temp = startIndex
                        startIndex=endIndex
                        endIndex=temp

                    if(consensusSequenceBlock.reference_sequence_id) in referenceLookup.keys():
                        #print('start:' + str(consensusSequenceBlock.start))
                        #print('end:' + str(consensusSequenceBlock.end))

                        # Print Reference from indices. Store it also, dictionary with reference IDs.
                        extractedReferenceSequence = referenceLookup[consensusSequenceBlock.reference_sequence_id][startIndex:endIndex] # Did i get indexing right? I dunno.
                        refSequenceDescription = '>ExtractedReference_' + consensusSequenceBlock.reference_sequence_id + '_' + consensusSequenceBlock.description + '_(' + str(consensusSequenceBlock.start) + ':' + str(consensusSequenceBlock.end) + ')'
                        identifiedSequences[consensusSequenceBlock.reference_sequence_id][refSequenceDescription] = extractedReferenceSequence
                    else:
                        raise Exception ('Reference Sequence not found:' + str(consensusSequenceBlock.reference_sequence_id))


                    #print('This is the csb sequence:' + str(consensusSequenceBlock.sequence))
                    reportedConsensusDescription = 'ReportedConsensus_' + consensusSequenceBlock.reference_sequence_id + '_' + consensusSequenceBlock.description + '_(' + str(consensusSequenceBlock.start) + ':' + str(consensusSequenceBlock.end) + ')'
                    identifiedSequences[consensusSequenceBlock.reference_sequence_id][reportedConsensusDescription] = str(consensusSequenceBlock.sequence)

                    if(consensusSequenceBlock.variant is not None and len(consensusSequenceBlock.variant) > 0):
                        print('Variants Detected!')
                        copyRefSeq = referenceLookup[consensusSequenceBlock.reference_sequence_id]

                        for variant in consensusSequenceBlock.variant:
                            print('Variant:' + str(variant))
                            print('Length Reference:' + str(len(copyRefSeq)))
                            referenceAtPosition=copyRefSeq[variant.start:variant.end]
                            print('Comparing....' + str(referenceAtPosition) + ':' + str(variant.reference_bases))

                            # Indices are relative to reference sequence.
                            # Apply variants

                        constructedConsensus = copyRefSeq[startIndex:endIndex]
                        constructedConsensusDescription = 'ConstructedConsensus_' + consensusSequenceBlock.reference_sequence_id + '_' + consensusSequenceBlock.description + '_(' + str(consensusSequenceBlock.start) + ':' + str(consensusSequenceBlock.end) + ')'
                        identifiedSequences[consensusSequenceBlock.reference_sequence_id][constructedConsensusDescription] = str(constructedConsensus)



                    else:
                        # No variants.
                        # TODO: Is this where I validate if extracted reference = consensus?
                        #  Do I just need to put the extracted reference as a constructed sequence again?
                        pass
                        #print('Warning, variant is None for consensus-sequence block ' + str( consensusSequenceBlock.description ) )
                        #validationFeedback += 'Warning: No variants provided for consensus-sequence block ' + str( consensusSequenceBlock.description ) + ';' + newline
                        #print(str(consensusSequenceBlock))

                # TODO: For each consensus sequence block
                # Apply Variants to reference
                # Print all this info.
                for refId in identifiedSequences.keys():
                    outputFileName = join(str(outputDirectory), 'sample_' + str(sample.id) + '.typing_' + str(typingIndex + 1) + '.consensus_' + str(consensusIndex + 1) + '.' + str(typing.gene_family) +'.ref_' + refId + '.fasta')
                    outputFile = open(outputFileName, 'w')

                    for sequenceDescription in identifiedSequences[refId].keys():
                        sequence = identifiedSequences[refId][sequenceDescription]
                        if(len(str(sequence).strip()) > 0):
                            outputFile.write('>' + sequenceDescription + newline)
                            outputFile.write(sequence + newline)
                        else:
                            print('Warning: Reference Sequence is length 0.' + sequenceDescription )
                        #

                    outputFile.close()

                    # Align
                    # TODO: Thread? It takes lots of memory.
                    try:
                        alignedClustalOOutputFilename = outputFileName.replace('.fasta','_clustalAligned.fasta')
                        if (alignSequences):
                            print('Aligning file -> ' + str(alignedClustalOOutputFilename))
                            cline = ClustalOmegaCommandline("clustalo", infile=outputFileName, outfile=alignedClustalOOutputFilename, verbose=True, auto=True, wrap=100000, threads=6, force=True)
                            print(cline)
                            cline()
                    except Exception as e:
                        print('Failed to align sequences:' + alignedClustalOOutputFilename)
                        print(e)

                # Load consensus sequence blocks.



            # For each locus print all sequences, for visual alignment.
                # 1) Reference Sequence(s) full
                # 2) Extracted Reference Sequence(s)
                # 3) Provided consensus sequences
                # 4) Constructed consensus sequences from variants


        # Get IMGT Database Version

    #imgtDatabaseVersion = None

    # TODO: Some validation checks.
    #  1) reference + variants = reported consensus
    #  2) Length of reported consensus matches



    return isValid, validationFeedback

def parseHamlFileForBeadData(hamlFileNames=None,s3=None, bucket=None, sampleIdQuery=None):
    beadData={}

    if(sampleIdQuery is None or len(str(sampleIdQuery).strip())<1):
        sampleIdQuery=None

    for hamlFileName in hamlFileNames:

        try:
            xmlFileObject = s3.get_object(Bucket=bucket, Key=hamlFileName)
        except Exception as err:
            print('Failed loading HAML data for key ' + str(hamlFileName))
            return beadData

        xmlText = xmlFileObject["Body"].read()
        documentRoot = ElementTree.fromstring(xmlText)

        # Can we find the sample ID Query within this document?
        sampleIdFound = False
        for patientAbAssessmentNode in documentRoot.findall('{urn:HAML.Namespace}patient-antibody-assessment'):
            sampleID=patientAbAssessmentNode.get('sampleID')
            if sampleIdQuery is not None and (sampleIdQuery.upper().replace(' ','') in sampleID.upper().replace(' ','')):
                # if the sample ID was not found, maybe that's ok.
                # Perhaps the SampleID was used in the HML file instead of in these HAML files.
                # In this case, we should just include all the typings.
                sampleIdFound = True


        for patientAbAssessmentNode in documentRoot.findall('{urn:HAML.Namespace}patient-antibody-assessment'):
            patientID=patientAbAssessmentNode.get('patientID')
            sampleID=patientAbAssessmentNode.get('sampleID')

            # Use this data if:
            # 1) No sample Id was provided
            # 2) We couldn't find the sample ID in this HAML file (Use every sample in this case)
            # 3) The sample ID is found in this sample.
            if sampleIdQuery is None or not sampleIdFound or sampleIdQuery.upper().replace(' ','') in sampleID.upper().replace(' ',''):

                negativeControlMfi=patientAbAssessmentNode.get('negative-control-MFI')
                positiveControlMfi = patientAbAssessmentNode.get('positive-control-MFI')
                for solidPhasePanelNode in patientAbAssessmentNode.findall('{urn:HAML.Namespace}solid-phase-panel'):
                    lotNumber=solidPhasePanelNode.get('kit-manufacturer') + ' : ' + solidPhasePanelNode.get('lot')
                    if lotNumber not in beadData.keys():
                        beadData[lotNumber]={}
                        beadData[lotNumber]['NC : '+ str(lotNumber)]=negativeControlMfi
                        beadData[lotNumber]['PC : ' + str(lotNumber)]=positiveControlMfi
                    for beadNode in solidPhasePanelNode.findall('{urn:HAML.Namespace}bead'):
                        specificity = beadNode.get('HLA-allele-specificity')
                        rawMfi = beadNode.get('raw-MFI')
                        ranking = beadNode.get('Ranking')

                        # What if we already found a value for this MFI? This means perhaps we found overlapping HAML files.
                        if specificity in beadData[lotNumber].keys():
                            beadData[lotNumber][specificity] = beadData[lotNumber][specificity] + ' ; ' + str(rawMfi)
                        else:
                            beadData[lotNumber][specificity] = str(rawMfi)
    return beadData

def getGlStringsFromHml(hmlFileName=None, s3=None, bucket=None):
    # TODO: Use the pyhml package. currently it requires to pass a string as an HML file name.
    #  Can I do that using the S3 key?
    #  Might need to save the file directly in a temp directory for lambda to access it. Figure that out.
    glStrings = {}

    # Parse XML
    xmlFileObject = s3.get_object(Bucket=bucket, Key=hmlFileName)
    xmlText = xmlFileObject["Body"].read()
    xmlParser = etree.XMLParser()
    try:
        xmlTree = etree.fromstring(xmlText, xmlParser)
        for sampleNode in xmlTree.iter("*"):
            if(str(sampleNode.tag) == str('{http://schemas.nmdp.org/spec/hml/1.0.1}sample')):

                sampleID = sampleNode.get('id')
                if (sampleID not in glStrings.keys()):
                    glStrings[sampleID] = []

                for glStringElement in sampleNode.iter("*"):
                    if(str(glStringElement.tag) == str('{http://schemas.nmdp.org/spec/hml/1.0.1}glstring')):
                        if(glStringElement.text is not None and len(glStringElement.text)>0):
                            glStrings[sampleID].append(glStringElement.text)

        # TODO: HLA typing can also be reported as A series of diploid locus blocks in HML.
        #  Should I fetch those and form them into a GLString?
        # schemas.nmdp.org
        return glStrings

    except etree.XMLSyntaxError as err:
        print('Could not parse xml file!' + str(err))
        print('Filename:' + str(hmlFileName))