# This script will install dependencies, bundle the lambda function, and deploy to the AWS lambda environment.
# Y must have the AWS commandline environment already installed
# And you must have previously run "aws configure" to set up your machine for access to the AWS Environment.
# Feel free to try it without activating the virtual environment (remove the line source $ENVIRONMENT_PATH"/bin/activate")
# it may or may not be necessary depending on your local python environment.
PROJECT_PATH="/home/ben/github/Converters/HAMLConverterPy"
ENVIRONMENT_PATH="/home/ben/github/Converters/venv"
LAMBDA_FUNCTION="convertCSVToHAMLStaging"
#LAMBDA_FUNCTION="convertCSVToHAMLProd"

cd $PROJECT_PATH

# In case an old zip file is still here.
rm function.zip

# Install package(s)
source $ENVIRONMENT_PATH"/bin/activate"
pip install --target ./package lxml
pip install --target ./package pyyaml
pip install --target ./package pandas
deactivate

# Zip packages
cd package
zip -r9 $PROJECT_PATH"/function.zip" .

# Zip Script
cd ..
zip -g function.zip csv_to_haml_lambda_handler.py
zip -g function.zip ihiw_converter.py
zip -j -g function.zip ../Common/IhiwRestAccess.py

# Upload to AWS
aws lambda update-function-code --function-name $LAMBDA_FUNCTION --zip-file fileb://function.zip
