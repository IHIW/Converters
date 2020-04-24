from sys import exc_info

def validateMiring(xmlText=None):
    # TODO: there's nothing here yet. send a message to miring.b12x.org and get a response.
    try:
        print('Inside the MIRING Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        return('MIRING validation Results')

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))
