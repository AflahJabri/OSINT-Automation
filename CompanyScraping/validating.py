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
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, WebDriverException

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
    match = re.match(r"^([\w\s]+ \d+)", full_address)
    if match:
        return match.group(1).strip()
    return full_address.strip()

def accept_cookies(driver):
    try:
        accept_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-ui-test-class="toestemming"][name="Opslaan"]'))
        )
        accept_button.click()
        logging.info("Accepted cookies successfully.")
    except (TimeoutException, NoSuchElementException, ElementClickInterceptedException):
        logging.warning("Could not find or click the accept cookies button. Continuing without accepting cookies.")

def search_kvk(driver, name, address):
    try:
        logging.info(f"Searching KVK for {name}, {address}")
        driver.get("https://www.kvk.nl/zoeken")

        accept_cookies(driver)

        time.sleep(3)

        try:
            active_element = driver.switch_to.active_element
            active_element.send_keys(Keys.CONTROL + "a")
            active_element.send_keys(Keys.DELETE)
            logging.info("Cleared the search bar.")

            search_query = f"{name} {address}"
            active_element.send_keys(search_query)
            logging.info(f"Typed '{search_query}' into the search bar.")

            active_element.send_keys(u'\ue007')

        except Exception as e:
            logging.error('Failed to type into the search bar or press Enter')
            logging.error(e)
            return None, None, None, None

        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'ul[data-ui-test-class="search-results-list"]'))
        )
        logging.info("Search results are loaded.")

        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        company_elements = soup.select('ul[data-ui-test-class="search-results-list"] > li')

        for company in company_elements:
            company_name_tag = company.find('a', class_='TextLink-module_textlink__1SZwI')
            company_address_tag = company.find('li', class_='icon-locationLargeIcon')
            kvk_number_tag = company.find('li', class_='icon-fileCertificateIcon')
            branch_number_tag = company.find('li', class_='icon-officeBuildingIcon')

            if company_name_tag:
                company_name = company_name_tag.get_text(strip=True)
                if company_address_tag:
                    company_address = company_address_tag.get_text(strip=True)
                else:
                    company_address = "No address found"
                
                kvk_number = re.search(r'\d+', kvk_number_tag.get_text()).group() if kvk_number_tag else None
                branch_number = re.search(r'\d+', branch_number_tag.get_text()).group() if branch_number_tag else None

                logging.info(f"Found company: {company_name}, Address: {company_address}, KVK Number: {kvk_number}, Branch Number: {branch_number}")
                return company_name, company_address, kvk_number, branch_number

        logging.info(f"No matching company found on KVK for {name}")
        return None, None, None, None
    except TimeoutException:
        logging.error(f"{name} was not found")
        return None, None, None, None
    except WebDriverException as e:
        logging.error(f"WebDriverException occurred: {e}")
        return None, None, None, None

def update_kvk_check(company_id, status, kvk_number=None, branch_number=None):
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
            "UPDATE companies SET kvk_check = %s, kvk_number = %s, branch_number = %s WHERE id = %s",
            (status, kvk_number, branch_number, company_id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        logging.info(f"Updated KVK check for company ID {company_id} to {status} with KVK Number {kvk_number} and Branch Number {branch_number}")

    except Exception as e:
        logging.error(f"Error updating kvk_check in PostgreSQL: {e}")

if __name__ == "__main__":
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Uncomment to run in headless mode
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

    companies = fetch_companies()
    logging.info(f"Fetched {len(companies)} companies from the database.")
    
    for company_id, name, address in companies:
        retries = 3
        for attempt in range(retries):
            try:
                kvk_name, kvk_address, kvk_number, branch_number = search_kvk(driver, name, address)
                if kvk_address:
                    db_street = extract_street_name(address)
                    kvk_street = extract_street_name(kvk_address)
                    logging.info(f"Database street: {db_street.lower()}")
                    logging.info(f"KVK street: {kvk_street.lower()}")
                    if db_street.lower() == kvk_street.lower():
                        update_kvk_check(company_id, "PASS", kvk_number, branch_number)
                        logging.info(f"Company {name} with ID {company_id} passed the KVK check.")
                        break
                    else:
                        update_kvk_check(company_id, "FAIL", kvk_number, branch_number)
                        logging.info(f"Company {name} with ID {company_id} failed the KVK check.")
                        break
                else:
                    update_kvk_check(company_id, "FAIL", kvk_number, branch_number)
                    logging.info(f"Company {name} with ID {company_id} failed the KVK check.")
                    break
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed for company {name} with error: {e}")
                if attempt < retries - 1:
                    logging.info(f"Retrying ({attempt + 2}/{retries})...")
                else:
                    logging.error(f"All {retries} attempts failed for company {name}")

    driver.quit()
