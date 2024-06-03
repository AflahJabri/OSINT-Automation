import time
import random
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import psycopg2
from psycopg2 import sql
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Function to scrape business listings from a given base URL
def get_business_list(base_url, max_pages=100, delay=1):
    businesses = []
    seen_business_ids = set()

    # Setup Chrome options for headless browsing
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run Chrome in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    # Open the base URL
    driver.get(base_url)
    time.sleep(delay + random.uniform(0, delay))  # Random delay to mimic human behavior

    for page in range(1, max_pages + 1):
        print(f"Scraping page {page}")

        time.sleep(delay + random.uniform(0, delay))  # Random delay to mimic human behavior
        soup = BeautifulSoup(driver.page_source, 'html.parser')  # Parse the page source with BeautifulSoup
        business_elements = soup.select('div.company.with_img.g_0, div.company.g_0')  # Select business elements

        print(f"Page {page}: Found {len(business_elements)} business listings")

        if not business_elements:
            print(f"No more business listings found at page {page}")
            break

        for business in business_elements:
            # Extract business name and address
            name = business.find('h4').text.strip()
            address = business.find('div', class_='address').text.strip()
            link_tag = business.find('a')  # Find the link tag
            company_url = None
            if link_tag and 'href' in link_tag.attrs:
                company_page_url = link_tag['href']
                company_url = get_company_url(company_page_url)  # Fetch company URL from the company page

            business_id = f"{name}_{address}"

            if business_id not in seen_business_ids:
                seen_business_ids.add(business_id)
                businesses.append({'name': name, 'address': address, 'url': company_url})  # Add business to the list
            else:
                print(f"Duplicate listing found: {name}, {address}")

        print(f"Page {page}: Total unique businesses added: {len(businesses)}")

        # Check if there's a next page button and click it
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[@rel="next"]'))
            )
            driver.execute_script("arguments[0].click();", next_button)  # Click the next page button
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.company.with_img.g_0, div.company.g_0'))
            )
            time.sleep(delay + random.uniform(0, delay))  # Random delay to mimic human behavior
        except TimeoutException:
            print("Timeout waiting for page to load or unable to find next button")
            break
        except NoSuchElementException:
            print("No more pages available or unable to find next button")
            break
        except StaleElementReferenceException:
            print("Stale element reference, retrying...")
            time.sleep(delay)
            driver.get(driver.current_url)  # Reload the current URL and retry
            continue

    driver.quit()  # Close the browser
    return businesses

# Function to fetch the company's URL from its page
def get_company_url(company_page_url):
    base_url = 'https://www.yelu.nl'
    url = f"{base_url}{company_page_url}"
    print(f"Fetching company URL from: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)  # Make a GET request to the company page
        if response.status_code != 200:
            print(f"Failed to retrieve company page: Status code {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')  # Parse the company page with BeautifulSoup
        website_tag = soup.find('div', class_='text weblinks').find('a')  # Find the website link
        if website_tag and 'href' in website_tag.attrs:
            return website_tag['href']  # Return the website URL
        else:
            return None
    except Exception as e:
        print(f"Error fetching company URL: {e}")
        return None

# Function to save the scraped data to PostgreSQL
def save_to_postgresql(businesses):
    try:
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()

        for business in businesses:
            # Insert business data into the database, avoiding duplicates based on name and address
            cursor.execute(
                sql.SQL("INSERT INTO companies (name, address, url) VALUES (%s, %s, %s) ON CONFLICT (name, address) DO NOTHING"),
                [business['name'], business['address'], business['url']]
            )

        conn.commit()  # Commit the transaction
        cursor.close()
        conn.close()  # Close the database connection
        print("Data saved successfully to PostgreSQL")

    except Exception as e:
        print(f"Error: {e}")

# Calling functions with base_url based on city we are scraping 
base_url = 'https://www.yelu.nl/location/s_Hertogenbosch'
business_list = get_business_list(base_url, max_pages=1, delay=2)
save_to_postgresql(business_list)

# Uncomment the lines below to print the business list
# for business in business_list:
#     print(business)
