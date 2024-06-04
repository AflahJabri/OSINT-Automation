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

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    driver.get(base_url)
    time.sleep(delay + random.uniform(0, delay))

    for page in range(1, max_pages + 1):
        print(f"Scraping page {page}")

        time.sleep(delay + random.uniform(0, delay))
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        business_elements = soup.select('div.company.with_img.g_0, div.company.g_0')

        if not business_elements:
            print(f"No more business listings found at page {page}")
            break

        for business in business_elements:
            name = business.find('h4').text.strip()
            address = business.find('div', class_='address').text.strip()
            link_tag = business.find('a')
            company_url, phone = None, None
            if link_tag and 'href' in link_tag.attrs:
                company_page_url = link_tag['href']
                company_url, phone = get_company_details(company_page_url)

            business_id = f"{name}_{address}"

            if business_id not in seen_business_ids:
                seen_business_ids.add(business_id)
                businesses.append({'name': name, 'address': address, 'url': company_url, 'phone': phone})
            else:
                print(f"Duplicate listing found: {name}, {address}")

        print(f"Page {page}: Total unique businesses added: {len(businesses)}")

        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//a[@rel="next"]'))
            )
            driver.execute_script("arguments[0].click();", next_button)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.company.with_img.g_0, div.company.g_0'))
            )
            time.sleep(delay + random.uniform(0, delay))
        except TimeoutException:
            print("Timeout waiting for page to load or unable to find next button")
            break
        except NoSuchElementException:
            print("No more pages available or unable to find next button")
            break
        except StaleElementReferenceException:
            print("Stale element reference, retrying...")
            time.sleep(delay)
            driver.get(driver.current_url)
            continue

    driver.quit()
    return businesses

# Function to fetch the company's URL and phone from its page
def get_company_details(company_page_url):
    base_url = 'https://www.yelu.nl'
    url = f"{base_url}{company_page_url}"
    print(f"Fetching company details from: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve company page: Status code {response.status_code}")
            return None, None

        soup = BeautifulSoup(response.content, 'html.parser')
        website_tag = soup.find('div', class_='text weblinks').find('a')
        phone_tag = soup.find('div', class_='text phone')

        website_url = website_tag['href'] if website_tag and 'href' in website_tag.attrs else None
        phone = phone_tag.text.strip() if phone_tag else None

        return website_url, phone
        
    except Exception as e:
        print(f"Error fetching company details: {e}")
        return None, None

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
            cursor.execute(
                sql.SQL("INSERT INTO companies (name, address, url, phone) VALUES (%s, %s, %s, %s) ON CONFLICT (name, address) DO NOTHING"),
                [business['name'], business['address'], business['url'], business['phone']]
            )

        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved successfully to PostgreSQL")

    except Exception as e:
        print(f"Error: {e}")

# Execution
base_url = 'https://www.yelu.nl/location/s_Hertogenbosch'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Eindhoven'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Tilburg'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Helmond'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Boxtel'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Best'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Breda'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Roosendaal'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Oosterhout'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Sint-michielsgestel'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Geertruidenberg'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Eersel'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Steenbergen'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)

base_url = 'https://www.yelu.nl/location/Rucphen'
business_list = get_business_list(base_url, max_pages=2, delay=1)
save_to_postgresql(business_list)
