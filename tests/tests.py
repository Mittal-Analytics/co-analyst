import unittest
from utils import extract_data_from_pdf


class TestExtractDataFromPdf(unittest.TestCase):
    def test_extract_data_from_pdf(self):
        expected = '{"title": "Balance Sheet", "data": [{"title": "CAPITAL AND LIABILITIES", "data": [{"title": "Capital", "data": [{"No": "1", "As at 31.03.2022": "8924612", "(Current Year)": "8924612"}, {"title": "Reserves & Surplus", "data": [{"No": "2", "As at 31.03.2022": "2791955989", "(Current Year)": "2529827285"}]}, {"title": "Deposits", "data": [{"No": "3", "As at 31.03.2022": "40515341227", "(Current Year)": "36812770796"}]}, {"title": "Borrowings", "data": [{"No": "4", "As at 31.03.2022": "4260433798", "(Current Year)": "4172976988"}]}, {"title": "Other Liabilities and Provisions", "data": [{"No": "5", "As at 31.03.2022": "2299318428", "(Current Year)": "1819796631"}]}]}, {"title": "TOTAL", "data": [{"As at 31.03.2022": "49875974054", "(Current Year)": "45344296312"}]}, {"title": "ASSETS", "data": [{"title": "Cash and Balances with Reserve Bank of India", "data": [{"No": "6", "As at 31.03.2022": "2578592071", "(Current Year)": "2132015363"}]}, {"title": "Balances with Banks and money at call and short notice", "data": [{"No": "7", "As at 31.03.2022": "1366931140", "(Current Year)": "1298371731"}]}, {"title": "Investments", "data": [{"No": "8", "As at 31.03.2022": "14814454698", "(Current Year)": "13517052051"}]}, {"title": "Advances", "data": [{"No": "9", "As at 31.03.2022": "27339665929", "(Current Year)": "24494977911"}]}, {"title": "Fixed Assets", "data": [{"No": "10", "As at 31.03.2022": "377081583", "(Current Year)": "384192419"}]}, {"title": "Other Assets", "data": [{"No": "11", "As at 31.03.2022": "3399248633", "(Current Year)": "3517686837"}]}]}, {"title": "TOTAL", "data": [{"As at 31.03.2022": "49875974054", "(Current Year)": "45344296312"}]}]}]}'
        actual = extract_data_from_pdf(
            "tests/annual_reports/sbi.pdf", start=119, end=119
        )
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
