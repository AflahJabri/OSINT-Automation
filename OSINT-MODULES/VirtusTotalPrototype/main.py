import requests
import psycopg2
import time
from urllib.parse import urlparse, quote

# PostgreSQL connection details
db_config = {
    'dbname': 'postgres',
    'user': 'postgres',
    'password': 'password',
    'host': 'localhost',
    'port': '5432'
}

# VirusTotal Public API key
virustotal_api_key = '975d1bead13442d3d7107e3ce5ede37cfc5d6062cbd6d9fd5ff9f98b8f2db2a4'

# Function to extract domain from URL
def extract_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc

# Function to get VirusTotal report
def get_virustotal_report(url):
    headers = {
        'x-apikey': virustotal_api_key
    }
    url_id = quote(url, safe='')
    response = requests.get(f'https://www.virustotal.com/api/v3/urls/{url_id}', headers=headers)
    if response.status_code == 200:
        return response.json()
    elif response.status_code == 404:
        # URL not found, submit the URL
        submission_response = requests.post(
            'https://www.virustotal.com/api/v3/urls',
            headers=headers,
            data={'url': url}
        )
        if submission_response.status_code == 200:
            print(f"Submitted {url} to VirusTotal for scanning.")
            return None
        else:
            print(f"Failed to submit {url} to VirusTotal: {submission_response.status_code} - {submission_response.text}")
            return None
    else:
        print(f"Failed to retrieve VirusTotal report for {url}: {response.status_code} - {response.text}")
        return None

# Function to create the VirusTotal results table if it does not exist
def create_virustotal_table_if_not_exists(conn):
    with conn.cursor() as cursor:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS virustotal_info (
                id SERIAL PRIMARY KEY,
                url TEXT,
                virustotal_report JSON
            )
        """)
        conn.commit()

# Function to save VirusTotal results to PostgreSQL
def save_virustotal_to_db(conn, data):
    create_virustotal_table_if_not_exists(conn)
    with conn.cursor() as cursor:
        insert_query = """
            INSERT INTO virustotal_info (url, virustotal_report)
            VALUES (%s, %s)
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
        virustotal_report = get_virustotal_report(url)
        if not virustotal_report:
            # Wait and retry fetching the report
            for _ in range(3):  # Retry up to 3 times
                print(f"Waiting to retry fetching report for {url}...")
                time.sleep(30)  # Wait for 30 seconds before retrying
                virustotal_report = get_virustotal_report(url)
                if virustotal_report:
                    break

        if virustotal_report:
            result = (
                url,
                virustotal_report
            )
            results.append(result)
            print(f"Processed {url}: {result}")
        else:
            print(f"Could not retrieve VirusTotal report for {url}")

    save_virustotal_to_db(conn, results)
    conn.close()

# Run the VirusTotal processing
process_urls(db_config)
