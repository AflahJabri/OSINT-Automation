
#Stream SSL certs collected by Shodan in realtime.

import shodan
import sys

# Configuration
API_KEY = 'HQAaZHw77bxA65ScIJkiO84fcbMyIKlK'

try:
    # Setup the api
    api = shodan.Shodan(API_KEY)

    print ('Listening for certs...')
    for banner in api.stream.ports([443, 8443]):
                if 'ssl' in banner:
                        # Print out all the SSL information that Shodan has collected
                        print(banner['ssl'])

except Exception as e:
    print('Error: {}'.format(e))
    sys.exit(1)