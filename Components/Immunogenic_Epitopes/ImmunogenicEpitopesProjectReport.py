from boto3 import client
#import json
#import urllib
from Common.ParseExcel import createExcelTransplantationReport
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from os.path import join


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

def getTransplantationReportSpreadsheet(donorTyping=None, recipientTyping=None, recipHamlPreTxFilenames=None, recipHamlPostTxFilenames=None, s3=None, bucket=None):
    recipPreTxAntibodyData = ParseXml.parseHamlFileForBeadData(hamlFileNames=recipHamlPreTxFilenames, s3=s3, bucket=bucket)
    recipPostTxAntibodyData = ParseXml.parseHamlFileForBeadData(hamlFileNames=recipHamlPostTxFilenames, s3=s3, bucket=bucket)
    transplantationReportSpreadsheet, preTxAntibodies, postTxAntibodies = ParseExcel.createExcelTransplantationReport(donorTyping=donorTyping, recipientTyping=recipientTyping, recipPreTxAntibodyData=recipPreTxAntibodyData, recipPostTxAntibodyData=recipPostTxAntibodyData, preTxFileNames=recipHamlPreTxFilenames, postTxFileNames=recipHamlPostTxFilenames)
    return transplantationReportSpreadsheet, preTxAntibodies, postTxAntibodies

def createProjectZipFile(bucket=None, projectIDs=None, url=None, token=None):
    print('Creating Project Zip Files for project(s) ' + str(projectIDs))
    #print('URL=' + str(url))

    if url is None:
        url = IhiwRestAccess.getUrl()
        token = IhiwRestAccess.getToken(url=url)

    # Get a list of uploads
    print('Fetching Upload List...')
    projectUploads = IhiwRestAccess.getUploadsByProjects(token=token,url=url,projectIDs=projectIDs)
    print('I found ' + str(len(projectUploads)) + ' uploads for project IDs ' + str(projectIDs))

    # TODO: Sort by FileType? Maybe I should "Start" with Data matrices. Or Put them in Separate .zip by file size.
    # zipFileCounter=1
    # fileSizeLimit=10000
    zipFileName = zipFileName = 'Project.' + str('_'.join(projectIDs)) + '.Data.zip'

    # create zip file
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    for uploadIndex, projectUpload in enumerate(projectUploads):
    #for supportingFile in list(set(supportingUploadFilenames)):
        try:
            # TODO: Should I filter some files? Yeah probably, don't add .zip files, to avoid redundancy.
            # Sort into "subfolders" in .zip file
            supportingFileName = projectUpload['fileName']
            uploadType = str(projectUpload['type'])
            uploadProjectId = str(projectUpload['project']['id'])
            uploadProjectName = str(projectUpload['project']['name']).replace('.','').replace(' ','_').replace('-','_')
            #print('ProjectName=' + str(uploadProjectName))

            if (uploadIndex%100==0):
                #print('Adding file ' + str(supportingFile) + ' to ' + str(zipFileName))
                print('Progress = ' + str(uploadIndex) + '/' + str(len(projectUploads)) + ' = ' + str (100 * (uploadIndex/len(projectUploads))) + '%')

            supportingFileObject = s3.get_object(Bucket=bucket, Key=supportingFileName)
            fileNameWithRelativePath=join('project_' + str(uploadProjectName),join(uploadType,supportingFileName))
            supportingFileZip.writestr(fileNameWithRelativePath, supportingFileObject["Body"].read())

        except Exception as e:
            print('Exception when writing file to zip:\n' + str(e) + '\n' + str(exc_info()))


        # TODO: Add logic for maximum .zip file size.
        #  Note: make sure these newly created .zip files won't be included in the actual project .zip.


    print('Closing Zip File....')
    supportingFileZip.close()
    print('Writing file to bucket ' + str(bucket) + ' : ' + zipFileName)
    S3_Access.writeFileToS3(newFileName=zipFileName, bucket=bucket, s3ObjectBytestream=zipFileStream)

    # TODO: Make Upload Object for (each) project leader
    print('Done')

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
    print('parsing GL String:' + str(glstring))
    glStringTyping={}

    # Split by locus
    for locusToken in glstring.split('^'):
        print('Found locus:' + str(locusToken))
        if('A*' in locusToken):
            glStringTyping['A']=locusToken
        elif ('B*' in locusToken):
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
        else:
            print('Unknown Locus:' + str(locusToken))

    return glStringTyping



