import nmap
import psycopg2
from psycopg2 import Error
import logging
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_to_database():
    return psycopg2.connect(
        host="localhost",
        database='postgres',
        user="postgres",
        password="password"
    )

def fetch_targets(cursor):
    cursor.execute("""
        SELECT id, url 
        FROM companies 
        WHERE kvk_check = 'PASS' 
        AND url IS NOT NULL 
        AND url <> '' 
        AND url <> 'None'
    """)
    targets = cursor.fetchall()
    logging.info(f"Fetched {len(targets)} targets from the database.")
    return targets

def initialize_nmap():
    return nmap.PortScanner()

def get_domain_from_url(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc

def scan_target(nmScan, target_id, target_url):
    domain = get_domain_from_url(target_url)
    try:
        nmScan.scan(hosts=domain, arguments='-sV -O')
        results = []
        for host in nmScan.all_hosts():
            host_info = nmScan[host]
            osmatch = host_info.get('osmatch', [])
            osclass = host_info.get('osclass', [])
            for proto in host_info.all_protocols():
                ports = host_info[proto].keys()
                for port in ports:
                    port_info = host_info[proto][port]
                    results.append({
                        'id': target_id,
                        'url': target_url,
                        'ip_address': host,
                        'state': host_info.state(),
                        'hostname': host_info.hostname(),
                        'os': osmatch[0]['name'] if osmatch else None,
                        'os_accuracy': osmatch[0]['accuracy'] if osmatch else None,
                        'os_type': osclass[0]['type'] if osclass else None,
                        'os_vendor': osclass[0]['vendor'] if osclass else None,
                        'os_family': osclass[0]['osfamily'] if osclass else None,
                        'os_gen': osclass[0]['osgen'] if osclass else None,
                        'protocol': proto,
                        'port': port,
                        'port_state': port_info['state'],
                        'service': port_info['name'],
                        'service_version': port_info.get('version', ''),
                        'script_output': port_info.get('script', '')
                    })
        logging.info(f"Scan results for target {target_url}: {results}")
        return results
    except Exception as e:
        logging.error(f"Error scanning {target_url}: {e}")
        return [{
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
        }]

def create_scan_results_table(cursor):
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
    logging.info("Scan results table created or already exists.")

def insert_scan_results(cursor, results):
    for result in results:
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
            logging.info(f"Inserted scan result for target {result['url']}.")
        except Error as e:
            logging.error(f"Error inserting scan results for target {result['url']}: {e}")

def main():
    try:
        conn = connect_to_database()
        with conn.cursor() as cursor:
            targets = fetch_targets(cursor)
            if not targets:
                logging.info("No validated companies found")
                return

            nmScan = initialize_nmap()
            scan_results = []

            for target_id, target_url in targets:
                logging.info(f"Scanning target: {target_url}")
                scan_results.extend(scan_target(nmScan, target_id, target_url))

            create_scan_results_table(cursor)
            insert_scan_results(cursor, scan_results)
            conn.commit()
            logging.info("Scan results inserted successfully!")
    except Error as e:
        logging.error(f"Error connecting to PostgreSQL: {e}")
    finally:
        if 'conn' in locals() or 'conn' in globals():
            conn.close()
            logging.info("Database connection closed.")

if __name__ == "__main__":
    main()
