# This script will install dependencies, bundle the lambda function, and deploy to the AWS lambda environment.
# Y must have the AWS commandline environment already installed
# And you must have previously run "aws configure" to set up your machine for access to the AWS Environment.
# You need to provide the config file validation_config.yml with entries url: {} username: {} password: {}
# Feel free to try it without activating the virtual environment (remove the line source $ENVIRONMENT_PATH"/bin/activate")
# it may or may not be necessary depending on your local python environment.
PROJECT_PATH="/home/bmatern/github/Converters/XmlValidator"
ENVIRONMENT_PATH="/home/bmatern/github/Converters/venv"
HANDLER_FILE="NmdpPortalValidation.py"
LAMBDA_FUNCTION="validateXmlNMDPStaging"
#LAMBDA_FUNCTION="validateXmlNMDPProd"

cd $PROJECT_PATH

# In case an old zip file is still here.
rm function.zip

# Install package(s)
source $ENVIRONMENT_PATH"/bin/activate"
pip install --target ./package lxml
pip install --target ./package pyyaml
deactivate

# Zip packages
cd package
zip -r9 $PROJECT_PATH"/function.zip" .

# Zip Script
cd ..
zip -g function.zip $HANDLER_FILE

# Zip Config File
zip -g function.zip validation_config.yml

# Add Common Files
cd ..
zip -g XmlValidator/function.zip Common/IhiwRestAccess.py
cd XmlValidator

# Upload to AWS
aws lambda update-function-code --function-name $LAMBDA_FUNCTION --zip-file fileb://function.zip