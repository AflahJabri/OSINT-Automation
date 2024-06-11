import nmap
import psycopg2
from psycopg2 import Error

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        database='postgres',
        user="postgres",
        password="password"
    )
    with conn.cursor() as cursor:
        # Fetch URLs that passed the KVK check
        cursor.execute("SELECT id, url FROM companies WHERE kvk_check = 'PASS'")
        targets = cursor.fetchall()

        if not targets:
            print("No validated companies found")
        else:
            # Initialize nmap
            nmScan = nmap.PortScanner()

            # Dictionary to store scan results
            scan_results = []

            # Scan each target
            for target_id, target_url in targets:
                print("Scanning target:", target_url)
                try:
                    nmScan.scan(hosts=target_url, arguments='-sV -O')  # Added arguments for service and OS detection

                    for host in nmScan.all_hosts():
                        host_info = nmScan[host]
                        for proto in host_info.all_protocols():
                            ports = host_info[proto].keys()
                            for port in ports:
                                port_info = host_info[proto][port]
                                scan_results.append({
                                    'id': target_id,
                                    'url': target_url,
                                    'ip_address': host,
                                    'state': host_info.state(),
                                    'hostname': host_info.hostname(),
                                    'os': host_info.osmatch[0]['name'] if host_info.osmatch else None,
                                    'os_accuracy': host_info.osmatch[0]['accuracy'] if host_info.osmatch else None,
                                    'os_type': host_info.osclass[0]['type'] if host_info.osclass else None,
                                    'os_vendor': host_info.osclass[0]['vendor'] if host_info.osclass else None,
                                    'os_family': host_info.osclass[0]['osfamily'] if host_info.osclass else None,
                                    'os_gen': host_info.osclass[0]['osgen'] if host_info.osclass else None,
                                    'protocol': proto,
                                    'port': port,
                                    'port_state': port_info['state'],
                                    'service': port_info['name'],
                                    'service_version': port_info.get('version', ''),
                                    'script_output': port_info.get('script', '')
                                })

                except Exception as e:
                    print(f"Error scanning {target_url}: {e}")
                    scan_results.append({
                        'id': target_id,
                        'url': target_url,
                        'ip_address': None,
                        'state': 'error',
                        'hostname': None,
                        'os': None,
                        'os_accuracy': None,
                        'os_type': None,
                        'os_vendor': None,
                        'os_family': None,
                        'os_gen': None,
                        'protocol': None,
                        'port': None,
                        'port_state': None,
                        'service': None,
                        'service_version': None,
                        'script_output': None
                    })

        # Create a new table for storing scan results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id INT,
                url VARCHAR(255),
                ip_address VARCHAR(50),
                state VARCHAR(50),
                hostname VARCHAR(255),
                os VARCHAR(255),
                os_accuracy VARCHAR(10),
                os_type VARCHAR(50),
                os_vendor VARCHAR(50),
                os_family VARCHAR(50),
                os_gen VARCHAR(50),
                protocol VARCHAR(10),
                port INT,
                port_state VARCHAR(20),
                service VARCHAR(100),
                service_version VARCHAR(100),
                script_output TEXT,
                PRIMARY KEY (id, ip_address, port)
            )
        """)

        # Insert scan results into PostgreSQL
        for result in scan_results:
            try:
                cursor.execute(
                    """
                    INSERT INTO scan_results (
                        id, url, ip_address, state, hostname, os, os_accuracy, os_type, os_vendor, os_family, os_gen,
                        protocol, port, port_state, service, service_version, script_output
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        result['id'], result['url'], result['ip_address'], result['state'], result['hostname'],
                        result['os'], result['os_accuracy'], result['os_type'], result['os_vendor'],
                        result['os_family'], result['os_gen'], result['protocol'], result['port'],
                        result['port_state'], result['service'], result['service_version'], result['script_output']
                    )
                )
            except Error as e:
                print(f"Error inserting scan results for target {result['url']}: {e}")

        # Commit changes to the database
        conn.commit()
        print("Scan results inserted successfully!")

except Error as e:
    print("Error connecting to PostgreSQL:", e)

finally:
    # Close the database connection
    if 'conn' in locals() or 'conn' in globals():
        conn.close()
        print("Database connection closed.")
