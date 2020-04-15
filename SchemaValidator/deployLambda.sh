rm function.zip

# Install package(s)
source /home/bmatern/schemavalidationenv/bin/activate
pip install --target ./package lxml
pip install --target ./package pyyaml
deactivate

# Zip packages
cd package
zip -r9 /home/bmatern/github/Converters/SchemaValidator/function.zip .

# Zip Script
cd ..
zip -g function.zip SchemaValidation.py

# Zip Config File
zip -g function.zip validation_config.yml

# Upload to AWS
aws lambda update-function-code --function-name validateXml --zip-file fileb://function.zip
