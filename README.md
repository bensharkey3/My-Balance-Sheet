# My Balance Sheet

This repo includes 2 Python files that are used to create a dashboard of my personal finances.

I maintain asset transactions in a google sheets doc. The Python scripts in this repo fetch current prices and generate an output to csv which summarises my holdings over time.

**GetCurrentPrices.py** makes 3 API requests to return prices for my holdings across 3 different asset types; shares on the asx, shares on the nyse, and cryptocurrency.

**MyBalanceSheet.py** pulls holdings and dates from the google sheets doc and generates a csv to be read by Tableau.