def constructTypings(allUploads=None, hla=None, token=None, url=None, projectIDs=None, bucket=None):
    print('getting typingData for (' + str(hla) + ')')

    fileResults = IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HML'],
        token=token, url=url,
        fileName=str(hla),
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

    print('FileResults:' + str(fileResults))

    if(len(fileResults)>0):
        # If it's an HML File Fetch the file, parse for GL Strings, Get the Typing
        #print('I found ' + str(len(fileResults)) + ' files, parsing for GLStrings...')
        for fileResult in fileResults:
            #print('Checking file for glstrings:' + str(fileResult['fileName']))
            currentGlString = ParseXml.getGlStringFromHml(hmlFileName=fileResult['fileName'], s3=s3, bucket=bucket)
            #print('Found this GLString:' + str(currentGlString))
            if currentGlString is not None:
                typings.update(parseGlString(glstring=currentGlString))
            else:
                print('Warning, No GL Strings found for HML file ' + fileResult['fileName'])

    else:
        typings.update(parseGlString(glstring=hla))

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
                                        print('This might be a nullallele!:' + allele)
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

    for hamlRawFilename in hamlRawFilenames:
        fileResults = IhiwRestAccess.getUploadFileNamesByPartialKeyword(uploadTypeFilter=['HAML'],
            token=token, url=url,
            fileName=str(cellData),
            projectIDs=projectIDs,
            allUploads=allUploads,
            uploadUser=uploadUser)


        if len(fileResults) != 1:
            print('Warning: I found ' + str(len(fileResults)) + ' for the keyword ' + str(hamlRawFilename))

        # TODO: There should really be only one matching filename here. Should I check if there is only one?
        for fileResult in fileResults:
            hamlFileNames.append(fileResult['fileName'])

    return hamlFileNames


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

    antibodyPreTxFileName = 'Project.' + projectString + '.Antibody.PreTx.xlsx'
    antibodyPostTxFileName = 'Project.' + projectString+ '.Antibody.PostTx.xlsx'
    summaryFileName = 'Project.' + projectString+ '.SummaryReport.xlsx'
    summaryWithTypingFileName = 'Project.' + projectString+ '.SampleSummary.xlsx'

    # preload an upload list to use repeatedly later
    allUploads = IhiwRestAccess.getUploadsByProjects(token=token, url=url, projectIDs=projectIDs)

    dataMatrixUploadList = getDataMatrixUploads(projectIDs=projectIDs, token=token, url=url, uploadList=allUploads)

    # Create Spreadsheet, Define Headers?
    summaryWithTypingWorkbook = Workbook()
    summaryWithTypingWorksheet = summaryWithTypingWorkbook.active
    summaryWithTypingWorksheet.freeze_panes = 'A2'

    summaryWithTypingHeaders = ('upload_filename', 'row#', 'submitter'
        , 'recipient_sample_id','recipient_hla', 'R_A', 'R_B', 'R_C', 'R_DRB1', 'R_DRB3', 'R_DRB4', 'R_DRB5', 'R_DQB1', 'R_DQA1', 'R_DPB1', 'R_DPA1'
        , 'donor_sample_id', 'donor_hla', 'D_A', 'D_B', 'D_C', 'D_DRB1', 'D_DRB3', 'D_DRB4', 'D_DRB5', 'D_DQB1', 'D_DQA1', 'D_DPB1', 'D_DPA1')

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
                    recipientTypings = constructTypings(allUploads=allUploads, hla=recipientHla, token=token, url=url, projectIDs=projectIDs, bucket=bucket)
                    donorTypings = constructTypings(allUploads=allUploads, hla=donorHla, token=token, url=url, projectIDs=projectIDs, bucket=bucket)

                    recipientTypingsSimplified = reduceGenotypings(typings=recipientTypings)
                    donorTypingsSimplified = reduceGenotypings(typings=donorTypings)

                    # Put the typing in the spreadsheets.


                    recipientGenotypingsLookup[transplantationIndex] = recipientTypingsSimplified
                    donorGenotypingsLookup[transplantationIndex] = donorTypingsSimplified
                    # TODO: What about HAML?



                    # Write data for summaryWithTypingWorksheet
                    '''
                    ('upload_filename', 'row#', 'submitter'
                        , 'recipient_sample_id','recipient_hla', 'R_A', 'R_B', 'R_C', 'R_DRB1', 'R_DRB3', 'R_DRB4', 'R_DRB5', 'R_DQB1', 'R_DQA1', 'R_DPB1', 'R_DPA1'
                        , 'donor_sample_id', 'donor_hla', 'D_A', 'D_B', 'D_C', 'D_DRB1', 'D_DRB3', 'D_DRB4', 'D_DRB5', 'D_DQB1', 'D_DQA1', 'D_DPB1', 'D_DPA1')
                    '''
                    summaryWithTypingDataTuple = (dataMatrixFileName, currentExcelRow, (submittingUser + ', ' + submittingLab)
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
                            s3=s3, bucket=bucket)
                        supportingSpreadsheets[transplantationReportFileName] = transplantationReportText

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

    # Text wrapping. For every cell.
    #for row in summaryWithTypingWorksheet.iter_rows():
    #    for cell in row:
    #        cell.alignment = cell.alignment.copy(wrapText=True)


    #createUploadEntriesForReport(summaryFileName=summaryFileName, zipFileName=zipFileName)
    outputWorkbookbyteStream = ParseExcel.createBytestreamExcelOutputFile(workbookObject=summaryWithTypingWorkbook)
    S3_Access.writeFileToS3(newFileName=summaryWithTypingFileName, bucket=bucket, s3ObjectBytestream=outputWorkbookbyteStream)

    # create zip file
    zipFileName = 'Project.' + str('_'.join(projectIDs)) + '.TransplantationReports.zip'
    zipFileStream = io.BytesIO()
    supportingFileZip = zipfile.ZipFile(zipFileStream, 'a', zipfile.ZIP_DEFLATED, False)

    for transplantationReportFileName in supportingSpreadsheets:
        print('Adding file ' + str(transplantationReportFileName) + ' to ' + str(zipFileName))
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







