import nmap
import psycopg2

#initialize nmap 
nmScan = nmap.PortScanner()

#Scan PSV.nl 
nmScan.scan('psv.nl', '80,443,21,8080')

#Connect to PostgreSQL 
conn = psycopg2.connect(
    host="localhost",
    database='nmap_scans',
    user="postgres",
    password="postgres"
)

#insert scan results into postgres
for host in nmScan.all_hosts():
    state = nmScan[host].state()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO scan_results (hostname, state) VALUES (%s, %s)", (host, state))
    conn.commit()

#close database connection
conn.close()
