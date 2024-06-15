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
from selenium.common.exceptions import NoSuchElementException


def get_business_list(base_url, max_pages=100, delay=1):
    businesses = []
    seen_business_ids = set()

    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless Chrome
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # Create a new instance of the Chrome driver
    driver = webdriver.Chrome(service=Service(), options=chrome_options)

    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        print(f"Fetching URL: {url}")

        driver.get(url)
        time.sleep(delay + random.uniform(0, delay))

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        business_elements = soup.find_all('div', class_='company with_img g_0')

        print(f"Page {page}: Found {len(business_elements)} business listings")

        if not business_elements:
            print(f"No more business listings found at page {page}")
            break

        for business in business_elements:
            name = business.find('h4').text.strip()
            address = business.find('div', class_='address').text.strip()
            link_tag = business.find('a')
            company_url = None
            if link_tag and 'href' in link_tag.attrs:
                company_page_url = link_tag['href']
                company_url = get_company_url(company_page_url)

            business_id = f"{name}_{address}"

            if business_id not in seen_business_ids:
                seen_business_ids.add(business_id)
                businesses.append({'name': name, 'address': address, 'url': company_url})
            else:
                print(f"Duplicate listing found: {name}, {address}")

        print(f"Page {page}: Total unique businesses added: {len(businesses)}")

    driver.quit()
    return businesses

def get_company_url(company_page_url):
    base_url = 'https://www.yelu.nl'
    url = f"{base_url}{company_page_url}"
    print(f"Fetching company URL from: {url}")

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve company page: Status code {response.status_code}")
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        website_tag = soup.find('div', class_='text weblinks').find('a')
        if website_tag and 'href' in website_tag.attrs:
            return website_tag['href']
        else:
            return None
    except Exception as e:
        print(f"Error fetching company URL: {e}")
        return None

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
                sql.SQL("INSERT INTO companies (name, address, url) VALUES (%s, %s, %s)"),
                [business['name'], business['address'], business['url']]
            )

        conn.commit()
        cursor.close()
        conn.close()
        print("Data saved successfully to PostgreSQL")

    except Exception as e:
        print(f"Error: {e}")

# Example usage
base_url = 'https://www.yelu.nl/location/s_Hertogenbosch'
business_list = get_business_list(base_url, max_pages=4, delay=2)
save_to_postgresql(business_list)

for business in business_list:
    print(business)
