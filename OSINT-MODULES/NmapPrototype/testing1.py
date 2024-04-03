import nmap
import psycopg2
from psycopg2 import Error

try:
    # Initialize nmap
    nmScan = nmap.PortScanner()

    # List of targets 
    targets = ['psv.nl', 'hightechcampus.com', 'asml.com', 'philips-museum.com']

    # Initiaize scan
    for target in targets:
        # Scan each target from the list
        nmScan.scan(hosts=target)

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        database='nmap_scans',
        user="postgres",
        password="postgres"
    )

    with conn.cursor() as cursor:
        # Insert scan results into PostgreSQL
        for host in nmScan.all_hosts():
            state = nmScan[host].state()
            cursor.execute("INSERT INTO scan_results (ip_address, state) VALUES (%s, %s)", (host, state))
        conn.commit()

except Error as e:
    print("Error connecting to PostgreSQL:", e)

except nmap.PortScannerError as e:
    print("Nmap scan error:", e)

finally:
    # Close database connection
    if 'conn' in locals() or 'conn' in globals():
        conn.close()
        print("Done!")