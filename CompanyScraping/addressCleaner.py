import re
import psycopg2
from psycopg2 import sql

def clean_address(address):
    """
    Cleans the address to only include the street name and number.
    
    Example:
    Input: "Oude Ban 1 4285tg, Woudrichem"
    Output: "Oude Ban 1"
    """
    match = re.match(r"^(.*? \d+)", address)
    if match:
        return match.group(1).strip()
    return address

def fetch_addresses():
    """
    Fetches the list of companies and their addresses from the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id, address FROM companies")
        companies = cursor.fetchall()
        cursor.close()
        conn.close()
        return companies

    except Exception as e:
        print(f"Error fetching addresses from PostgreSQL: {e}")
        return []

def update_address(company_id, cleaned_address):
    """
    Updates the cleaned address back into the PostgreSQL database.
    """
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute(
            sql.SQL("UPDATE companies SET address = %s WHERE id = %s"),
            [cleaned_address, company_id]
        )
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Error updating address in PostgreSQL: {e}")

if __name__ == "__main__":
    # Fetch the data from the database
    companies = fetch_addresses()
    print(f"Fetched {len(companies)} companies from the database.")

    # Clean the addresses and update the database
    for company_id, address in companies:
        cleaned_address = clean_address(address)
        print(f"Original: {address}")
        print(f"Cleaned: {cleaned_address}")
        update_address(company_id, cleaned_address)
        print(f"Updated address for company ID {company_id}")
