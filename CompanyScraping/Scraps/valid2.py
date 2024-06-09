import time
import logging
import re
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_companies():
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, address FROM companies")
        companies = cursor.fetchall()
        cursor.close()
        conn.close()
        return companies

    except Exception as e:
        logging.error(f"Error fetching companies from PostgreSQL: {e}")
        return []

def extract_street_name(full_address):
    # Extracts the street name from the full address.
    # Assuming the street name is the part of the address before the first comma or numeric sequence.
    match = re.match(r"^([\w\s]+ \d+)", full_address)
    if match:
        return match.group(1).strip()
    return full_address.strip()

def search_kvk(driver, name):
    try:
        logging.info(f"Searching KVK for {name}")
        driver.get("https://www.kvk.nl/zoeken")
        
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[type="search"][placeholder="Search kvk.nl"]'))
        )
        search_box.clear()
        search_box.send_keys(name)
        search_box.send_keys(u'\ue007')  # Press Enter key

        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-ui-test-class="search-results-list"]'))
        )
        time.sleep(5)  # Wait for results to load completely
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        company_elements = soup.select('ul[data-ui-test-class="search-results-list"] > li')

        for company in company_elements:
            company_name_tag = company.find('a', class_='TextLink-module_textlink__1SZwI')
            company_address_tag = company.find('li', class_='icon-locationLargeIcon')
            font_tag = company_address_tag.find('font')

            if company_name_tag and company_address_tag:
                company_name = company_name_tag.get_text(strip=True)
                company_address = font_tag.get_text(strip=True)
                logging.info(f"Found company: {company_name}, Address: {company_address}")
                return company_name, company_address

        logging.info(f"No matching company found on KVK for {name}")
        return None, None
    except TimeoutException:
        logging.error(f"Error searching KVK for {name}")
        return None, None

def update_kvk_check(company_id, status):
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
            "UPDATE companies SET kvk_check = %s WHERE id = %s",
            (status, company_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Updated KVK check for company ID {company_id} to {status}")

    except Exception as e:
        logging.error(f"Error updating kvk_check in PostgreSQL: {e}")

if __name__ == "__main__":
    # Configure Selenium WebDriver
    chrome_options = Options()
    # Remove headless mode
    # chrome_options.add_argument("--headless")  # Comment out or remove this line
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--disable-logging")
    chrome_options.add_argument("--allow-running-insecure-content")

    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    # Fetch the data from the database
    companies = fetch_companies()
    logging.info(f"Fetched {len(companies)} companies from the database.")
    
    # Validate the addresses and update the database
    for company_id, name, address in companies:
        retries = 3
        for attempt in range(retries):
            try:
                kvk_name, kvk_address = search_kvk(driver, name)
                if kvk_address:
                    db_street = extract_street_name(address)
                    kvk_street = extract_street_name(kvk_address)
                    logging.info(f"Database street: {db_street.lower()}")
                    logging.info(f"KVK street: {kvk_street.lower()}")
                    if db_street.lower() == kvk_street.lower():
                        update_kvk_check(company_id, "PASS")
                        logging.info(f"Company {name} with ID {company_id} passed the KVK check.")
                        break
                    else:
                        update_kvk_check(company_id, "FAIL")
                        logging.info(f"Company {name} with ID {company_id} failed the KVK check.")
                        break
                else:
                    update_kvk_check(company_id, "FAIL")
                    logging.info(f"Company {name} with ID {company_id} failed the KVK check.")
                    break
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed for company {name} with error: {e}")
                if attempt < retries - 1:
                    logging.info(f"Retrying ({attempt + 2}/{retries})...")
                else:
                    logging.error(f"All {retries} attempts failed for company {name}")

    driver.quit()
