from boto3 import client
from openpyxl import Workbook
from openpyxl.utils import get_column_letter

try:
    import IhiwRestAccess
    import ParseExcel
    import ParseXml
    import Validation
    import S3_Access
    import ImmunogenicEpitopesValidator
except Exception as e:
    print('Failed in importing files: ' + str(e))
    from Common import IhiwRestAccess
    from Common import ParseExcel
    from Common import ParseXml
    from Common import Validation
    from Common import S3_Access
    import ImmunogenicEpitopesValidator

s3 = client('s3')
from sys import exc_info

import zipfile
import io
from time import sleep

# TODO: In general I re-worked the epitopes validator, and i need the project report to match it.
#  I don't have per-row validation feedback to generate on the fly.
#  Perhaps it's better to collect the data matrixes in individual tabs
#  Validate them individually and collect the validation issues on the single tab. That would have the submitter data.
#  Then make a first tab as a summary of all the submitted data matrices.

def immunogenic_epitope_project_report_handler(event, context):
    print('Lambda handler: Creating a project report for immunogenic epitopes.')
    # This is the AWS Lambda handler function.
    try:
        # Sleep 1 second, enough time to make sure the file is available.
        sleep(1)
        # TODO: get the bucket from the sns message ( there is no sns message, trigger one?)
        #bucket = content['Records'][0]['s3']['bucket']['name']
        bucket = 'ihiw-management-upload-prod'
        #bucket = 'ihiw-management-upload-staging'

        #adminUserID=

        createImmunogenicEpitopesReport(bucket=bucket)

    except Exception as e:
        print('Exception:\n' + str(e) + '\n' + str(exc_info()))
        return str(e)


def createUploadEntriesForReport(summaryFileName=None, zipFileName=None):
    # TODO: This should be a standalone upload, not a child upload. Need some work on this part.
    # Probably need to modify the REST method to allow validation user to do this.

    # TODO: This will also make multiple copies. I should check if the report file already exists and/or (probably) overwrite it
    parentUploadName = '1497_1615205312528_PROJECT_DATA_MATRIX_ProjectReport'
    url = IhiwRestAccess.getUrl()
    token = IhiwRestAccess.getToken(url=url)

    if(url is not None and token is not None and len(url)>0 and len(token)>0):

        IhiwRestAccess.createConvertedUploadObject(newUploadFileName=summaryFileName
                                                   , newUploadFileType='OTHER'
                                                   , previousUploadFileName=parentUploadName
                                                   , url=url, token=token)
        IhiwRestAccess.createConvertedUploadObject(newUploadFileName=zipFileName
                                                   , newUploadFileType='OTHER'
                                                   , previousUploadFileName=parentUploadName
                                                   , url=url, token=token)

        IhiwRestAccess.setValidationStatus(uploadFileName=parentUploadName, isValid=True,
                                           validationFeedback='Valid Report.', validatorType='PROJECT_REPORT', url=url,
                                           token=token)
        IhiwRestAccess.setValidationStatus(uploadFileName=summaryFileName, isValid=True,
                                           validationFeedback='Valid Report.', validatorType='PROJECT_REPORT', url=url,
                                           token=token)
        IhiwRestAccess.setValidationStatus(uploadFileName=zipFileName, isValid=True,
                                           validationFeedback='Valid Report.', validatorType='PROJECT_REPORT', url=url,
                                           token=token)
    else:
        raise Exception('Could not create login token when creating upload entries for report files.')

def getTransplantationReportSpreadsheet(donorTyping=None, recipientTyping=None, recipHamlPreTxFilenames=None, recipHamlPostTxFilenames=None, s3=None, bucket=None, transplantationIndex=None, recipientSampleId=None):
    recipPreTxAntibodyData = ParseXml.parseHamlFileForBeadData(hamlFileNames=recipHamlPreTxFilenames, s3=s3, bucket=bucket, sampleIdQuery=recipientSampleId)
    recipPostTxAntibodyData = ParseXml.parseHamlFileForBeadData(hamlFileNames=recipHamlPostTxFilenames, s3=s3, bucket=bucket, sampleIdQuery=recipientSampleId)
    transplantationReportSpreadsheet = ParseExcel.createExcelTransplantationReport(donorTyping=donorTyping, recipientTyping=recipientTyping, recipPreTxAntibodyData=recipPreTxAntibodyData, recipPostTxAntibodyData=recipPostTxAntibodyData, preTxFileNames=recipHamlPreTxFilenames, postTxFileNames=recipHamlPostTxFilenames, transplantationIndex=transplantationIndex)
    return transplantationReportSpreadsheet, recipPreTxAntibodyData, recipPostTxAntibodyData

def getDataMatrixValue(validatedWorkbook=None, columnName=None, currentExcelRow=None, firstSheet=None):
    try:
        data = firstSheet[validatedWorkbook.columnNameLookup[columnName] + str(currentExcelRow)].value
        if data is None:
            return '?'
        else:
            return data
    except Exception as e:
        return '?'


def parseGlString(glstring=None):
    # Parse GL String, locus delimiters. Keep copies of genes together, I guess.
    #print('parsing GL String:' + str(glstring))
    glStringTyping={}

    # Split by locus
    for locusToken in glstring.split('^'):
        #print('Found locus:' + str(locusToken))
        if('A*' in locusToken and 'MICA*' not in locusToken):
            glStringTyping['A']=locusToken
        elif ('B*' in locusToken and 'MICB*' not in locusToken):
            glStringTyping['B'] = locusToken
        elif ('C*' in locusToken):
            glStringTyping['C'] = locusToken
        elif ('DRB1*' in locusToken):
            glStringTyping['DRB1'] = locusToken
        elif ('DRB3*' in locusToken):
            glStringTyping['DRB3'] = locusToken
        elif ('DRB4*' in locusToken):
            glStringTyping['DRB4'] = locusToken
        elif ('DRB5*' in locusToken):
            glStringTyping['DRB5'] = locusToken
        elif ('DQB1*' in locusToken):
            glStringTyping['DQB1'] = locusToken
        elif ('DQA1*' in locusToken):
            glStringTyping['DQA1'] = locusToken
        elif ('DPB1*' in locusToken):
            glStringTyping['DPB1'] = locusToken
        elif ('DPA1*' in locusToken):
            glStringTyping['DPA1'] = locusToken
        elif('HLA-E*' in locusToken or 'HLA-F*' in locusToken or 'HLA-G*' in locusToken or 'HLA-H*' in locusToken or 'MICA*' in locusToken or 'MICB*' in locusToken):
            # Not a problem but we're not using these.
            pass
        else:
            print('Unknown Locus:' + str(locusToken))

    return glStringTyping


