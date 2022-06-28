import argparse
from os import makedirs
from sys import exc_info
from os.path import join, isdir

from Common.IhiwRestAccess import getCredentials, getUrl, getToken, getFilteredUploads
from Common.S3_Access import getFileSize


def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--task", required=True, help="task to perform", type=str)
    parser.add_argument("-b", "--bucket", required=True, help="S3 Bucket Name", type=str )
    parser.add_argument("-o", "--output", required=True, help="Output Folder", type=str)

    return parser.parse_args()


def writeData(allUploadData=None, outputDirectory=None, delimiter = ',', newline = '\n'):
    outputFileName = join(outputDirectory, 'AllUploadAnalysis.csv')

    print('Writing output file:' + str(outputFileName))

    if not isdir(outputDirectory):
        makedirs(outputDirectory)

    with open(outputFileName, 'w') as outputFile:
        headerLine = delimiter.join(['Upload_ID','Filename','Project','Type','Size','LabName'])
        outputFile.write(headerLine + newline)

        for projectId in allUploadData.keys():
            for uploadId in allUploadData[projectId].keys():
                uploadData = allUploadData[projectId][uploadId]
                dataLine = delimiter.join([str(uploadId), str(uploadData['fileName']).replace(',',';'), str(uploadData['projectName']).replace(',',';')
                    , str(uploadData['type']), str(uploadData['fileSizeKb']), str(uploadData['submitterLab']).replace(',',';')])
                outputFile.write(dataLine + newline)

    countsPerProject = {}
    countsPerLab = {}
    countsPerUploadType = {}
    fileSizePerProject = {}
    fileSizePerLab = {}
    fileSizePerUploadType = {}

    for projectId in allUploadData.keys():
        for uploadId in allUploadData[projectId].keys():
            uploadData = allUploadData[projectId][uploadId]

            if(uploadData['projectName'] not in countsPerProject.keys()):
                countsPerProject[uploadData['projectName']] = 0
                fileSizePerProject[uploadData['projectName']] = 0

            if(uploadData['submitterLab'] not in countsPerLab.keys()):
                countsPerLab[uploadData['submitterLab']] = 0
                fileSizePerLab[uploadData['submitterLab']] = 0

            if(uploadData['type'] not in countsPerUploadType.keys()):
                countsPerUploadType[uploadData['type']] = 0
                fileSizePerUploadType[uploadData['type']] = 0

            try:
                countsPerProject[uploadData['projectName']] += 1
                fileSizePerProject[uploadData['projectName']] += float(uploadData['fileSizeKb'])

                countsPerLab[uploadData['submitterLab']] += 1
                fileSizePerLab[uploadData['submitterLab']] += float(uploadData['fileSizeKb'])

                countsPerUploadType[uploadData['type']] += 1
                fileSizePerUploadType[uploadData['type']] += float(uploadData['fileSizeKb'])


            except Exception as e:
                print('Problem updating the allUploadSummaryData:') + str(e)

    outputFileName = join(outputDirectory, 'UploadsSummary.csv')
    print('Writing output file:' + str(outputFileName))
    with open(outputFileName, 'w') as outputFile:
        headerLine = delimiter.join(['Lab','Upload_Count','Total_File_Size(Kb)','Total_File_Size(Mb)'])
        outputFile.write(headerLine + newline)
        for labName in countsPerLab.keys():
            dataLine = delimiter.join([str(labName).replace(',',';')
                , str(countsPerLab[labName])
                ,str(fileSizePerLab[labName])
                ,str(float(fileSizePerLab[labName])/1024)])
            outputFile.write(dataLine + newline)

        outputFile.write(newline + newline)

        headerLine = delimiter.join(['Project','Upload_Count','Total_File_Size(Kb)','Total_File_Size(Mb)'])
        outputFile.write(headerLine + newline)
        for projectName in countsPerProject.keys():
            dataLine = delimiter.join([str(projectName).replace(',',';')
                , str(countsPerProject[projectName])
                ,str(fileSizePerProject[projectName])
                ,str(float(fileSizePerProject[projectName])/1024)])
            outputFile.write(dataLine + newline)


        outputFile.write(newline + newline)

        headerLine = delimiter.join(['Type','Upload_Count','Total_File_Size(Kb)','Total_File_Size(Mb)'])
        outputFile.write(headerLine + newline)
        for uploadType in countsPerUploadType.keys():
            dataLine = delimiter.join([str(uploadType).replace(',',';')
                , str(countsPerUploadType[uploadType])
                ,str(fileSizePerUploadType[uploadType])
                ,str(float(fileSizePerUploadType[uploadType])/1024)])
            outputFile.write(dataLine + newline)


def analyzeIhiwUploads(args=None, allProjectIds=None):
    print('Analyzing All uploads')

    (user, password) = getCredentials(configFileName='validation_config.yml')
    url = getUrl(configFileName='validation_config.yml')
    token = getToken(user=user, password=password, url=url)

    allUploadData = {}

    for projectIdIndex, projectId in enumerate(allProjectIds):
        print('Checking Project ID:' + str(projectId) + ' : ' + str(projectIdIndex + 1) + '/' + str(len(allProjectIds)))
        projectUploads = getFilteredUploads(projectIDs=[projectId], token=token, url=url)
        print('for project ' + str(projectId) + ' i found ' + str(len(projectUploads)) + ' uploads.')
        projectData = {}

        for uploadIndex, projectUpload in enumerate(projectUploads):
            print('Project:' + str(projectId) + ' : ' + str(projectIdIndex + 1) + '/' + str(len(allProjectIds)) + ' Upload: ' + str(uploadIndex+1) + '/' + str(len(projectUploads)))
            uploadData = {}
            try:
                uploadData['id']= projectUpload['id']
                uploadData['type'] = projectUpload['type']
                uploadData['fileName'] = projectUpload['fileName']
                uploadData['submitterLab'] = projectUpload['createdBy']['lab']['department'] + ' : '+ projectUpload['createdBy']['lab']['institution']
                uploadData['projectName'] = projectUpload['project']['name']
                uploadData['fileSizeKb'] = getFileSize(bucket=args.bucket, uploadFilename=uploadData['fileName'])
            except Exception as e:
                print('Warning: could not get info on file: ' + str(projectUpload['id']))
                print(e)
                uploadData['fileSizeKb'] = 0.0
            projectData[uploadData['id']] = uploadData

        allUploadData[projectId] = projectData

    writeData(allUploadData=allUploadData, outputDirectory=args.output)

if __name__ == '__main__':
    print('Testing Rest Methods')

    try:
        args=parseArgs()
        task =args.task

        allProjectIds = [141,302,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404]

        print('Task=' + str(task))
        if(task== 'ANALYZE_IHIW_UPLOADS'):
            analyzeIhiwUploads(args=args, allProjectIds=allProjectIds)
        else:
            print('I do not understand which task to perform')

    except Exception:
        print ('Unexpected problem running tests:')
        print (str(exc_info()))
        raise
