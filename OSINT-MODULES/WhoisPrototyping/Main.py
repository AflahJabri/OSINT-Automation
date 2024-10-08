import whois
import socket
import requests
import psycopg2
from urllib.parse import urlparse
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PostgreSQL connection details
db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

# Function to extract domain from URL
def extract_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc

# Function to get WHOIS information
def get_whois_info(domain):
    try:
        w = whois.whois(domain)
        return w
    except Exception as e:
        logging.error(f"Failed to retrieve WHOIS for {domain}: {e}")
        return None

# Function to geolocate IP address
def geolocate_ip(ip):
    try:
        response = requests.get(f"https://geolocation-db.com/json/{ip}&position=true").json()
        return response
    except Exception as e:
        logging.error(f"Failed to geolocate IP {ip}: {e}")
        return None

# Function to create the table if it does not exist
def create_table_if_not_exists(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS url_info (
                id SERIAL PRIMARY KEY,
                url TEXT,
                ip TEXT,
                country_name TEXT,
                state TEXT,
                city TEXT,
                latitude FLOAT,
                longitude FLOAT,
                continent TEXT,
                postal TEXT,
                registrar TEXT,
                creation_date TIMESTAMP,
                expiration_date TIMESTAMP,
                updated_date TIMESTAMP,
                organization TEXT,
                whois_country TEXT,
                whois_state TEXT,
                whois_city TEXT,
                whois_email TEXT,
                whois_phone TEXT
            )
        """)
        conn.commit()

# Function to save results to PostgreSQL
def save_to_db(conn, data):
    create_table_if_not_exists(conn)
    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO url_info (
                url, ip, country_name, state, city, latitude, longitude, continent, postal,
                registrar, creation_date, expiration_date, updated_date, organization, whois_country,
                whois_state, whois_city, whois_email, whois_phone
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, data)
        conn.commit()

# Function to fetch URLs from companies table
def fetch_urls_from_db(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            SELECT url FROM companies WHERE kvk_check = 'PASS' AND url IS NOT NULL AND url != ''
        """)
        rows = cursor.fetchall()
        return [row[0] for row in rows]

# Main function to process URLs
def process_urls(db_config):
    conn = psycopg2.connect(**db_config)
    urls = fetch_urls_from_db(conn)
    results = []

    for url in urls:
        domain = extract_domain(url)
        whois_info = get_whois_info(domain)
        
        if not whois_info:
            logging.info(f"No WHOIS information for {domain}")
            continue
        
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror as e:
            logging.error(f"Could not resolve domain {domain}: {e}")
            continue
        
        geolocation = geolocate_ip(ip)
        
        if geolocation:
            creation_date = whois_info.creation_date
            expiration_date = whois_info.expiration_date
            updated_date = whois_info.updated_date
            
            if isinstance(creation_date, list):
                creation_date = creation_date[0]
            if isinstance(expiration_date, list):
                expiration_date = expiration_date[0]
            if isinstance(updated_date, list):
                updated_date = updated_date[0]

            result = (
                url,
                ip,
                geolocation.get('country_name'),
                geolocation.get('state'),
                geolocation.get('city'),
                geolocation.get('latitude'),
                geolocation.get('longitude'),
                geolocation.get('continent_name'),
                geolocation.get('postal'),
                whois_info.registrar,
                creation_date,
                expiration_date,
                updated_date,
                whois_info.org,
                whois_info.country,
                whois_info.state,
                whois_info.city,
                whois_info.emails[0] if whois_info.emails else None,
                whois_info.phone[0] if whois_info.phone else None
            )
            results.append(result)
            logging.info(f"Processed {url}: {result}")
        else:
            logging.info(f"Could not geolocate IP for {url}")

    save_to_db(conn, results)
    conn.close()

# Run the proof of concept
process_urls(db_config)