def updateTypings(typings=None, newTypings=None):
    #print('Updating Typings\n' + str(typings) + '\nwith new typings\n' + str(newTypings))
    for locus in newTypings.keys():
        if(typings[locus] == '?'):
            typings[locus] = newTypings[locus]
        else:
            # Using a genotype ambiguity separator here.
            typings[locus] = typings[locus] + '|' + newTypings[locus]
    return typings


def constructTypings(allUploads=None, hla=None, token=None, url=None, projectIDs=None, bucket=None, sampleID=None):
    #print('getting typingData for (' + str(hla) + ')')

    fileResults = IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HML'],
        token=token, url=url,
        fileNameQueries=[str(hla).strip()],
        projectIDs=projectIDs,
        allUploads=allUploads)

    typings={}
    typings['A'] = '?'
    typings['B'] = '?'
    typings['C'] = '?'
    typings['DRB1'] = '?'
    typings['DRB3'] = '?'
    typings['DRB4'] = '?'
    typings['DRB5'] = '?'
    typings['DQB1'] = '?'
    typings['DQA1'] = '?'
    typings['DPB1'] = '?'
    typings['DPA1'] = '?'

    #print('FileResults:' + str(fileResults))

    if(len(fileResults)>0):
        # If it's an HML File Fetch the file, parse for GL Strings, Get the Typing
        #print('I found ' + str(len(fileResults)) + ' files, parsing for GLStrings...')
        for fileResult in fileResults:
            #print('Checking file for glstrings:' + str(fileResult['fileName']))
            #print('Parsing file:' + str(fileResult) + ' for glStrings.')
            currentGlStrings = ParseXml.getGlStringsFromHml(hmlFileName=fileResult['fileName'], s3=s3, bucket=bucket)
            #print('I found:' + str(currentGlStrings))

            #print('Looking for sample id:(' + str(sampleID) + ')')

            #print('Found this GLString:' + str(currentGlString))
            if currentGlStrings is not None:
                for hmlSampleId in currentGlStrings.keys():
                    if (sampleID is None or sampleID.strip()=='?' or len(str(sampleID).strip()) < 1):
                        # If there is no SampleID Given in DataMatrix, use all the GLStrings.
                        # TODO: This probably isn't completely correct. But we want to see the problem (multiple sample IDs) in the reports.
                        # This will probably result in multiple samples from one HML assigned to this person.
                        typings = updateTypings(typings=typings, newTypings=parseGlString(currentGlStrings[hmlSampleId]))
                    else:
                        # Check if the data matrix sample id is in the data matrix
                        if(str(sampleID).strip().upper() in str(hmlSampleId).strip().upper()):
                            typings = updateTypings(typings=typings, newTypings=parseGlString(currentGlStrings[hmlSampleId]))
                        else:
                            # TODO: What do we do if there is no matching sample? We found an HML file but no Sample?
                            # This is another sample in the same HML file.
                            pass

            else:
                print('Warning, No GL Strings found for HML file ' + fileResult['fileName'])

    else:
        typings.update(parseGlString(glstring=hla))

    #print('returning typings' + str(typings))
    return typings


def reduceGenotypings(typings=None):
    # Reduce the typings to two fields. Try to maintain a bit of the ambiguity if possible.
    # Keep in mind the GLStrings
    #print('Reducing Genotypings:' + str(typings))
    reducedTyping={}
    for locus in typings.keys():
        #print('Locus = ' + str(locus))
        fullGenotypes = typings[locus]

        if(fullGenotypes is None):
            print('Warning, full genotypes is None for locus ' + str(locus))
            reducedTyping[locus] = typings[locus]
        elif(type(fullGenotypes)==str):
            if(fullGenotypes=='?'):
                # This is fine. Unknown typing.
                reducedTyping[locus]=typings[locus]
            else:
                # Split by genotype ambiguities
                genotypeOptions = set()
                for genotypeString in (fullGenotypes.split('|')):
                    #print('Found genotype option:' + str(genotypeString))
                    # How many alleles does this genotype have? 1 or 2 is normal
                    alleleStrings=genotypeString.split('+')

                    if(len(alleleStrings) in [1,2]):
                        bothAlleles = []
                        for alleleString in alleleStrings:
                            #print('Allele String:' + str(alleleString))
                            alleleOptions = set()
                            for allele in alleleString.split('/'):
                                #print('Allele:' + str(allele))
                                # Get the first 2 fields
                                nomenclatureTokens = allele.split(':')
                                if(len(nomenclatureTokens)==1):
                                    alleleOptions.add(allele)
                                else:
                                    shortAlleleName = nomenclatureTokens[0] + ':' + nomenclatureTokens[1]
                                    expressionCharacter = allele[-1]
                                    if not str.isdigit(expressionCharacter):
                                        #print('This might be a nullallele!:' + allele)
                                        # Check if there are > 2 fields before adding charcter, otherwise we get doubled-up expression characters.
                                        if(len(nomenclatureTokens)>2):
                                            shortAlleleName = shortAlleleName + expressionCharacter
                                    alleleOptions.add(shortAlleleName)
                                #print('alleleOptions:' + str(alleleOptions))
                            bothAlleles.append('/'.join(sorted(list(alleleOptions))))
                            #print('BothAlleles:' + str(bothAlleles))

                        genotypeOptions.add('+'.join(sorted(list(bothAlleles))))

                    else:
                        print('Warning, Apparently there are too many alleles (' + str(len(alleleStrings)) +  ') in a single genotype ' + str(genotypeString))
                reducedTyping[locus] = '|'.join(sorted(list(genotypeOptions)))
        else:
            print('Warning, full genotypes is not a string! for locus ' + str(locus))
            reducedTyping[locus] = typings[locus]

    #print('Reduced Genotypes:' + str(reducedTyping))
    return reducedTyping


def getFullHamlFileNames(token=None, url=None, projectIDs=None, allUploads=None, cellData=None,uploadUser=None):
    hamlFileNames = []

    # Split by comma.
    hamlRawFilenames = cellData.split(',')
    hamlRawFilenames = [s.strip() for s in hamlRawFilenames]

    hamlUploadFilenames = []

    print('cellData:' + str(cellData))


    for hamlRawFilename in hamlRawFilenames:
        fileResults = IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HAML','ANTIBODY_CSV'],
            token=token, url=url,
            fileNameQueries=hamlRawFilename,
            projectIDs=projectIDs,
            allUploads=allUploads,
            uploadUser=uploadUser)

        print('Keyword:' + str(hamlRawFilename))
        print('fileResults: ' + str([fileResult['fileName'] for fileResult in fileResults]))

        for fileResult in fileResults:
            if fileResult['type'] == 'HAML':
                hamlUploadFilenames.append(fileResult['fileName'])
            elif(fileResult['type'] == 'ANTIBODY_CSV'):
                # TODO: can I just filter the "allUploads" instead of running another rest query here?
                childUploads = IhiwRestAccess.getUploadsByParentId(token=token,url=url,parentId=fileResult['id'])

                print('childUploads of file ' + str(fileResult['fileName']))

                for childUpload in childUploads:
                    if childUpload['type'] == 'HAML':
                        hamlUploadFilenames.append(childUpload['fileName'])
                    else:
                        pass
            else:
                raise Exception('I found a file that is neither HAML or ANTIBODY_CSV, that is strange:' + str(fileResult))

    # Unique filenames
    hamlUploadFilenames = sorted(list(set(hamlUploadFilenames)))

    if len(hamlUploadFilenames) != 1:
        print('Warning: for user ' + str(uploadUser) + ' I found ' + str(len(hamlUploadFilenames)) + ' files of type ' + str('HAML') + ' for the keywords ' + str(cellData))
        print('\n'.join(hamlUploadFilenames))


    return hamlUploadFilenames


