import requests
from bs4 import BeautifulSoup

def scrape_company_names(url):
    num_companies = 100501  # Número total de empresas
    companies_per_page = 10  # Suponemos que hay 10 empresas por página
    
    for page_num in range(1, num_companies // companies_per_page + 2):  # Ajustamos el rango
        params = {'page': page_num}
        response = requests.get(url, params=params)
        soup = BeautifulSoup(response.text, 'html.parser')
        companies = soup.find_all('div', class_='product-list-item')
        for company in companies:
            name_tag = company.find('h3', class_='product-title')
            if name_tag:
                name = name_tag.text.strip()
                print(name)  # Imprimir el nombre de la empresa
                # Aquí podrías almacenar el nombre en una lista si lo deseas
                # company_names.append(name)

url = 'https://www.kompass.com/z/nl/r/north-brabant/nl_30/'
scrape_company_names(url)