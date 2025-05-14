import os
import pandas as pd
from pandas_datareader import data as pdr

def fetch_fred_test(series_id, filename, start_date='1900-01-01'):
    """
    Fetch a FRED series and save to CSV.

    Args:
        series_id (str): FRED series ID
        filename (str): Path to save the CSV file
        start_date (str): Start date for the data (default: '1900-01-01')
    """
    df = pdr.DataReader(series_id, 'fred', start=start_date)
    print(f"Fetched {series_id}: {len(df)} rows from {df.index.min()} to {df.index.max()}")
    os.makedirs('data', exist_ok=True)
    df.to_csv(filename)

# Fetch some test data
fetch_fred_test('FEDFUNDS', 'data/FEDFUNDS_new.csv')
fetch_fred_test('CPALTT01USM657N', 'data/CPI_new.csv')
