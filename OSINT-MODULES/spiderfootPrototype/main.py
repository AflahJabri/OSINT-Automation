import psycopg2
import requests
import time
import json

# Database connection settings
db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

# Connect to PostgreSQL
try:
    conn = psycopg2.connect(**db_config)
    cur = conn.cursor()
    print("Database connection established.")
except psycopg2.Error as e:
    print(f"Error connecting to database: {e}")
    exit()

# Fetch URLs from the database
try:
    cur.execute("SELECT ip FROM url_info")
    urls = cur.fetchall()
    print(f"Fetched {len(urls)} URLs from the database.")
except psycopg2.Error as e:
    print(f"Error fetching URLs from database: {e}")
    conn.close()
    exit()

# SpiderFoot API settings
sf_base_url = 'http://127.0.0.1:5001'
sf_api_url = 'https://api.bgpview.io/ip/ip_address'

# Function to start a SpiderFoot scan
def start_scan(target):
    payload = {
        'target': target,
        'modules': 'abuse.ch',  # Use 'all' for all modules without API keys
        'scanname': f'Scan for {target}',
        'usecase': 'reconnaissance'
    }
    try:
        response = requests.post(f'{sf_api_url}/scan/new', json=payload)
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Error starting scan for {target}: {e}")
        if response.text:
            print(f"Response text: {response.text}")
        return None

# Function to get scan results
def get_scan_results(scan_id):
    try:
        response = requests.get(f'{sf_api_url}/scan/results/{scan_id}')
        response.raise_for_status()  # Raise an error for bad status codes
        return response.json()
    except requests.RequestException as e:
        print(f"Error fetching scan results for ID {scan_id}: {e}")
        return None

# Run scans for each URL and print results
for url in urls:
    url = url[0]
    print(f'Starting scan for {url}')
    scan_response = start_scan(url)
    
    if scan_response and 'scan_id' in scan_response:
        scan_id = scan_response['scan_id']
        print(f'Started scan with ID: {scan_id}')
        # Wait for some time before fetching results
        time.sleep(30)  # Increased to give the scan more time
        
        # Fetch scan results
        results = get_scan_results(scan_id)
        if results:
            print(json.dumps(results, indent=2))
        else:
            print(f'No results for scan ID {scan_id}')
    else:
        if scan_response:
            print(f'Failed to start scan for {url}: {scan_response.get("error", "Unknown error")}')
        else:
            print(f'Failed to start scan for {url}: No response from SpiderFoot API')
    time.sleep(1)  # To avoid overwhelming the server with requests

# Close database connection
cur.close()
conn.close()
print("Database connection closed.")
