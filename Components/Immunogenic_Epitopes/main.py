from sys import exc_info
import argparse
from ImmunogenicEpitopes import validateEpitopesDataMatrix




def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--verbose", help="verbose operation", action="store_true")
    parser.add_argument("-ex", "--excel", required=True, help="input excel file", type=str)
    # parser.add_argument("-b", "--binding", help="binding", required=True, type=str)
    # parser.add_argument("-hu", "--human", required=True, help="input fasta file of human proteome", type=str)
    # parser.add_argument("-u", "--uniprot", required=True, help="input fasta file of UniPROT KB", type=str)
    # parser.add_argument("-vi", "--virus", required=True, help="input fasta file of the virus", type=str)
    # parser.add_argument("-n", "--n", help="peptide length", type=int)

    return parser.parse_args()


if __name__=='__main__':
    try:
        args=parseArgs()
        verbose = args.verbose

        print('Starting up the immuno epitopes methods.')
        immunogenicEpitopeColumnNames = [
            'hml_id_donor'
            ,'hml_id_recipient'
            ,'haml_id_recipient_pre_tx'
            ,'haml_id_recipient_post_tx'
            ,'prozone_pre_tx'
            ,'prozone_post_tx'
            ,'availability_pre_tx'
            ,'availability_post_tx'
            ,'months_post_tx'
            ,'gender_recipient'
            ,'age_recipient_tx'
            ,'pregnancies_recipient'
            ,'immune_suppr_post_tx'
            ]

        validationResults = validateEpitopesDataMatrix(excelFile=args.excel, columnNames=immunogenicEpitopeColumnNames)
        print('Validation Results:\n' + str(validationResults))

        pass

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise
