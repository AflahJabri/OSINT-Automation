import nmap
import psycopg2
from psycopg2 import Error

try:
    # Initialize nmap
    nmScan = nmap.PortScanner()

    # List of targets 
    targets = ['hightechcampus.com', 'asml.com', 'philips-museum.com', 'psv.nl']

    # Initialize dictionary to store scan results
    scan_results = {}

    # Initiaize scan
    for target in targets:
        print("Scanning target:", target)
        try:
            # Scan each target from the list
            nmScan.scan(hosts=target)

            # Record scan results
            scan_results[target] = {host: nmScan[host].state() for host in nmScan.all_hosts()}
            # Print scan results
            #print(scan_results[target])
        except Exception as e:
            print(f"Error scanning {target}: {e}")
            scan_results[target] = {'error':str(e)}  # Record error in the scan results

    # Connect to PostgreSQL
    conn = psycopg2.connect(
        host="localhost",
        database='nmap_scans',
        user="postgres",
        password="postgres"
    )

    with conn.cursor() as cursor:
        # Create table if it doesn't exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_results (
                id SERIAL PRIMARY KEY,
                target VARCHAR(100),
                ip_address VARCHAR(50),
                state VARCHAR(50)
            )
        """)
        
        # Insert scan results into PostgreSQL
        for target, hosts in scan_results.items():
            for host, state in hosts.items():
                try:
                 cursor.execute("INSERT INTO scan_results (target, ip_address, state) VALUES (%s, %s, %s)", (target, host, state))
                except Error as e:
                 print(f"Error inserting scan results for target {target}: {e}")

        # Commit changes to the database
        conn.commit()
        print("Scan results inserted successfully!")

except Error as e:
    print("Error connecting to PostgreSQL:", e)

except nmap.PortScannerError as e:
    print("Nmap scan error:", e)

finally:
    # Close database connection if it exists
    if 'conn' in locals() or 'conn' in globals():
        conn.close()
        print("Database connection closed.")