def createAlleleSpecificReport(antibodiesLookup=None, recipientGenotypingsLookup=None, donorGenotypingsLookup=None, bucket=None, reportName=None):
    print('Creating Allele-Specific antibody report ' + str(reportName))
    #print('recipientGenotypingsLookup:' + str(recipientGenotypingsLookup))


    # A list of alleles
    classISpecificities=set()
    classIISpecificities=set()
    # Positive and negative controls for each patient.
    controlLookup = {}

    # First sort through the antibody data and pull out the stuff we need.
    for transplantationId in antibodiesLookup.keys():
        controlLookup[transplantationId] = {}
        controlLookup[transplantationId]['I'] = {}
        controlLookup[transplantationId]['I']['PC'] = '?'
        controlLookup[transplantationId]['I']['NC'] = '?'
        controlLookup[transplantationId]['I']['panel'] = '?'
        controlLookup[transplantationId]['II'] = {}
        controlLookup[transplantationId]['II']['PC'] = '?'
        controlLookup[transplantationId]['II']['NC'] = '?'
        controlLookup[transplantationId]['II']['panel'] = '?'

        for panel in antibodiesLookup[transplantationId]:
            hlaClass=None
            for specificity in sorted(antibodiesLookup[transplantationId][panel]):
                # Is this panel ClassI or ClassII?
                if(str(specificity).startswith('A*')
                    or str(specificity).startswith('B*')
                    or str(specificity).startswith('C*')):
                    hlaClass = 'I'
                    controlLookup[transplantationId][hlaClass]['panel']=panel
                    classISpecificities.add(specificity)
                elif(str(specificity).startswith('D')):
                    hlaClass = 'II'
                    controlLookup[transplantationId][hlaClass]['panel'] = panel
                    classIISpecificities.add(specificity)
                elif(specificity.startswith('NC : ')):
                    if (hlaClass in('I','II')):
                        controlLookup[transplantationId][hlaClass]['NC']=antibodiesLookup[transplantationId][panel][specificity]
                    else:
                        raise Exception('Is this class I or II?:' + str(specificity))
                elif (specificity.startswith('PC : ')):
                    if (hlaClass in('I','II')):
                        controlLookup[transplantationId][hlaClass]['PC']=antibodiesLookup[transplantationId][panel][specificity]
                    else:
                        raise Exception('Is this class I or II?:' + str(specificity))
                else:
                    raise Exception ('Something went wrong in allele-specific report, HLA class could not be determined:' + str(specificity))

    classISpecificities = sorted(list(set(classISpecificities)))
    classIISpecificities = sorted(list(set(classIISpecificities)))


    alleleSpecificReportWorkbook = Workbook()
    alleleSpecificReportWorksheet = alleleSpecificReportWorkbook.active
    alleleSpecificReportWorksheet.freeze_panes = 'B2'

    headers = ['transplantation_id', 'R_A', 'R_B', 'R_C', 'R_DRB1', 'R_DRB3', 'R_DRB4', 'R_DRB5', 'R_DQB1', 'R_DQA1', 'R_DPB1', 'R_DPA1'
        , 'D_A', 'D_B', 'D_C', 'D_DRB1', 'D_DRB3', 'D_DRB4', 'D_DRB5', 'D_DQB1', 'D_DQA1', 'D_DPB1', 'D_DPA1', 'classI-PanelID','classI-PC', 'classI-NC']
    headers.extend(classISpecificities)
    headers.extend(['classII-PanelID','classII-PC', 'classII-NC'])
    headers.extend(classIISpecificities)

    #print('Headers:' + str(headers))
    for headerIndex, header in enumerate(headers):
        columnLetter = get_column_letter(headerIndex+1)
        cellIndex = columnLetter + '1'
        alleleSpecificReportWorksheet[cellIndex] = header
        alleleSpecificReportWorksheet.column_dimensions[columnLetter].width = 30

    for transplantationId in antibodiesLookup.keys():
        patientData = [str(transplantationId)
            , recipientGenotypingsLookup[transplantationId]['A']
            , recipientGenotypingsLookup[transplantationId]['B']
            , recipientGenotypingsLookup[transplantationId]['C']
            , recipientGenotypingsLookup[transplantationId]['DRB1']
            , recipientGenotypingsLookup[transplantationId]['DRB3']
            , recipientGenotypingsLookup[transplantationId]['DRB4']
            , recipientGenotypingsLookup[transplantationId]['DRB5']
            , recipientGenotypingsLookup[transplantationId]['DQB1']
            , recipientGenotypingsLookup[transplantationId]['DQA1']
            , recipientGenotypingsLookup[transplantationId]['DPB1']
            , recipientGenotypingsLookup[transplantationId]['DPA1']
            , donorGenotypingsLookup[transplantationId]['A']
            , donorGenotypingsLookup[transplantationId]['B']
            , donorGenotypingsLookup[transplantationId]['C']
            , donorGenotypingsLookup[transplantationId]['DRB1']
            , donorGenotypingsLookup[transplantationId]['DRB3']
            , donorGenotypingsLookup[transplantationId]['DRB4']
            , donorGenotypingsLookup[transplantationId]['DRB5']
            , donorGenotypingsLookup[transplantationId]['DQB1']
            , donorGenotypingsLookup[transplantationId]['DQA1']
            , donorGenotypingsLookup[transplantationId]['DPB1']
            , donorGenotypingsLookup[transplantationId]['DPA1']
            , controlLookup[transplantationId]['I']['panel']
            , controlLookup[transplantationId]['I']['PC']
            , controlLookup[transplantationId]['I']['NC']
                ]

        for classISpecificity in classISpecificities:
            try:
                patientData.append(antibodiesLookup[transplantationId][ controlLookup[transplantationId]['I']['panel'] ][classISpecificity])
            except KeyError:
                patientData.append('?')

        patientData.extend([controlLookup[transplantationId]['II']['panel']
            , controlLookup[transplantationId]['II']['PC']
            , controlLookup[transplantationId]['II']['NC']])

        for classIISpecificity in classIISpecificities:
            try:
                patientData.append(antibodiesLookup[transplantationId][ controlLookup[transplantationId]['II']['panel'] ][classIISpecificity])
            except KeyError:
                patientData.append('?')


        alleleSpecificReportWorksheet.append(patientData)

    outputWorkbookbyteStream = ParseExcel.createBytestreamExcelOutputFile(workbookObject=alleleSpecificReportWorkbook)
    S3_Access.writeFileToS3(newFileName=reportName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)


