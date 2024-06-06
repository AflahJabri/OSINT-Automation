import whois
import socket
import requests
import psycopg2

# List of URLs for proof of concept
urls = ["https://www.asml.com", "https://www.philips.com", "https://www.nextbestbarber.com"]

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
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    return parsed_url.netloc

# Function to get WHOIS information
def get_whois_info(domain):
    try:
        w = whois.whois(domain)
        return w
    except Exception as e:
        print(f"Failed to retrieve WHOIS for {domain}: {e}")
        return None

# Function to geolocate IP address
def geolocate_ip(ip):
    try:
        response = requests.get(f"https://geolocation-db.com/json/{ip}&position=true").json()
        return response
    except Exception as e:
        print(f"Failed to geolocate IP {ip}: {e}")
        return None

# Function to save results to PostgreSQL
def save_to_db(conn, data):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS urls_info (
                id SERIAL PRIMARY KEY,
                url TEXT,
                ip TEXT,
                country_name TEXT,
                state TEXT,
                city TEXT
            )
        """)
        insert_query = """
            INSERT INTO url_info (url, ip, country_name, state, city)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.executemany(insert_query, data)
        conn.commit()

# Main function to process URLs
def process_urls(urls, db_config):
    conn = psycopg2.connect(**db_config)
    results = []
    
    for url in urls:
        domain = extract_domain(url)
        whois_info = get_whois_info(domain)
        
        if not whois_info or 'registrar' not in whois_info:
            print(f"No WHOIS information for {domain}")
            continue
        
        try:
            ip = socket.gethostbyname(domain)
        except socket.gaierror as e:
            print(f"Could not resolve domain {domain}: {e}")
            continue
        
        geolocation = geolocate_ip(ip)
        
        if geolocation:
            result = (
                url,
                ip,
                geolocation.get('country_name'),
                geolocation.get('state'),
                geolocation.get('city')
            )
            results.append(result)
            print(f"Processed {url}: {result}")
        else:
            print(f"Could not geolocate IP for {url}")

    save_to_db(conn, results)
    conn.close()

# Run the proof of concept
process_urls(urls, db_config)
