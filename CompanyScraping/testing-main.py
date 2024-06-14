import unittest
from unittest.mock import patch, MagicMock
from Main_Scraper import get_business_list, get_company_details, save_to_postgresql, scrape_and_save

class TestWebScraper(unittest.TestCase):

    @patch('Main_Scraper.webdriver.Chrome')
    def test_get_business_list(self, MockChrome):
        mock_driver = MockChrome.return_value
        mock_driver.page_source = '<html></html>'
        mock_driver.find_elements_by_css_selector.return_value = []

        businesses = get_business_list('https://www.yelu.nl/location/Eindhoven', max_pages=1, delay=0)

        self.assertEqual(len(businesses), 0)
        mock_driver.get.assert_called_with('https://www.yelu.nl/location/Eindhoven')
        mock_driver.quit.assert_called_once()

    @patch('requests.get')
    def test_get_company_details(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = '''
        <html>
            <div class="text weblinks"><a href="">https://lawandmore.nl</a></div>
            <div class="text phone">0403690680</div>
        </html>
        '''
        mock_get.return_value = mock_response

        url, phone = get_company_details('/company/1018672/Law_More_BV')

        self.assertEqual(url, 'https://lawandmore.nl')
        self.assertEqual(phone, '0403690680')

    @patch('psycopg2.connect')
    def test_save_to_postgresql(self, mock_connect):
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        businesses = [
            {'name': 'Law & More B.V.', 'address': "De Zaale 11, Eindhoven, Netherlands", 'url': 'https://lawandmore.nl', 'phone': '0403690680'}
        ]

        save_to_postgresql(businesses)

        mock_cursor.execute.assert_called()
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('Main_Scraper.get_business_list')
    @patch('Main_Scraper.save_to_postgresql')
    def test_scrape_and_save(self, mock_save_to_postgresql, mock_get_business_list):
        mock_get_business_list.return_value = [{'name': 'Law & More B.V.', 'address': 'De Zaale 11, Eindhoven, Netherlands', 'url': 'https://lawandmore.nl', 'phone': '0403690680'}]

        base_urls = ['https://www.yelu.nl/location/Eindhoven']
        scrape_and_save(base_urls, max_pages=1, delay=0)

        mock_get_business_list.assert_called_with('https://www.yelu.nl/location/Eindhoven', 1, 0)
        mock_save_to_postgresql.assert_called_once()

if __name__ == '__main__':
    unittest.main()
