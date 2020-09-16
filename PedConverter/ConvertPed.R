

convertPedFile <- function(workingDirectory, bucketName, pedFilename) {
  # TODO: Return a value from this function, put it in a try-catch.
  # That way the return value can indicate "success" or some kind of error.
  
  print("Hello World! We are inside the convertPedFile Function!")
  require(kinship2)
  #require(aws.s3)
  library("aws.s3")
  bucketlist()
  #install.packages("aws.s3")
  #install.packages("xml2")
  #install.packages("libxml2-dev")

  
 
  
  # Set working directoy
  setwd(workingDirectory)
  newWorkingDirectory <- getwd()
  print(newWorkingDirectory)
  # Download the remote file to working directory 
  save_object(pedFilename, file = pedFilename, bucket = bucketName, region="eu-central-1")

  
  
  
  myData = read.table(pedFilename, header=TRUE, stringsAsFactors=FALSE)
  print('This is the data I just read:')
  print(myData)
  # TODO: Detect the column names or use a position or something. These column headers won't always work.
  myDataFixedParents <- with(myData, fixParents(Individual_ID,Paternal_ID,Maternal_ID,Sex))
  print('This is the data with fixed parents:')
  print(myDataFixedParents)

  pedAll <- with(myDataFixedParents,pedigree(id=id, dadid=dadid, momid=momid, sex=sex, missid=0))
  
  # Plot the file and write it to .pdf. Use the same filename (+.pdf)
  pdfFileName = paste0(pedFilename,'.pdf')
  pdf(pdfFileName)
  plot(pedAll)
  dev.off()
  
  
  # put local file into S3
  put_object(file = pdfFileName, object = pdfFileName, bucket = bucketName, region="eu-central-1")
  
  return('Success')
}

lambdaHandler <- function(Records)
{
  inputClass = class(Records)
  
  #library(jsonlite)
  #jsonText = paste("{Records:",Records,"}")
  
  #returnValue=class(Records)
  #s3Object=Records["s3"]
  
  #fromJsons3Object = fromJSON(s3Object)
  
  #s3ObjectNames = names(s3Object)
  #objectObject=s3Object["object"]
  
  
  #returnValue=s3Object
  #returnValue=objectObject
  #firstRecord=Records[1]
  
  #parsedJson = fromJSON(Records)
  
  #returnValue = class(s3Object)
  returnValue = inputClass
  
  #returnValue=firstRecord
  #returnValue = jsonText
  #print("This is the Json Input:")
  #print(jsonInput)
  #install.packages('kinship2')
  #print('Inside the lambda handler')
  #convertPedFile("/home/bmatern/UMCU/Test Files/PED", "ihiw-management-upload-staging", "1497_1600100387164_PED_kazu.ped.tab")
  #return(paste("Success:",returnValue))
  return(returnValue)
  
} 

RecordsInput <- '[
    {
      "eventVersion": "2.1",
      "eventSource": "aws:s3",
      "awsRegion": "eu-central-1",
      "eventTime": "2020-09-15T12:28:06.851Z",
      "eventName": "ObjectCreated:Put",
      "userIdentity": {
        "principalId": "AWS:AIDAU7VWKTLKR2Y6EIZLL"
      },
      "requestParameters": {
        "sourceIPAddress": "31.201.47.123"
      },
      "responseElements": {
        "x-amz-request-id": "6WERAV5V1TCXCR0W",
        "x-amz-id-2": "qlJTWjA8YjxzqIfr0vlLzspvT1sOXGLxwC7qCaoS444MkJfthrg1ON3InX44K5isCaPD+vguhUlBO16qbnTmzFHEAlM0b9G3"
      },
      "s3": {
        "s3SchemaVersion": "1.0",
        "configurationId": "SNSonPUT",
        "bucket": {
          "name": "ihiw-management-upload-staging",
          "ownerIdentity": {
            "principalId": "A341HYTWE9KERG"
          },
          "arn": "arn:aws:s3:::ihiw-management-upload-staging"
        },
        "object": {
          "key": "1497_1600100387164_PED_kazu.ped.tab.pdf",
          "size": 5971,
          "eTag": "5b508276f6e38773c54041c9c3e93400",
          "versionId": "_Vf9RPhv2ae4Piq_fy0Z.6UORotF426w",
          "sequencer": "005F60B35A5C93FCC0"
        }
      }
    }
  ]'

#lambdaHandler(Records=RecordsInput)

