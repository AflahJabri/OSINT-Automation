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
conn = psycopg2.connect(**db_config)
cur = conn.cursor()

# Fetch URLs from the database
cur.execute("SELECT id, url FROM companies WHERE kvk_check = 'PASS' AND url IS NOT NULL AND url <> ''")
urls = cur.fetchall()

# SpiderFoot API settings
sf_base_url = 'http://127.0.0.1:5001'
sf_api_url = f'{sf_base_url}/api/v1'

# Function to start a SpiderFoot scan
def start_scan(target):
    payload = {
        'target': target,
        'modules': 'all',  # Use 'all' for all modules without API keys
        'scanname': f'Scan for {target}',
        'usecase': 'reconnaissance'
    }
    response = requests.post(f'{sf_api_url}/scan/new', json=payload)
    return response.json()

# Function to get scan results
def get_scan_results(scan_id):
    response = requests.get(f'{sf_api_url}/scan/results/{scan_id}')
    return response.json()

# Run scans for each URL and print results
for url in urls:
    url = url[0]
    print(f'Starting scan for {url}')
    scan_response = start_scan(url)
    
    scan_id = scan_response.get('scan_id')
    if scan_id:
        print(f'Started scan with ID: {scan_id}')
        # Wait for some time before fetching results
        time.sleep(10)
        
        # Fetch scan results
        results = get_scan_results(scan_id)
        print(json.dumps(results, indent=2))
    else:
        print(f'Failed to start scan for {url}: {scan_response.get("error", "Unknown error")}')
    time.sleep(1)  # To avoid overwhelming the server with requests

# Close database connection
cur.close()
conn.close()
