import string
import requests
from sys import exc_info

def validateNmdpPortal(xmlText=None):
    # TODO: there's nothing here yet. send a message to the NMDP portal and parse response
    #curl -X POST -d @"C:\Users\ioannis\Desktop\good.hml.1.0.1.xml" -H "Content-Type: text/xml" https://qa-api.nmdp.org/hml_gw/v1/validate
    try:
        print('Inside the NMPD Portal Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        baseurl = r'https://qa-api.nmdp.org/hml_gw/v1/validate'
        headers = {
            'Content-Type': 'text/xml',
        }
        data = open(r"C:\Users\ioannis\Desktop\good.hml.1.0.1.xml", "rb")
        #udata = str(data.__format__(xmlText)).encode('utf-8')
        response = requests.post(url=baseurl, headers=headers, data=data)
        return('NMPD validation Results are the following: ' + response.text)

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))





