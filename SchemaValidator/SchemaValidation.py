from lxml import etree
from sys import exc_info

def validateAgainstSchema(schemaText=None, xmlText=None):
    try:
        # Validate XML against Schema.
        schemaTree = etree.XMLSchema(etree.XML(schemaText))
        xmlParser = etree.XMLParser(schema=schemaTree)
        try:
            xmlTree = etree.fromstring(xmlText, xmlParser)
            # If we get this far, the XML has validated successfully.
            return ('Valid')
        except etree.XMLSyntaxError as err:
            return ('Invalid:\t' + str(err))

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))
