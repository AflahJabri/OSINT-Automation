import shodan

API_KEY = "HQAaZHw77bxA65ScIJkiO84fcbMyIKlK"

api = shodan.Shodan(API_KEY)


# Lookup the host (nextbestbarber)
host = api.host('88.214.28.132')

# Print general info
print("""
        IP: {}
        Organization: {}
        Operating System: {}
""".format(host['ip_str'], host.get('org', 'n/a'), host.get('os', 'n/a')))

# Print all banners
for item in host['data']:
        print("""
                Port: {}
                Banner: {}

        """.format(item['port'], item['data']))