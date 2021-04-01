import argparse
from PositiveBeads.calculate_positive_beads_handler import calculatePositiveBeads

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-x", "--xml", help="haml file to detect beads.", type=str, required=True)
    return parser.parse_args()

if __name__ == '__main__':
    args = parseArgs()
    print('Running the Positive Bead Calculator!')
    with open(args.xml,'r') as hamlFile:
        xmlText=hamlFile.read()
        #print('xmlText:' + str(xmlText))

    calculatePositiveBeads(xmlText=xmlText)