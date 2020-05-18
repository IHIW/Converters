from sys import exc_info

def validateHaml(xmlText=None):
    # TODO: there's nothing here yet. Maybe just do a schema validation on a haml file?
    try:
        print('Inside the HAML Validator, i was given xml text that looks like: ' + str(xmlText)[0:100])
        return('HAML validation Results')

    except Exception as e:
        print('Unexpected problem during xml validation.')
        print(str(e))
        print(exc_info())
        return (str(e) + '\n' + str(exc_info()))
