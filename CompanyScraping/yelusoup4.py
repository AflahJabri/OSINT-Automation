import requests
from bs4 import BeautifulSoup
import time
import random
import psycopg2
from psycopg2 import sql

# Function to get business list from a URL
def get_business_list(base_url, max_pages=100, delay=1):
    businesses = []
    seen_businesses = set()
    last_page_businesses = None
    
    for page in range(1, max_pages + 1):
        url = f"{base_url}?page={page}"
        print(f"Fetching URL: {url}")
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed to retrieve page {page}: Status code {response.status_code}")
            break
        
        soup = BeautifulSoup(response.content, 'html.parser')
        business_elements = soup.find_all('div', class_='company with_img g_0')
        
        print(f"Page {page}: Found {len(business_elements)} business listings")
        
        if not business_elements:
            print(f"No more business listings found at page {page}")
            break
        
        current_page_businesses = []
        for business in business_elements:
            name = business.find('h4').text.strip()
            address = business.find('div', class_='address').text.strip()
            link_tag = business.find('a')
            company_url = None
            if link_tag and 'href' in link_tag.attrs:
                company_page_url = link_tag['href']
                company_url = get_company_url(company_page_url)
            
            business_id = f"{name}_{address}"
            
            current_page_businesses.append(business_id)
            
            if business_id not in seen_businesses:
                seen_businesses.add(business_id)
                businesses.append({'name': name, 'address': address, 'url': company_url})
        
        new_businesses = len(current_page_businesses) - len(businesses)
        print(f"Page {page}: Added {new_businesses} new business listings")
        
        if last_page_businesses == current_page_businesses:
            print(f"Duplicate listings found at page {page}. Stopping.")
            break
        
        last_page_businesses = current_page_businesses
        time.sleep(delay + random.uniform(0, delay))
    
    return businesses

# Function to get company URL from company page
def get_company_url(company_page_url):
    base_url = 'https://www.yelu.nl'
    url = f"{base_url}{company_page_url}"
    print(f"Fetching company URL from: {url}")
    
    try:
        response = requests.get(url)
        if response.status_code != 200:
            print(f"Failed to retrieve company page: Status code {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        website_tag = soup.find('a', class_='website')
        if website_tag and 'href' in website_tag.attrs:
            return website_tag['href']
        else:
            return None
    except Exception as e:
        print(f"Error fetching company URL: {e}")
        return None

# Function to save businesses to PostgreSQL
def save_to_postgresql(businesses):
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="password",
            host="localhost",
            port="5432"
        )
        cursor = conn.cursor()
        
        # Insert businesses into the table
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
business_list = get_business_list(base_url, max_pages=50, delay=2)
save_to_postgresql(business_list)

for business in business_list:
    print(business)