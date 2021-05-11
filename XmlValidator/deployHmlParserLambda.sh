# This script will install dependencies, bundle the lambda function, and deploy to the AWS lambda environment.
# Y must have the AWS commandline environment already installed
# And you must have previously run "aws configure" to set up your machine for access to the AWS Environment.
# You need to provide the config file validation_config.yml with entries url: {} username: {} password: {}
# Feel free to try it without activating the virtual environment (remove the line source $ENVIRONMENT_PATH"/bin/activate")
# it may or may not be necessary depending on your local python environment.
PROJECT_PATH="/home/bmatern/github/Converters/XmlValidator"
ENVIRONMENT_PATH="/home/bmatern/github/Converters/venv"
HANDLER_FILE="HmlGlStringParser.py"
LAMBDA_FUNCTION="parseHmlStaging"
#LAMBDA_FUNCTION="parseHmlProd"

cd $PROJECT_PATH

# In case an old zip file is still here.
rm function.zip

# Install package(s)
source $ENVIRONMENT_PATH"/bin/activate"
pip install --target ./package lxml
pip install --target ./package pyyaml
#pip install -Iv --target ./package biopython==1.71
#pip install -Iv --target ./package numpy==1.14.2
pip install --target ./package git+https://github.com/nmdp-bioinformatics/pyglstring
#pip install --target ./package pyhml
deactivate

# Zip packages
cd package
zip -r9 $PROJECT_PATH"/function.zip" .

# Zip Script
cd ..
zip -g function.zip $HANDLER_FILE
zip -j -g function.zip ../Common/IhiwRestAccess.py
zip -j -g function.zip ../Common/Validation.py
zip -j -g function.zip ../Common/ParseXml.py


# Zip Config File
zip -g function.zip validation_config.yml

# Upload to AWS
aws lambda update-function-code --function-name $LAMBDA_FUNCTION --zip-file fileb://function.zip
