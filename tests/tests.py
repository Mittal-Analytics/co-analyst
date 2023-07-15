import json
import unittest

from analyst import extract_data_from_pdf
from utilities import tablex


class TestTablex(unittest.TestCase):
    def test_tablex_sbi(self):
        with open("tests/expected-table/sbi-balance-sheet.json", "r") as f:
            expected = json.load(f)
        actual = tablex.extract_tables(
            "tests/annual-reports/sbi.pdf", start=119, end=119
        )
        self.assertEqual(expected, actual)


class TestExtractDataFromPdf(unittest.TestCase):
    def test_extract_data_from_pdf_sbi(self):
        with open("tests/expected-data/sbi-balance-sheet.json", "r") as f:
            expected = json.load(f)
        actual = extract_data_from_pdf(
            "tests/annual-reports/sbi.pdf", start=119, end=119
        )
        self.assertEqual(expected, actual)
        actual = extract_data_from_pdf(
            "tests/annual-reports/sbi.pdf", statement_name="balance sheet"
        )
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
