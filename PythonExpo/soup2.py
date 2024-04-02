import requests
from bs4 import BeautifulSoup

def scrapecompany_names(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    num_companies_str = soup.find('span', class_='btn-filter filterEnterprise').text.strip().split()[0]
    numcompanies = int(num_companies_str.replace(',', ''))

    companies_per_page = len(soup.find_all('div', class_='product-list-item'))

    companynames = []
    for page_num in range(1, numcompanies // companies_per_page + 1):
        params = {'page': page_num}
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.text, 'html.parser')
        companies = soup.find_all('div', class_='product-list-item')
        for company in companies:
            name = company.find('h3', class_='product-title').text.strip()
            company_names.append(name)
    return company_names

url = 'https://www.kompass.com/z/nl/r/north-brabant/nl_30/'
company_names = scrapecompany_names(url)

for name in company_names:
    print(name)