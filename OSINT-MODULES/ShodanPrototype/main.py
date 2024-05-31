import shodan 
 
API_KEY = "HQAaZHw77bxA65ScIJkiO84fcbMyIKlK"

api = shodan.Shodan(API_KEY)

try:
    #Search Shodan
    results = api.search('apache')

    #Show results
    print('Results found: {}'.format(results['total']))
    for result in results['matches']:
        print('IP: {}'.format(result['ip_str']))
        print(result['data'])
        print('')
except shodan.APIError as e:
    print('Error: {}'.format(e))