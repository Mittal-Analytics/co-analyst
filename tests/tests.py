import unittest
from analyst import extract_data_from_pdf


class TestExtractDataFromPdf(unittest.TestCase):
    def test_extract_data_from_pdf(self):
        expected = '[{"title": "balance sheet", "unit": "thousands", "data": [{"title": "CAPITAL AND LIABILITIES", "data": [{"title": "Capital", "data": [{"Note": "1", "2022": "8924612", "2021": "8924612"}, {"title": "Reserves & Surplus", "data": [{"Note": "2", "2022": "2791955989", "2021": "2529827285"}]}, {"title": "Deposits", "data": [{"Note": "3", "2022": "40515341227", "2021": "36812770796"}]}, {"title": "Borrowings", "data": [{"Note": "4", "2022": "4260433798", "2021": "4172976988"}]}, {"title": "Other Liabilities and Provisions", "data": [{"Note": "5", "2022": "2299318428", "2021": "1819796631"}]}]}, {"title": "TOTAL", "data": [{"2022": "49875974054", "2021": "45344296312"}]}, {"title": "ASSETS", "data": [{"title": "Cash and Balances with Reserve Bank of India", "data": [{"Note": "6", "2022": "2578592071", "2021": "2132015363"}]}, {"title": "Balances with Banks and money at call and short notice", "data": [{"Note": "7", "2022": "1366931140", "2021": "1298371731"}]}, {"title": "Investments", "data": [{"Note": "8", "2022": "14814454698", "2021": "13517052051"}]}, {"title": "Advances", "data": [{"Note": "9", "2022": "27339665929", "2021": "24494977911"}]}, {"title": "Fixed Assets", "data": [{"Note": "10", "2022": "377081583", "2021": "384192419"}]}, {"title": "Other Assets", "data": [{"Note": "11", "2022": "3399248633", "2021": "3517686837"}]}]}, {"title": "TOTAL", "data": [{"2022": "49875974054", "2021": "45344296312"}]}]}]}]'
        actual = extract_data_from_pdf(
            "tests/annual_reports/sbi.pdf", start=119, end=119
        )
        self.assertEqual(expected, actual)
        actual = extract_data_from_pdf(
            "tests/annual_reports/sbi.pdf", statement_name="balance sheet"
        )
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
