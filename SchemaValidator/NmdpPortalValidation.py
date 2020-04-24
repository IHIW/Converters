from sys import exc_info

def validateNmdpPortal(xmlText=None):
    # TODO: there's nothing here yet. send a message to the NMDP portal and parse response
    try:
        print('Inside the NMPD Portal Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        return('NMPD validation Results')

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))

