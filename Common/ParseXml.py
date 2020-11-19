from lxml import etree


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