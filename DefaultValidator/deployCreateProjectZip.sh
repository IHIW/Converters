# This script will install dependencies, bundle the lambda function, and deploy to the AWS lambda environment.
# You must have the AWS commandline environment already installed
# And you must have previously run "aws configure" to set up your machine for access to the AWS Environment.
PROJECT_PATH="/home/ben/github/Converters/DefaultValidator"
ENVIRONMENT_PATH="/home/ben/github/Converters/venv"
LAMBDA_FUNCTION="zipProjectFilesStaging"
#LAMBDA_FUNCTION="zipProjectFilesStagingProd"

cd $PROJECT_PATH

# In case an old zip file is still here.
rm function.zip

# Install package(s)
source $ENVIRONMENT_PATH"/bin/activate"
pip install --target ./package pyyaml

# Zip packages
cd package
zip -r9 $PROJECT_PATH"/function.zip" .

# Zip it up
cd ..
zip -g function.zip CreateProjectZip.py
zip -j -g function.zip ../Common/IhiwRestAccess.py
zip -j -g function.zip ../Common/S3_Access.py

# Upload to AWS
aws lambda update-function-code --function-name $LAMBDA_FUNCTION --zip-file fileb://function.zip
