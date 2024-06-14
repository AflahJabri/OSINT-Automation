import unittest
from unittest.mock import patch, MagicMock
from addressCleaner import clean_address, fetch_addresses, update_address  # Replace 'your_module' with the actual module name
from psycopg2 import sql

class TestCleanAddresses(unittest.TestCase):

    def test_clean_address(self):
        self.assertEqual(clean_address("Hoekkampstraat 21, 5223 VC 's-Hertogenbosch, North Brabant, 's-Hertogenbosch"), "Hoekkampstraat 21")
        self.assertEqual(clean_address("Docterskampstraat 1F, 5222AM 's-Hertogenbosch, 's-Hertogenbosch"), "Docterskampstraat 1")
        self.assertEqual(clean_address("Invalid Address"), "Invalid Address")
        self.assertEqual(clean_address("Jacob van Maerlantstraat 86-90, 's-Hertogenbosch"), "Jacob van Maerlantstraat 86")

    @patch('addressCleaner.psycopg2.connect')
    def test_fetch_addresses(self, mock_connect):
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value
        mock_cursor.fetchall.return_value = [(1, "Hoekkampstraat 21, 5223 VC 's-Hertogenbosch, North Brabant, 's-Hertogenbosch"), (2, "Docterskampstraat 1F, 5222AM 's-Hertogenbosch, 's-Hertogenbosch")]

        companies = fetch_addresses()

        self.assertEqual(companies, [(1, "Hoekkampstraat 21, 5223 VC 's-Hertogenbosch, North Brabant, 's-Hertogenbosch"), (2, "Docterskampstraat 1F, 5222AM 's-Hertogenbosch, 's-Hertogenbosch")])
        mock_cursor.execute.assert_called_once_with("SELECT id, address FROM companies")
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch('addressCleaner.psycopg2.connect')
    def test_update_address(self, mock_connect):
        mock_conn = mock_connect.return_value
        mock_cursor = mock_conn.cursor.return_value

        update_address(1, "Hoekkampstraat 21")

        mock_cursor.execute.assert_called_once_with(
            sql.SQL("UPDATE companies SET address = %s WHERE id = %s"),
            ["Hoekkampstraat 21", 1]
        )
        mock_conn.commit.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_conn.close.assert_called_once()

if __name__ == '__main__':
    unittest.main()
