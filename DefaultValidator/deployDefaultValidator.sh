# This script will install dependencies, bundle the lambda function, and deploy to the AWS lambda environment.
# You must have the AWS commandline environment already installed
# And you must have previously run "aws configure" to set up your machine for access to the AWS Environment.
PROJECT_PATH="/home/ben/github/Converters/DefaultValidator"
ENVIRONMENT_PATH="/home/ben/github/Converters/venv"
LAMBDA_FUNCTION="defaultValidationStaging"
#LAMBDA_FUNCTION="defaultValidationProd"

cd $PROJECT_PATH

# In case an old zip file is still here.
rm function.zip

# Zip it up
zip -g function.zip DefaultValidator.py

# Upload to AWS
aws lambda update-function-code --function-name $LAMBDA_FUNCTION --zip-file fileb://function.zip