def createImmunogenicEpitopesReport(bucket=None, projectIDs=None, url=None, token=None):
    print('Creating an Immunogenic Epitopes Submission Report for project ids ' + str(projectIDs))

    if url is None:
        url = IhiwRestAccess.getUrl()
        token = IhiwRestAccess.getToken(url=url)

    if(projectIDs is None):
        return
    elif(not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]

    # Convert to String for consistency..
    projectIDs = [str(projectID) for projectID in projectIDs]
    projectString = str('_'.join(projectIDs))



    # preload an upload list to use repeatedly later
    allUploads = IhiwRestAccess.getUploadsByProjects(token=token, url=url, projectIDs=projectIDs)

    dataMatrixUploadList = getDataMatrixUploads(projectIDs=projectIDs, token=token, url=url, uploadList=allUploads)

    '''
    # TODO: This is debugging code.
    print('!!!!!!!!!!!!!! I am doing a filter of data matrices, we are only looking at a limited set here!')
    newUploadList=[]
    for dataMatrixUpload in dataMatrixUploadList:
        if(dataMatrixUpload['fileName']=='1672_1636373025293_PROJECT_DATA_MATRIX_immunogenic_epitopes_template All Loci project - HML links.xlsx'):
            newUploadList.append(dataMatrixUpload)
    dataMatrixUploadList=newUploadList
    '''



    # Create Spreadsheet, Define Headers?
    summaryWithTypingWorkbook = Workbook()
    summaryWithTypingWorksheet = summaryWithTypingWorkbook.active
    summaryWithTypingWorksheet.freeze_panes = 'A2'

    summaryWithTypingHeaders = ('transplant_id', 'upload_filename', 'row#', 'submitter'
        , 'recipient_sample_id','recipient_hla', 'R_A', 'R_B', 'R_C', 'R_DRB1', 'R_DRB3', 'R_DRB4', 'R_DRB5', 'R_DQB1', 'R_DQA1', 'R_DPB1', 'R_DPA1'
        , 'donor_sample_id', 'donor_hla', 'D_A', 'D_B', 'D_C', 'D_DRB1', 'D_DRB3', 'D_DRB4', 'D_DRB5', 'D_DQB1', 'D_DQA1', 'D_DPB1', 'D_DPA1')

    reportLineIndex = 0

    for headerIndex, header in enumerate(summaryWithTypingHeaders):
        columnLetter = get_column_letter(headerIndex+1)
        cellIndex = columnLetter + '1'
        summaryWithTypingWorksheet[cellIndex] = header
        summaryWithTypingWorksheet.column_dimensions[columnLetter].width = 35

    # Write headers on new sheet.
    #summaryHeaders = ('donor_glstring', 'recipient_glstring', 'antibodies_pretx', 'antibodies_posttx'
    #                  , 'data_matrix_filename', 'valid', 'submitting_user', 'submitting_lab', 'submission_date',
    #                  'transplantation_report')

    dataMatrixHeaders = ImmunogenicEpitopesValidator.getColumnNames(isImmunogenic=True)

    # print('These are the summary headers:' + str(summaryHeaders))
    # print('These are the data matrix headers:' + str(dataMatrixHeaders))

    '''
    summaryWithTypingWorksheet.append(summaryHeaders)
    summaryWithTypingWorksheet.column_dimensions['A'].width = 40
    summaryWithTypingWorksheet.column_dimensions['B'].width = 40
    summaryWithTypingWorksheet.column_dimensions['C'].width = 40
    summaryWithTypingWorksheet.column_dimensions['D'].width = 40
    summaryWithTypingWorksheet.column_dimensions['E'].width = 40
    summaryWithTypingWorksheet.column_dimensions['F'].width = 12
    summaryWithTypingWorksheet.column_dimensions['G'].width = 25
    summaryWithTypingWorksheet.column_dimensions['H'].width = 25
    summaryWithTypingWorksheet.column_dimensions['I'].width = 25
    summaryWithTypingWorksheet.column_dimensions['J'].width = 40
    summaryWithTypingWorksheet.column_dimensions['K'].width = 40
    '''

    # for headerIndex, header in enumerate(summaryHeaders):
    # columnLetter = get_column_letter(headerIndex+1)
    # cellIndex = columnLetter + '1'
    # summaryWorksheet[cellIndex] = header
    #    summaryWorksheet.column_dimensions[columnLetter].width = 35

    supportingUploadFilenames = []
    supportingSpreadsheets = {}

    reportLineIndex = 0


    # I want the first transplantation to be index 0,
    transplantationIndex = -1
    antibodiesPreTxLookup = {}
    antibodiesPostTxLookup = {}
    recipientGenotypingsLookup = {}
    donorGenotypingsLookup = {}


    # Combine data matrices together for summary worksheet..
    for dataMatrixIndex, dataMatrixUpload in enumerate(dataMatrixUploadList):
        print('Checking Validation of this file:' + dataMatrixUpload['fileName'])
        #print('This is the upload: ' + str(dataMatrixUpload))

        excelFileObject = s3.get_object(Bucket=bucket, Key=dataMatrixUpload['fileName'])
        inputExcelBytes = io.BytesIO(excelFileObject["Body"].read())
        # validateEpitopesDataMatrix returns all the information we need.
        (validationResults, validatedWorkbook) = ImmunogenicEpitopesValidator.validateEpitopesDataMatrix(
            excelFile=inputExcelBytes, isImmunogenic=True, projectIDs=projectIDs, uploadList=allUploads)
        if (validatedWorkbook is not None):
            supportingSpreadsheets[dataMatrixUpload['fileName']] = ParseExcel.createBytestreamExcelOutputFile(
                workbookObject=validatedWorkbook)
            dataMatrixFileName = dataMatrixUpload['fileName']
            submittingUser = dataMatrixUpload['createdBy']['user']['firstName'] + ' ' + \
                             dataMatrixUpload['createdBy']['user']['lastName'] + ':\n' + \
                             dataMatrixUpload['createdBy']['user']['email']
            submittingLab = dataMatrixUpload['createdBy']['lab']['department'] + ', ' + \
                            dataMatrixUpload['createdBy']['lab']['institution']
            submissionDate = dataMatrixUpload['createdAt']

            uploadUserId = dataMatrixUpload['createdBy']['id']
            print('Found an upload user ID:' + str(uploadUserId))

            # Loop input Workbook data
            # for dataLineIndex, dataLine in enumerate(inputExcelFileData):
            firstSheet = validatedWorkbook[validatedWorkbook.sheetnames[0]]
            for dataLineIndex, dataLine in enumerate(firstSheet.iter_rows(min_row=2)):

                currentExcelRow = dataLineIndex + 2

                recipientSampleId = getDataMatrixValue(columnName='recipient_sample_id', validatedWorkbook=validatedWorkbook, currentExcelRow=currentExcelRow, firstSheet=firstSheet)
                recipientHla = getDataMatrixValue(columnName='recipient_hla', validatedWorkbook=validatedWorkbook, currentExcelRow=currentExcelRow, firstSheet=firstSheet)
                donorSampleId = getDataMatrixValue(columnName='donor_sample_id', validatedWorkbook=validatedWorkbook, currentExcelRow=currentExcelRow, firstSheet=firstSheet)
                donorHla = getDataMatrixValue(columnName='donor_hla', validatedWorkbook=validatedWorkbook, currentExcelRow=currentExcelRow, firstSheet=firstSheet)

                # Check if there is some data here, for now it's good enough if there is some HLA typing included
                # TODO: Check other columns? Maybe good data without an hla typing somehow?
                if(len(str(recipientHla).strip()) > 1 and len(str(donorHla).strip()) > 1):
                    reportLineIndex += 1
                    transplantationIndex += 1

                    # Get the Donor GLString/HML File
                    # Get the Recipient GLString/HML File
                    recipientTypings = constructTypings(allUploads=allUploads, hla=recipientHla, token=token, url=url, projectIDs=projectIDs, bucket=bucket, sampleID=recipientSampleId)
                    donorTypings = constructTypings(allUploads=allUploads, hla=donorHla, token=token, url=url, projectIDs=projectIDs, bucket=bucket, sampleID=donorSampleId)

                    recipientTypingsSimplified = reduceGenotypings(typings=recipientTypings)
                    donorTypingsSimplified = reduceGenotypings(typings=donorTypings)

                    # Put the typing in the spreadsheets.
                    recipientGenotypingsLookup[transplantationIndex] = recipientTypingsSimplified
                    donorGenotypingsLookup[transplantationIndex] = donorTypingsSimplified

                    # Write data for summaryWithTypingWorksheet
                    '''
                    ('transplant_id', 'upload_filename', 'row#', 'submitter'
                        , 'recipient_sample_id','recipient_hla', 'R_A', 'R_B', 'R_C', 'R_DRB1', 'R_DRB3', 'R_DRB4', 'R_DRB5', 'R_DQB1', 'R_DQA1', 'R_DPB1', 'R_DPA1'
                        , 'donor_sample_id', 'donor_hla', 'D_A', 'D_B', 'D_C', 'D_DRB1', 'D_DRB3', 'D_DRB4', 'D_DRB5', 'D_DQB1', 'D_DQA1', 'D_DPB1', 'D_DPA1')
                    '''
                    summaryWithTypingDataTuple = (str(transplantationIndex), dataMatrixFileName, currentExcelRow, (submittingUser + ', ' + submittingLab)
                        , recipientSampleId ,recipientHla, recipientTypingsSimplified['A'], recipientTypingsSimplified['B']
                        , recipientTypingsSimplified['C'], recipientTypingsSimplified['DRB1'], recipientTypingsSimplified['DRB3'], recipientTypingsSimplified['DRB4'], recipientTypingsSimplified['DRB5']
                        , recipientTypingsSimplified['DQB1'], recipientTypingsSimplified['DQA1'], recipientTypingsSimplified['DPB1'], recipientTypingsSimplified['DPA1']
                        , donorSampleId, donorHla, donorTypingsSimplified['A'], donorTypingsSimplified['B']
                        , donorTypingsSimplified['C'], donorTypingsSimplified['DRB1'], donorTypingsSimplified['DRB3'], donorTypingsSimplified['DRB4'], donorTypingsSimplified['DRB5']
                        , donorTypingsSimplified['DQB1'], donorTypingsSimplified['DQA1'], donorTypingsSimplified['DPB1'], donorTypingsSimplified['DPA1']
                    )
                    summaryWithTypingWorksheet.append(summaryWithTypingDataTuple)

                    # Get the antibody filenames
                    hamlPreTxCellData = getDataMatrixValue(columnName='recipient_haml_pre_tx', validatedWorkbook=validatedWorkbook, currentExcelRow=currentExcelRow, firstSheet=firstSheet)
                    recipHamlPreTxFilenames = getFullHamlFileNames(token=token,url=url, projectIDs=projectIDs, allUploads=allUploads, cellData=hamlPreTxCellData, uploadUser=uploadUserId)

                    hamlPostTxCellData = getDataMatrixValue(columnName='recipient_haml_post_tx', validatedWorkbook=validatedWorkbook, currentExcelRow=currentExcelRow, firstSheet=firstSheet)
                    recipHamlPostTxFilenames = getFullHamlFileNames(token=token,url=url, projectIDs=projectIDs, allUploads=allUploads, cellData=hamlPostTxCellData, uploadUser=uploadUserId)

                    # Create the Antibody Typing Report.
                    if(len(donorTypingsSimplified) > 0 and len(recipientTypingsSimplified) > 0):

                        transplantationReportFileName = 'AntibodyReport_' + dataMatrixUpload['fileName'] + '_Row' + str(
                            currentExcelRow) + '.xlsx'
                        transplantationReportText, preTxAntibodies, postTxAntibodies = getTransplantationReportSpreadsheet(
                            donorTyping=donorTypingsSimplified, recipientTyping=recipientTypingsSimplified,
                            recipHamlPreTxFilenames=recipHamlPreTxFilenames, recipHamlPostTxFilenames=recipHamlPostTxFilenames,
                            s3=s3, bucket=bucket, transplantationIndex=transplantationIndex, recipientSampleId=recipientSampleId)
                        supportingSpreadsheets[transplantationReportFileName] = transplantationReportText

                        #print('The antibody report returned these values:' + str(preTxAntibodies) + str(postTxAntibodies))

                        antibodiesPreTxLookup[transplantationIndex] = preTxAntibodies
                        antibodiesPostTxLookup[transplantationIndex] = postTxAntibodies

                    '''
                    for headerIndex, header in enumerate(dataMatrixHeaders):
                        columnLetter = validatedWorkbook.columnNameLookup[header]
                        # print('Checking header ' + str(header) + ' which is at column ' + columnLetter)
    
                        cellIndex = columnLetter + str(currentExcelRow)
                        cellData = firstSheet[cellIndex].value
                        # print('Cell Index: ' + str(cellIndex))
                        # print('Data:' + str(cellData))
    
                        currentGlString = None
    
                        # Add supporting files.
                        fileResults = []
                        if (header.endswith('_hla')):
                            fileResults = IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HML'],
                                                                                            token=token, url=url,
                                                                                            fileName=str(cellData),
                                                                                            projectIDs=projectIDs,
                                                                                            allUploads=allUploads)
    
                            if (len(fileResults) == 1):
                                # We found a single file mapped to this HLA result. Get a GlString.
                                currentGlString = ParseXml.getGlStringFromHml(hmlFileName=fileResults[0]['fileName'], s3=s3,
                                                                              bucket=bucket)
                            else:
                                # We didn't find a single file to calculate a glString from. Use the existing data
                                currentGlString = cellData
                            if (currentGlString is None or len(currentGlString) < 1):
                                currentGlString = ''
    
                            # print the glString in the appropriate column
                            if (header == 'donor_hla'):
                                donorGlString = currentGlString
                                donorGlStringValidationResults = Validation.validateGlString(glString=donorGlString)
                            elif (header == 'recipient_hla'):
                                recipientGlString = currentGlString
                                recipientGlStringValidationResults = Validation.validateGlString(glString=recipientGlString)
                            else:
                                raise Exception(
                                    'I cannot understand to do with the data for column ' + str(header) + ':' + str(
                                        cellData))
    
                        elif ('_haml_' in (header)):
                            # TODO: Include Antibody_CSV?
                            print('Fetching HAML Files')
    
                            # print('all uploads:' + str(allUploads))
                            print('FileName:' + str(cellData))
                            fileResults = IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HAML'],
                                                                                            token=token, url=url,
                                                                                            fileName=str(cellData),
                                                                                            projectIDs=[immuEpsProjectID,
                                                                                                        dqEpsProjectID],
                                                                                            allUploads=allUploads)
    
                            print('I just found these haml results:' + str(fileResults))
    
                            # TODO: Assuming a single HAML file here. What if !=1 results are found?
                            if (header == 'recipient_haml_pre_tx' and len(fileResults) == 1):
                                recipHamlPreTxFileName = fileResults[0]['fileName']
                            elif (header == 'recipient_haml_post_tx' and len(fileResults) == 1):
                                recipHamlPostTxFileName = fileResults[0]['fileName']
                            else:
                                pass
    
                        else:
                            pass
    
                        for uploadFile in fileResults:
                            # print('Appending this file to the upload list:' + str(uploadFile))
                            supportingUploadFilenames.append(uploadFile['fileName'])
    
                    # print('In that row I found these GLStrings ')
                    # print('Donor:' +str(donorGlString))
                    # print('recipientGlString:' + str(recipientGlString))
    
                    if (len(donorGlString) > 0 and len(recipientGlString) > 0):
    
                        transplantationReportFileName = 'AntibodyReport_' + dataMatrixUpload['fileName'] + '_Row' + str(
                            currentExcelRow) + '.xlsx'
                        transplantationReportText, preTxAntibodies, postTxAntibodies = getTransplantationReportSpreadsheet(
                            donorTyping=donorGlString, recipientTyping=recipientGlString,
                            recipHamlPreTxFilename=recipHamlPreTxFileName, recipHamlPostTxFilename=recipHamlPostTxFileName,
                            s3=s3, bucket=bucket)
                        supportingSpreadsheets[transplantationReportFileName] = transplantationReportText
    
                        if len(validationResults) == 0:
                            validationText = 'Valid'
                        else:
                            validationText = str(len(validationResults)) + ' validation issues found'
    
                        preTxAntibodyText = ''
                        postTxAntibodyText = ''
                        for specificity in sorted(list(preTxAntibodies.keys())):
                            preTxAntibodyText = preTxAntibodyText + specificity + ' : ' + str(
                                preTxAntibodies[specificity]) + '\n'
                        preTxAntibodyText = preTxAntibodyText[:-1]
                        for specificity in sorted(list(postTxAntibodies.keys())):
                            postTxAntibodyText = postTxAntibodyText + specificity + ' : ' + str(
                                postTxAntibodies[specificity]) + '\n'
                        postTxAntibodyText = postTxAntibodyText[:-1]
    
                        # Make a tuple matching this:     summaryHeaders = ('donor_glstring', 'recipient_glstring','antibodies_pretx','antibodies_posttx'
                        #         ,'data_matrix_filename','valid','submitting_user','submitting_lab','submission_date', 'transplantation_report')
                        currentTuple = (
                        donorGlString, recipientGlString, preTxAntibodyText, postTxAntibodyText, dataMatrixFileName,
                        validationText, submittingUser, submittingLab, submissionDate, transplantationReportFileName
                        )
                        summaryWorksheet.append(currentTuple)
                        print('Added Row: ' + str(tuple(summaryWorksheet.rows)[reportLineIndex]))
                        summaryWorksheet.row_dimensions[reportLineIndex + 1].height = 80
    
                    else:
                        print('Warning: Could not find a GLString for row ' + str(currentExcelRow))
                        
                    '''
                else:
                    #print('Empty Data line.')
                    pass


        else:
            print('No workbook data was found for data matrix ' + str(dataMatrixUpload['fileName']))
            print('Upload ID of missing data matrix:' + str(dataMatrixUpload['id']))

    summaryWithTypingFileName = 'Project.' + projectString+ '.SampleSummary.xlsx'
    outputWorkbookbyteStream = ParseExcel.createBytestreamExcelOutputFile(workbookObject=summaryWithTypingWorkbook)
    S3_Access.writeFileToS3(newFileName=summaryWithTypingFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)

    preTxAlleleSpecificReportName = 'Project.' + str('_'.join(projectIDs)) + '.AlleleSpecificPreTx.xlsx'
    createAlleleSpecificReport(antibodiesLookup=antibodiesPreTxLookup, recipientGenotypingsLookup=recipientGenotypingsLookup
        , donorGenotypingsLookup=donorGenotypingsLookup, bucket=bucket, reportName=preTxAlleleSpecificReportName)

    postTxAlleleSpecificReportName = 'Project.' + str('_'.join(projectIDs)) + '.AlleleSpecificPostTx.xlsx'
    createAlleleSpecificReport(antibodiesLookup=antibodiesPostTxLookup, recipientGenotypingsLookup=recipientGenotypingsLookup
        , donorGenotypingsLookup=donorGenotypingsLookup, bucket=bucket, reportName=postTxAlleleSpecificReportName)


    # create zip file
    zipFileName = 'Project.' + str('_'.join(projectIDs)) + '.TransplantationReports.zip'
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    for transplantationReportFileName in supportingSpreadsheets:
        #print('Adding file ' + str(transplantationReportFileName) + ' to ' + str(zipFileName))
        supportingFileZip.writestr(transplantationReportFileName, supportingSpreadsheets[transplantationReportFileName])

    supportingFileZip.close()
    S3_Access.writeFileToS3(newFileName=zipFileName, bucket=bucket, s3ObjectBytestream=zipFileStream)

