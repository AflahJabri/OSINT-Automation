import psycopg2
import shodan
import socket
from urllib.parse import urlparse
import logging

# Replace with your actual credentials
DATABASE_CONFIG = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

SHODAN_API_KEY = "mwtPvYnCIbtxXGVEhU5ZmfugoO8vtUlh"

# Configure logging
logging.basicConfig(level=logging.INFO, filename='shodan_scan.log',
                    format='%(asctime)s - %(levelname)s - %(message)s')

def get_passed_urls():
    # Retrieve company IDs and URLs that passed validation from the PostgreSQL database.
    try:
        connection = psycopg2.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        cursor.execute("SELECT id, url FROM companies WHERE kvk_check = 'PASS' AND url IS NOT NULL AND url <> ''")
        companies = cursor.fetchall()
        return companies
    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
        return []
    finally:
        if connection:
            cursor.close()
            connection.close()

def extract_hostname(url):
    # Extract the hostname from a URL.
    try:
        parsed_url = urlparse(url)
        return parsed_url.hostname
    except Exception as e:
        logging.error(f"URL parsing error for {url}: {e}")
        return None

def resolve_hostname_to_ip(hostname):
    # Resolve a hostname to its corresponding IP address.
    try:
        ip = socket.gethostbyname(hostname)
        return ip
    except socket.gaierror as e:
        logging.error(f"Hostname resolution error for {hostname}: {e}")
        return None

def scan_ip(api_key, ip):
    # Scan the IP address using the Shodan API and return metadata.
    try:
        api = shodan.Shodan(api_key)
        host = api.host(ip)
        return host
    except shodan.APIError as e:
        logging.error(f"Shodan error for IP {ip}: {e}")
        return None

def ensure_table_exists():
    # Ensure the shodan_metadata table exists, creating it if necessary.
    try:
        connection = psycopg2.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shodan_metadata (
                company_id INTEGER,
                ip VARCHAR(15),
                organization VARCHAR(255),
                operating_system VARCHAR(255),
                port INTEGER,
                banner TEXT,
                hostnames TEXT,
                country_name VARCHAR(255),
                isp VARCHAR(255),
                city VARCHAR(255),
                region VARCHAR(255),
                latitude FLOAT,
                longitude FLOAT,
                asn VARCHAR(255),
                vulnerabilities TEXT
            );
        """)
        connection.commit()
    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def store_metadata(company_id, metadata):
    # Store the extracted metadata into the PostgreSQL database.
    try:
        connection = psycopg2.connect(**DATABASE_CONFIG)
        cursor = connection.cursor()
        
        for item in metadata['data']:
            cursor.execute(
                """
                INSERT INTO shodan_metadata (company_id, ip, organization, operating_system, port, banner,
                                             hostnames, country_name, isp, city, region, latitude, longitude, asn, vulnerabilities)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (company_id, metadata['ip_str'], metadata.get('org', 'n/a'), metadata.get('os', 'n/a'), item['port'], item['data'],
                 ','.join(metadata.get('hostnames', [])), metadata.get('country_name', 'n/a'), metadata.get('isp', 'n/a'),
                 metadata.get('location', {}).get('city', 'n/a'), metadata.get('location', {}).get('region_code', 'n/a'),
                 metadata.get('location', {}).get('latitude', None), metadata.get('location', {}).get('longitude', None),
                 metadata.get('asn', 'n/a'), ','.join(metadata.get('vulns', [])))
            )
        
        connection.commit()
    except psycopg2.Error as e:
        logging.error(f"Database error: {e}")
    finally:
        if connection:
            cursor.close()
            connection.close()

def main():
    ensure_table_exists()
    
    passed_companies = get_passed_urls()
    if not passed_companies:
        logging.info("No URLs passed validation.")
        return

    for company_id, url in passed_companies:
        hostname = extract_hostname(url)
        if hostname:
            ip = resolve_hostname_to_ip(hostname)
            if ip:
                metadata = scan_ip(SHODAN_API_KEY, ip)
                if metadata:
                    store_metadata(company_id, metadata)

if __name__ == "__main__":
    main()
