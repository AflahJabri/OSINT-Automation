import unittest
from unittest.mock import patch, MagicMock
from validating import fetch_companies, search_kvk, update_kvk_check, extract_street_name, accept_cookies
from selenium.webdriver.support.ui import WebDriverWait

class TestValidating(unittest.TestCase):

    @patch('validating.psycopg2.connect')
    def test_fetch_companies(self, mock_connect):
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [(1, 'Dakbedekking Brabant', 'Topaas 9'), (2, 'Taxi Service Den Bosch', 'Hoekkampstraat 21')]

        companies = fetch_companies()

        self.assertEqual(companies, [(1, 'Dakbedekking Brabant', 'Topaas 9'), (2, 'Taxi Service Den Bosch', 'Hoekkampstraat 21')])
        mock_cursor.execute.assert_called_once_with("SELECT id, name, address FROM companies")
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('validating.psycopg2.connect')
    def test_update_kvk_check(self, mock_connect):
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        update_kvk_check(2, "PASS", "54458455", "000010212302")

        mock_cursor.execute.assert_called_once_with(
            "UPDATE companies SET kvk_check = %s, kvk_number = %s, branch_number = %s WHERE id = %s",
            ("PASS", "54458455", "000010212302", 2)
        )
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    def test_extract_street_name(self):
        address = "Hoekkampstraat 21, 5223 VC 's-Hertogenbosch, North Brabant, 's-Hertogenbosch, Netherlands"
        street_name = extract_street_name(address)
        self.assertEqual(street_name, "Hoekkampstraat 21")

    @patch('validating.webdriver.Chrome')
    def test_search_kvk(self, MockChrome):
        mock_driver = MockChrome.return_value
        mock_driver.page_source = '''
        <html>
            <ul class="mb-9 mb-12@size-m border-top pt-6" data-ui-test-class="search-results-list"><li class="mb-6 pb-7 border-bottom"><div class="Flexbox__s-sc-5j1a9d-0 hqhWFk"><div class="FlexboxItem__s-sc-wm1s05-0 jdISuf"><div class="mb-4"><a aria-label="Taxi Service Den Bosch with number 54458455000010212302" class="TextLink-module_textlink__1SZwI TextLink-module_primary__rc8ab font-weight-regular" href="https://www.kvk.nl/bestellen/#/54458455000010212302" style="overflow-wrap: anywhere; white-space: normal;"><span class="TextLink-module_content__Qg5Ga"><span class="TextLink-module_icon-first-word__GYcoh"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Taxi</font></font></span> <font style="vertical-align: inherit;"><font style="vertical-align: inherit;"> Service Den Bosch</font></font></span></a><div class="mb-2 font-size-s"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Taxi Service Den Bosch is part of HeinTax</font></font></div><div data-ui-test-class="activiteitomschrijving"><div><span data-ui-test-class="visible-text"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Taxi company. Guidance with or takeover of personal care. Individual guidance; providing daily structure, supervising/monitoring...</font></font></span><a aria-label="Show more" class="TextLink-module_textlink__1SZwI TextLink-module_primary__rc8ab pl-2" href="#"><span class="TextLink-module_content__Qg5Ga"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Show </font><span class="TextLink-module_icon-last-word__Q9OD1"><font style="vertical-align: inherit;">more</font></span></font> <span class="TextLink-module_icon-last-word__Q9OD1"><font style="vertical-align: inherit;"></font><svg aria-hidden="true" aria-label="" class="TextLink-module_icon__LLZuk TextLink-module_right__5bdh1" focusable="false" height="32px" version="1.1" viewBox="0 0 64 64" width="32px" xmlns="http://www.w3.org/2000/svg"><polygon points="32 46 54.44 23.56 50.91 20.02 32 38.93 13.09 20.02 9.56 23.56"></polygon></svg></span></span></a></div></div></div><ul class="List-module_generic-list__eILOq List-module_icons__aKWLT mb-4"><li class="icon-fileCertificateIcon"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Chamber of Commerce number: 54458455</font></font></li><li class="icon-stampIcon"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Partnership</font></font></li><li class="icon-officeBuildingsIcon"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Headquarters</font></font></li><li class="icon-officeBuildingIcon"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Location number: 000010212302</font></font></li><li class="icon-locationLargeIcon"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Hoekkampstraat 21, 5223VC 's-Hertogenbosch</font></font></li></ul><div class="mt-2"><span class="font-weight-medium mr-2"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Trade names:</font></font></span><ul class="d-inline pr-2"><li class="d-inline-block border-left border-width-double border-color-primary-petrol-base pr-2 border-none pl-0" style="line-height: 18px;"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">HeinTax</font></font></li><li class="d-inline-block border-left border-width-double border-color-primary-petrol-base pr-2 pl-2" style="line-height: 18px;"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Taxi Service Den Bosch</font></font></li></ul></div></div><div class="FlexboxItem__s-sc-wm1s05-0 eeLjkF"><div class="mt-6 mt-2@size-m ml-2@size-m"><button type="button" aria-disabled="false" class="Button-module_generic-button__RuwCD Button-module_secondary__phBso trinity-button" tabindex="0"><font style="vertical-align: inherit;"><font style="vertical-align: inherit;">Order now</font></font></button></div></div></div></li></ul>
        </html>
        '''

        name, address, kvk_number, branch_number = search_kvk(mock_driver, "Taxi Service Den Bosch", "Hoekkampstraat 21")

        self.assertEqual(name, "TaxiService Den Bosch")
        self.assertEqual(address, "Hoekkampstraat 21, 5223VC 's-Hertogenbosch")
        self.assertEqual(kvk_number, "54458455")
        self.assertEqual(branch_number, "000010212302")

    @patch('validating.webdriver.Chrome')
    @patch('validating.WebDriverWait')
    def test_accept_cookies(self, MockWebDriverWait, MockChrome):
        mock_driver = MockChrome.return_value
        mock_wait = MockWebDriverWait.return_value
        mock_button = MagicMock()
        mock_wait.until.return_value = mock_button

        accept_cookies(mock_driver)

        mock_wait.until.assert_called_once()
        mock_button.click.assert_called_once()

if __name__ == '__main__':
    unittest.main()
