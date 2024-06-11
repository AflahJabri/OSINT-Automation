import os
import nmap
import psycopg2
from psycopg2 import Error

# Ensure nmap is in the PATH
os.environ["PATH"] += os.pathsep + r'C:\Program Files (x86)\Nmap'

def log(message):
    print(message)

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        database='postgres',
        user="postgres",
        password="password"
    )
    log("Connected to the database.")

    with conn.cursor() as cursor:
        # Fetch URLs that passed the KVK check and are not null or empty
        cursor.execute("SELECT id, url FROM companies WHERE kvk_check = 'PASS' AND url IS NOT NULL AND url <> ''")
        targets = cursor.fetchall()
        log(f"Fetched {len(targets)} targets from the database.")

        if not targets:
            log("No valid URLs found with KVK PASS status.")
        else:
            # Initialize nmap
            nmScan = nmap.PortScanner()
            log("Initialized Nmap scanner.")

            # List to store scan results
            scan_results = []

            # Scan each target
            for target_id, target_url in targets:
                if target_url and isinstance(target_url, str):
                    log(f"Scanning target: {target_url}")
                    try:
                        nmScan.scan(hosts=target_url, arguments='-sV -O')  # Added arguments for service and OS detection

                        for host in nmScan.all_hosts():
                            host_info = nmScan[host]
                            for proto in host_info.all_protocols():
                                ports = host_info[proto].keys()
                                for port in ports:
                                    port_info = host_info[proto][port]
                                    result = {
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
                                    }
                                    scan_results.append(result)
                                    log(f"Generated scan result for {target_url}: {result}")

                    except Exception as e:
                        log(f"Error scanning {target_url}: {e}")
                        result = {
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
                            'script_output': str(e)
                        }
                        scan_results.append(result)
                        log(f"Generated error result for {target_url}: {result}")
                else:
                    log(f"Skipping invalid URL: {target_url}")
                    continue

        # Create a new table for storing scan results if it doesn't exist
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
        log("Ensured the scan_results table exists.")

        # Insert scan results into PostgreSQL
        for result in scan_results:
            try:
                log(f"Inserting result into database: {result}")
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
                log(f"Error inserting scan results for target {result['url']}: {e}")

        # Commit changes to the database
        conn.commit()
        log("Scan results inserted successfully!")

except Error as e:
    log(f"Error connecting to PostgreSQL: {e}")

finally:
    # Close the database connection
    if 'conn' in locals() or 'conn' in globals():
        conn.close()
        log("Database connection closed.")
