

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


lambdaHandler <- function(jsonInput) {
  print("This is the Json Input:")
  print(jsonInput)
  #install.packages('kinship2')
  print('Inside the lambda handler')
  convertPedFile("/home/bmatern/UMCU/Test Files/PED", "ihiw-management-upload-staging", "1497_1600100387164_PED_kazu.ped.tab")
  return('Successful lambda handler.')
  
} 

#lambdaHandler()

