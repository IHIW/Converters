import time
from os import getcwd, remove
from os.path import join

from Bio import SeqIO
from lxml import etree
import xml.etree.ElementTree as ElementTree
import pyhml

def getSampleIDs(hml=None):
    sampleIDs=[]
    for sample in hml.sample:
        sampleIDs.append(sample.id)
    return sampleIDs

def getHmlid(xmlText=None):
    # HMLID Is apparently not in the hml object, gotta parse it from the text.
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

def parseXmlFromText(xmlText=None, tempDirectory=None):
    #print('Parsing XML Text.')
    # Parse using pyhml
    # pyHml needs an actual file to work in. Write it.
    if(tempDirectory is None):
        tempDirectory = getcwd()
    # use a unique filename
    tempFileName = join(tempDirectory,'temp_' + str(time.time()) + '.xml')
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
        if(databaseVersion=='3390'):
            referenceInputFile=join(xmlDirectory, '3.39.0_FullLengthSequences.fasta')
        elif(databaseVersion=='3400'):
            referenceInputFile=join(xmlDirectory, '3.40.0_FullLengthSequences.fasta')
        else:
            raise Exception('Unknown IPD-IMGT/HLA database version:' + str(databaseVersion))

        rawReferenceSequences[databaseVersion]={}
        for record in SeqIO.parse(referenceInputFile, 'fasta'):
            rawReferenceSequences[databaseVersion][record.id]=record.seq


def extrapolateConsensusFromVariants(hml=None, outputDirectory=None, xmlDirectory=None, newline='\n'):
    print('Extrapolating consensus from Variants')
    #TODO: For each consensus sequence block, instead of just writing the sequences, collect them. Then I can do a MSA in biopython automatically.
    rawReferenceSequences = {}
    for sample in hml.sample:
        for typingIndex, typing in enumerate(sample.typing):
            for consensusIndex, consensusSequence in enumerate(typing.consensus_sequence):
                outputFileName = join(str(outputDirectory), 'sample_' + str(sample.id) + '.typing_' + str(typingIndex + 1) + '.consensus_' + str(consensusIndex + 1) + '.' + str(typing.gene_family) + '.fasta')
                outputFile = open(outputFileName, 'w')
                referenceLookup={}
                # Load reference sequences from file
                for referenceDatabase in consensusSequence.reference_database:
                    #print('Reference database name:' + str(referenceDatabase.name))
                    #print('Reference database version:' + str(referenceDatabase.version))
                    databaseVersion = referenceDatabase.version.replace('.', '')
                    loadReferencesFromFile(rawReferenceSequences=rawReferenceSequences, databaseVersion=databaseVersion, xmlDirectory=xmlDirectory)
                    for referenceSequence in referenceDatabase.reference_sequence:
                        #print('ID:' + str(referenceSequence.id))
                        #print('name:' + str(referenceSequence.name))

                        if(not referenceSequence.name.startswith('HLA-')):
                            # Sometimes "HLA-" is not included in the allele name.
                            # TODO: This might break on some genes like MICA..
                            print('Modifying reference allele name from ' + referenceSequence.name + ' to HLA-' + referenceSequence.name)
                            referenceSequence.name = 'HLA-' + referenceSequence.name

                        if(referenceSequence.name in rawReferenceSequences[databaseVersion]):
                            #print('Ref Found!')
                            # Print full reference sequence
                            outputFile.write('>FullReference_' + referenceSequence.id + '_' + referenceSequence.name +  newline)
                            fullSequence = str(rawReferenceSequences[databaseVersion][referenceSequence.name])
                            referenceLookup[referenceSequence.id] = fullSequence
                            outputFile.write(fullSequence + newline)
                        else:
                            # We don't have this reference sequence.
                            print('Warning! Reference sequence was not found. (Allele=' + str(referenceSequence.name) + '), (IPD-IMGT/HLA v' + databaseVersion + ')')
                            outputFile.write('>ReferenceNotFound' + referenceSequence.id + '_' + referenceSequence.name +  newline)
                            fullSequence = 'N'*(referenceSequence.end - referenceSequence.start)
                            referenceLookup[referenceSequence.id] = fullSequence
                            outputFile.write(fullSequence + newline)
                        # TODO: Is it in the standard set of reference sequences? or just in full-length?

                for consensusSequenceBlock in consensusSequence.consensus_sequence_block:
                    if(consensusSequenceBlock.reference_sequence_id) in referenceLookup.keys():
                        #print('start:' + str(consensusSequenceBlock.start))
                        #print('end:' + str(consensusSequenceBlock.end))

                        # Print Reference from indices. Store it also, dictionary with reference IDs.
                        extractedReferenceSequence = referenceLookup[consensusSequenceBlock.reference_sequence_id][consensusSequenceBlock.start:consensusSequenceBlock.end] # Did i get indexing right? I dunno.
                        outputFile.write('>ExtractedReference_' + consensusSequenceBlock.reference_sequence_id
                            + '_' + consensusSequenceBlock.description + '_(' + str(consensusSequenceBlock.start) + ':' + str(consensusSequenceBlock.end) + ')'+ newline)
                        outputFile.write(extractedReferenceSequence + newline)
                    else:
                        raise Exception ('Reference Sequence not found:' + str(consensusSequenceBlock.reference_sequence_id))


                    #print('This is the csb sequence:' + str(consensusSequenceBlock.sequence))
                    outputFile.write('>ReportedConsensus_' + consensusSequenceBlock.reference_sequence_id + '_'
                        + consensusSequenceBlock.description + '_(' + str(consensusSequenceBlock.start) + ':' + str(consensusSequenceBlock.end) + ')' + newline)
                    outputFile.write(str(consensusSequenceBlock.sequence) + newline)

                # TODO: For each consensus sequence block
                # Apply Variants to reference
                # Print all this info.

                # TODO: Can I split it by allele? Maybe not in a consnstent way...
                # TODO: Although I can split by which reference it's using.

                outputFile.close()


                # Load consensus sequence blocks.



            # For each locus print all sequences, for visual alignment.
                # 1) Reference Sequence(s) full
                # 2) Extracted Reference Sequence(s)
                # 3) Provided consensus sequences
                # 4) Constructed consensus sequences from variants


        # Get IMGT Database Version

    #imgtDatabaseVersion = None





def getGlStringFromHml(hmlFileName=None, s3=None, bucket=None):
    # TODO: Use the pyhml package. currently it requires to pass a string as an HML file name.
    #  Can I do that using the S3 key?
    #  Might need to save the file directly in a temp directory for lambda to access it. Figure that out.
    print('Getting GL String from HML for file:' + str(hmlFileName))

    glString = ''

    # Parse XML
    xmlFileObject = s3.get_object(Bucket=bucket, Key=hmlFileName)
    xmlText = xmlFileObject["Body"].read()
    xmlParser = etree.XMLParser()
    try:
        xmlTree = etree.fromstring(xmlText, xmlParser)

        for element in xmlTree.iter("*"):
            if(str(element.tag) == str('{http://schemas.nmdp.org/spec/hml/1.0.1}glstring')):
                #print('*****glstring text is this:' + str(element.text))
                if(element.text is not None):
                    glString += str(element.text).strip() + '^'


        # TODO: HLA typing can also be reported as A series of diploid locus blocks in HML
        # schemas.nmdp.org


        # Combine them in

    except etree.XMLSyntaxError as err:
        print('!!!!Could not parse xml file!')

    if(len(glString) > 0):

        return glString[0:len(glString)-1] # Trim off the trailing locus delimiter
    else:
        return None