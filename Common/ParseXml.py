from lxml import etree
import xml.etree.ElementTree as ElementTree


def parseXml(xmlText=None):
    print('Parsing XML Text.')

    documentRoot = ElementTree.fromstring(xmlText)
    print('DocumentRoot:' + str(documentRoot))

    # Get HML ID
    hmlIdNodes = documentRoot.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}hmlid')
    print('found these hmlid nodes:' + str(hmlIdNodes))
    if(len(hmlIdNodes)==0):
        print('Warning! No HMLID found!')
        hmlId=None
    elif(len(hmlIdNodes)==1):
        hmlId = str(hmlIdNodes[0].get('root') + ':' + hmlIdNodes[0].get('extension') )
        print('found hmlid (root:extension) (' + hmlId + ')')
    else:
        print('Warning! Multiple HMLIDs found, that should not happen!!')
        hmlId=None

    # Get Sample IDs & GL Strings
    sampleIds = []
    glStrings = []
    for sampleNode in documentRoot.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}sample'):
        currentID = sampleNode.get('id')
        sampleIds.append(currentID)

        for typingNode in sampleNode.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}typing'):
            for alleleAssignmentNode in typingNode.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}allele-assignment'):
                glStringNodes = alleleAssignmentNode.findall('{http://schemas.nmdp.org/spec/hml/1.0.1}glstring')

                for glStringNode in glStringNodes:
                    currentGlStringText = str(glStringNode.text).strip()
                    #print('glStringNode:' + str(glStringNode))
                    print('glstring:' + currentGlStringText)
                    glStrings.append(currentGlStringText)


    # TODO: Get variant nodes, reference sequence nodes, and indices. Return those as well.


    return hmlId,sampleIds, glStrings


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