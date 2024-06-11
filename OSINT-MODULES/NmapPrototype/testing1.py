import nmap

# Initialize the PortScanner
nm = nmap.PortScanner()

# Scan localhost
nm.scan('127.0.0.1', '22-443')

# Print scan results
print(nm.all_hosts())
for host in nm.all_hosts():
    print(f'Host: {host} ({nm[host].hostname()})')
    print(f'State: {nm[host].state()}')
    for proto in nm[host].all_protocols():
        print(f'Protocol: {proto}')
        lport = nm[host][proto].keys()
        for port in lport:
            print(f'Port: {port}\tState: {nm[host][proto][port]["state"]}')
