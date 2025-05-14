import os
import pandas as pd
from pandas_datareader import data as pdr

def fetch_fred_test(series_id, filename, start_date='1900-01-01'):
    """
    Fetch a FRED series, resample to monthly frequency, and save to CSV.
    
    Args:
        series_id (str): FRED series ID
        filename (str): Path to save the CSV file
        start_date (str): Start date for the data (default: '1900-01-01')
    """
    # Fetch data from FRED
    df = pdr.DataReader(series_id, 'fred', start=start_date)
    original_count = len(df)
    
    # Check if the data is already monthly
    is_monthly = False
    if len(df) > 1:
        # Get the first two dates to check frequency
        dates = df.index.sort_values()[:2]
        days_diff = (dates[1] - dates[0]).days
        # If difference is approximately a month (28-31 days)
        is_monthly = 28 <= days_diff <= 31
    
    # Resample to monthly frequency if not already monthly
    if not is_monthly:
        # Convert index to datetime if it's not already
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Resample to end of month (EOM) and take the last value of each month
        df = df.resample('ME').last()
        print(f"Resampled {series_id} from {original_count} rows to {len(df)} monthly rows")
    else:
        print(f"{series_id} is already monthly with {len(df)} rows")
    
    # Print date range
    print(f"Date range for {series_id}: {df.index.min()} to {df.index.max()}")
    
    # Save to CSV
    os.makedirs('data', exist_ok=True)
    df.to_csv(filename)
    return df

# Test with a monthly series (FEDFUNDS)
print("Testing with FEDFUNDS (expected to be monthly):")
monthly_df = fetch_fred_test('FEDFUNDS', 'data/FEDFUNDS_monthly.csv')

# Test with a daily series (DCOILWTICO - Crude Oil)
print("\nTesting with DCOILWTICO (expected to be daily):")
daily_df = fetch_fred_test('DCOILWTICO', 'data/DCOILWTICO_monthly.csv')

# Print the first few rows of each
print("\nFirst few rows of FEDFUNDS (monthly):")
print(monthly_df.head())

print("\nFirst few rows of DCOILWTICO (resampled to monthly):")
print(daily_df.head())