def createNonImmunogenicEpitopesReport(bucket=None, projectIDs=None, url=None, token=None):
    print('Creating an non-Immunogenic Epitopes Submission Report for project ids ' + str(projectIDs))

    if url is None:
        url = IhiwRestAccess.getUrl()
        token = IhiwRestAccess.getToken(url=url)

    if (projectIDs is None):
        return
    elif (not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]

    # Convert to String for consistency..
    projectIDs = [str(projectID) for projectID in projectIDs]
    projectString = str('_'.join(projectIDs))

    print('The Non-immunogenic report has not yet been implemented.')

'''
def createImmunogenicEpitopesReport(bucket=None, projectID=None):
    print('Creating an Immunogenic Epitopes Submission Report.')

    url=IhiwRestAccess.getUrl()
    token=IhiwRestAccess.getToken(url=url)
    immuEpsProjectID = IhiwRestAccess.getProjectID(projectName='immunogenic_epitopes')
    dqEpsProjectID = IhiwRestAccess.getProjectID(projectName='dq_immunogenicity')
    #summaryFileName = 'Project.' + str(immuEpsProjectID) + '.Report.xlsx'
    #zipFileName = 'Project.' + str(immuEpsProjectID) + '.Report.zip'
    summaryFileName = 'ImmunogenicEpitopes.ProjectReport.xlsx'
    zipFileName = 'ImmunogenicEpitopes.ProjectReport.zip'

    dataMatrixUploadList = getDataMatrixUploads(projectIDs=[immuEpsProjectID, dqEpsProjectID], token=token, url=url)

    # Create Spreadsheet, Define Headers?
    outputWorkbook = Workbook()
    summaryWorksheet = outputWorkbook.active
    summaryWorksheet.freeze_panes = 'A2'

    # Write headers on new sheet.
    summaryHeaders = ('donor_glstring', 'recipient_glstring','antibodies_pretx','antibodies_posttx'
        ,'data_matrix_filename','valid','submitting_user','submitting_lab','submission_date', 'transplantation_report')

    dataMatrixHeaders=ImmunogenicEpitopesValidator.getColumnNames(isImmunogenic=True)

    #print('These are the summary headers:' + str(summaryHeaders))
    #print('These are the data matrix headers:' + str(dataMatrixHeaders))

    summaryWorksheet.append(summaryHeaders)
    summaryWorksheet.column_dimensions['A'].width = 40
    summaryWorksheet.column_dimensions['B'].width = 40
    summaryWorksheet.column_dimensions['C'].width = 40
    summaryWorksheet.column_dimensions['D'].width = 40
    summaryWorksheet.column_dimensions['E'].width = 40
    summaryWorksheet.column_dimensions['F'].width = 12
    summaryWorksheet.column_dimensions['G'].width = 25
    summaryWorksheet.column_dimensions['H'].width = 25
    summaryWorksheet.column_dimensions['I'].width = 25
    summaryWorksheet.column_dimensions['J'].width = 40
    summaryWorksheet.column_dimensions['K'].width = 40

    #for headerIndex, header in enumerate(summaryHeaders):
        #columnLetter = get_column_letter(headerIndex+1)
        #cellIndex = columnLetter + '1'
        #summaryWorksheet[cellIndex] = header
    #    summaryWorksheet.column_dimensions[columnLetter].width = 35

    supportingUploadFilenames = []
    supportingSpreadsheets = {}

    reportLineIndex = 0

    # preload an upload list to use repeatedly later
    allUploads = IhiwRestAccess.getUploads(token=token,url=url)

    # Combine data matrices together for summary worksheet..
    for dataMatrixIndex, dataMatrixUpload in enumerate(dataMatrixUploadList):
        #print('Checking Validation of this file:' + dataMatrixUpload['fileName'])
        #print('This is the upload: ' + str(dataMatrixUpload))

        excelFileObject = s3.get_object(Bucket=bucket, Key=dataMatrixUpload['fileName'])
        inputExcelBytes = io.BytesIO(excelFileObject["Body"].read())
        # validateEpitopesDataMatrix returns all the information we need.
        (validationResults, validatedWorkbook) = ImmunogenicEpitopesValidator.validateEpitopesDataMatrix(excelFile=inputExcelBytes, isImmunogenic=True, projectIDs=[immuEpsProjectID, dqEpsProjectID])
        if(validatedWorkbook is not None):
            supportingSpreadsheets[dataMatrixUpload['fileName']]=ParseExcel.createBytestreamExcelOutputFile(workbookObject=validatedWorkbook)
            dataMatrixFileName = dataMatrixUpload['fileName']
            submittingUser = dataMatrixUpload['createdBy']['user']['firstName'] + ' ' + dataMatrixUpload['createdBy']['user']['lastName'] + ':\n' + dataMatrixUpload['createdBy']['user']['email']
            submittingLab = dataMatrixUpload['createdBy']['lab']['department'] + ', ' + dataMatrixUpload['createdBy']['lab']['institution']
            submissionDate = dataMatrixUpload['createdAt']

            # Loop input Workbook data
            #for dataLineIndex, dataLine in enumerate(inputExcelFileData):
            firstSheet = validatedWorkbook[validatedWorkbook.sheetnames[0]]
            for dataLineIndex, dataLine in enumerate(firstSheet.iter_rows(min_row=2)):

                reportLineIndex += 1
                currentExcelRow = dataLineIndex+2

                print('Copying this line(Row=' + str(currentExcelRow) + '):' + str(dataLine))
                donorGlString = '?'
                recipientGlString = '?'
                recipHamlPreTxFileName = '?'
                recipHamlPostTxFileName = '?'

                for headerIndex, header in enumerate(dataMatrixHeaders):
                    columnLetter = validatedWorkbook.columnNameLookup[header]
                    #print('Checking header ' + str(header) + ' which is at column ' + columnLetter)

                    cellIndex = columnLetter + str(currentExcelRow)
                    cellData = firstSheet[cellIndex].value
                    #print('Cell Index: ' + str(cellIndex))
                    #print('Data:' + str(cellData))

                    currentGlString = None

                    # Add supporting files.
                    fileResults=[]
                    if(header.endswith('_hla')):
                        fileResults=IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HML'], token=token, url=url, fileName=str(cellData), projectIDs=[immuEpsProjectID, dqEpsProjectID], allUploads=allUploads)

                        if(len(fileResults) == 1):
                            # We found a single file mapped to this HLA result. Get a GlString.
                            currentGlString = ParseXml.getGlStringFromHml(hmlFileName=fileResults[0]['fileName'], s3=s3, bucket=bucket)
                        else:
                            # We didn't find a single file to calculate a glString from. Use the existing data
                            currentGlString = cellData
                        if(currentGlString is None or len(currentGlString) < 1):
                            currentGlString=''

                        # print the glString in the appropriate column
                        if(header=='donor_hla'):
                            donorGlString=currentGlString
                            donorGlStringValidationResults = Validation.validateGlString(glString=donorGlString)
                        elif(header=='recipient_hla'):
                            recipientGlString=currentGlString
                            recipientGlStringValidationResults = Validation.validateGlString(glString=recipientGlString)
                        else:
                            raise Exception ('I cannot understand to do with the data for column ' + str(header) + ':' + str(cellData))

                    elif('_haml_' in (header)):
                        # TODO: Include Antibody_CSV?
                        print('Fetching HAML Files')

                        #print('all uploads:' + str(allUploads))
                        print('FileName:' + str(cellData))
                        fileResults=IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HAML'], token=token, url=url, fileName=str(cellData), projectIDs=[immuEpsProjectID, dqEpsProjectID], allUploads=allUploads)


                        print('I just found these haml results:' + str(fileResults))

                        # TODO: Assuming a single HAML file here. What if !=1 results are found?
                        if(header=='recipient_haml_pre_tx' and len(fileResults)==1):
                            recipHamlPreTxFileName = fileResults[0]['fileName']
                        elif(header=='recipient_haml_post_tx' and len(fileResults)==1):
                            recipHamlPostTxFileName = fileResults[0]['fileName']
                        else:
                            pass

                    else:
                        pass

                    for uploadFile in fileResults:
                        #print('Appending this file to the upload list:' + str(uploadFile))
                        supportingUploadFilenames.append(uploadFile['fileName'])

                #print('In that row I found these GLStrings ')
                #print('Donor:' +str(donorGlString))
                #print('recipientGlString:' + str(recipientGlString))

                if(len(donorGlString) > 0 and len(recipientGlString) > 0):


                    transplantationReportFileName = 'AntibodyReport_' + dataMatrixUpload['fileName'] + '_Row' + str(currentExcelRow) + '.xlsx'
                    transplantationReportText, preTxAntibodies, postTxAntibodies = getTransplantationReportSpreadsheet(donorTyping=donorGlString, recipientTyping=recipientGlString, recipHamlPreTxFilename=recipHamlPreTxFileName, recipHamlPostTxFilename=recipHamlPostTxFileName ,s3=s3, bucket=bucket)
                    supportingSpreadsheets[transplantationReportFileName]=transplantationReportText

                    if len(validationResults)==0:
                        validationText='Valid'
                    else:
                        validationText=str(len(validationResults)) + ' validation issues found'

                    preTxAntibodyText=''
                    postTxAntibodyText=''
                    for specificity in sorted(list(preTxAntibodies.keys())):
                        preTxAntibodyText = preTxAntibodyText + specificity + ' : ' + str(preTxAntibodies[specificity]) + '\n'
                    preTxAntibodyText = preTxAntibodyText[:-1]
                    for specificity in sorted(list(postTxAntibodies.keys())):
                        postTxAntibodyText = postTxAntibodyText + specificity + ' : ' + str(postTxAntibodies[specificity]) + '\n'
                    postTxAntibodyText = postTxAntibodyText[:-1]

                    # Make a tuple matching this:     summaryHeaders = ('donor_glstring', 'recipient_glstring','antibodies_pretx','antibodies_posttx'
                    #         ,'data_matrix_filename','valid','submitting_user','submitting_lab','submission_date', 'transplantation_report')
                    currentTuple=(donorGlString, recipientGlString,preTxAntibodyText,postTxAntibodyText, dataMatrixFileName,validationText,submittingUser,submittingLab,submissionDate, transplantationReportFileName
                             )
                    summaryWorksheet.append(currentTuple)
                    print('Added Row: ' + str(tuple(summaryWorksheet.rows)[reportLineIndex]))
                    summaryWorksheet.row_dimensions[reportLineIndex+1].height=80

                else:
                    print('Warning: Could not find a GLString for row ' + str(currentExcelRow))


        else:
            print('No workbook data was found for data matrix ' + str(dataMatrixUpload['fileName']) )
            print('Upload ID of missing data matrix:' +  str(dataMatrixUpload['id']) )

    # Text wrapping. For every cell.
    for row in summaryWorksheet.iter_rows():
        for cell in row:
            cell.alignment = cell.alignment.copy(wrapText=True)


    createUploadEntriesForReport(summaryFileName=summaryFileName, zipFileName=zipFileName)
    outputWorkbookbyteStream = ParseExcel.createBytestreamExcelOutputFile(workbookObject=outputWorkbook)
    S3_Access.writeFileToS3(newFileName=summaryFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)



    # create zip file
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    #supportingFileZip.writestr('HelloWorld.txt', 'Hello World!')
    supportingFileZip.writestr(summaryFileName, outputWorkbookbyteStream)

    for supportingFile in list(set(supportingUploadFilenames)):
        print('Adding file ' + str(supportingFile) + ' to ' + str(zipFileName))

        supportingFileObject = s3.get_object(Bucket=bucket, Key=supportingFile)
        # TODO: We're writing a string in the zip file.
        #  I think that's fine for hml & text-like files but this might cause problems with some file types.
        supportingFileZip.writestr(supportingFile, supportingFileObject["Body"].read())

    for transplantationReportFileName in supportingSpreadsheets:
        supportingFileZip.writestr(transplantationReportFileName, supportingSpreadsheets[transplantationReportFileName])
    

    supportingFileZip.close()
    S3_Access.writeFileToS3(newFileName=zipFileName, bucket=bucket, s3ObjectBytestream=zipFileStream)



    print('Done. Summary is here: ' + str(summaryFileName) + '\nSupporting zip is here: ' + str(zipFileName)
          + '\nin bucket: ' + str(bucket))
    '''

def getDataMatrixUploads(projectIDs=None, token=None, url=None, uploadList=None):
    # collect all data matrix files.
    if(uploadList is None):
        uploadList = IhiwRestAccess.getUploads(token=token, url=url)
    #print('I found these uploads:' + str(uploadList))
    #print('This is my upload list:' + str(uploadList))
    print('Parsing ' + str(len(uploadList)) + ' uploads to find data matrices for project(s) ' + str(projectIDs) + '..')
    if(not isinstance(projectIDs, list)):
        projectIDs = [projectIDs]
    dataMatrixUploadList = []
    for upload in uploadList:
        uploadId = str(upload['project']['id'])
        #print('UploadID:' + uploadId)
        #print('ProjectIDs:' + str(projectIDs))
        if (uploadId in projectIDs):
            if (upload['type'] == 'PROJECT_DATA_MATRIX'):
                dataMatrixUploadList.append(upload)
            else:
                #print('Disregarding this upload because it is not a data matrix.')
                pass
        else:
            #print('Disregarding this upload because it is not in our project.')
            pass
    print(
        'I found a total of ' + str(len(dataMatrixUploadList)) + ' data matrices for project' + str(projectIDs) + '.\n')
    return dataMatrixUploadList







