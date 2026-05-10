"""
Sample data for testing when Finviz is blocking requests
"""

import pandas as pd

def get_sample_data(sector: str) -> pd.DataFrame:
    """Return sample data for testing when Finviz is unavailable"""
    
    sample_stocks = {
        'Technology': [
            {'Ticker': 'AAPL', 'Company': 'Apple Inc.', 'Sector': 'Technology', 'Price': 175.43, 'Change': 1.2, 'Volume': 52345678, 'P/E': 29.5, 'EPS (ttm)': 5.95, 'EPS next Y': 8.2, 'EPS Q/Q': 15.3, 'Sales Q/Q': 8.1, 'ROE': 36.9, 'Debt/Eq': 1.73, 'Perf Week': 2.1},
            {'Ticker': 'MSFT', 'Company': 'Microsoft Corporation', 'Sector': 'Technology', 'Price': 378.91, 'Change': 0.8, 'Volume': 23456789, 'P/E': 35.2, 'EPS (ttm)': 10.76, 'EPS next Y': 12.4, 'EPS Q/Q': 18.2, 'Sales Q/Q': 12.7, 'ROE': 39.7, 'Debt/Eq': 0.47, 'Perf Week': 1.5},
            {'Ticker': 'GOOGL', 'Company': 'Alphabet Inc.', 'Sector': 'Technology', 'Price': 139.62, 'Change': -0.5, 'Volume': 34567890, 'P/E': 26.8, 'EPS (ttm)': 5.21, 'EPS next Y': 6.8, 'EPS Q/Q': 12.4, 'Sales Q/Q': 9.3, 'ROE': 18.7, 'Debt/Eq': 0.11, 'Perf Week': -0.8},
            {'Ticker': 'NVDA', 'Company': 'NVIDIA Corporation', 'Sector': 'Technology', 'Price': 485.09, 'Change': 3.2, 'Volume': 45678901, 'P/E': 65.3, 'EPS (ttm)': 7.43, 'EPS next Y': 9.2, 'EPS Q/Q': 42.3, 'Sales Q/Q': 34.2, 'ROE': 55.1, 'Debt/Eq': 0.22, 'Perf Week': 4.1},
            {'Ticker': 'META', 'Company': 'Meta Platforms Inc.', 'Sector': 'Technology', 'Price': 326.49, 'Change': 1.8, 'Volume': 56789012, 'P/E': 32.1, 'EPS (ttm)': 10.17, 'EPS next Y': 11.9, 'EPS Q/Q': 23.1, 'Sales Q/Q': 16.8, 'ROE': 19.8, 'Debt/Eq': 0.15, 'Perf Week': 2.3},
        ],
        'Healthcare': [
            {'Ticker': 'JNJ', 'Company': 'Johnson & Johnson', 'Sector': 'Healthcare', 'Price': 157.23, 'Change': 0.3, 'Volume': 67890123, 'P/E': 16.8, 'EPS (ttm)': 9.36, 'EPS next Y': 10.2, 'EPS Q/Q': 8.7, 'Sales Q/Q': 6.9, 'ROE': 25.3, 'Debt/Eq': 0.41, 'Perf Week': 0.5},
            {'Ticker': 'PFE', 'Company': 'Pfizer Inc.', 'Sector': 'Healthcare', 'Price': 28.94, 'Change': -0.2, 'Volume': 78901234, 'P/E': 12.3, 'EPS (ttm)': 2.35, 'EPS next Y': 2.1, 'EPS Q/Q': -5.2, 'Sales Q/Q': -8.3, 'ROE': 15.7, 'Debt/Eq': 0.58, 'Perf Week': -0.1},
            {'Ticker': 'UNH', 'Company': 'UnitedHealth Group', 'Sector': 'Healthcare', 'Price': 512.73, 'Change': 1.1, 'Volume': 89012345, 'P/E': 21.7, 'EPS (ttm)': 23.63, 'EPS next Y': 26.8, 'EPS Q/Q': 14.2, 'Sales Q/Q': 11.3, 'ROE': 27.9, 'Debt/Eq': 0.71, 'Perf Week': 1.4},
        ],
        'Financial': [
            {'Ticker': 'JPM', 'Company': 'JPMorgan Chase & Co.', 'Sector': 'Financial', 'Price': 148.67, 'Change': 0.9, 'Volume': 90123456, 'P/E': 11.2, 'EPS (ttm)': 13.27, 'EPS next Y': 14.5, 'EPS Q/Q': 9.8, 'Sales Q/Q': 7.2, 'ROE': 15.3, 'Debt/Eq': 1.18, 'Perf Week': 1.2},
            {'Ticker': 'BAC', 'Company': 'Bank of America Corporation', 'Sector': 'Financial', 'Price': 29.84, 'Change': 0.7, 'Volume': 12345678, 'P/E': 10.8, 'EPS (ttm)': 2.76, 'EPS next Y': 3.1, 'EPS Q/Q': 11.2, 'Sales Q/Q': 8.9, 'ROE': 11.8, 'Debt/Eq': 1.42, 'Perf Week': 0.9},
            {'Ticker': 'WFC', 'Company': 'Wells Fargo & Company', 'Sector': 'Financial', 'Price': 41.28, 'Change': 0.5, 'Volume': 23456789, 'P/E': 9.3, 'EPS (ttm)': 4.44, 'EPS next Y': 4.8, 'EPS Q/Q': 7.3, 'Sales Q/Q': 5.1, 'ROE': 11.2, 'Debt/Eq': 1.31, 'Perf Week': 0.6},
        ]
    }
    
    if sector in sample_stocks:
        return pd.DataFrame(sample_stocks[sector])
    else:
        # Return empty DataFrame for sectors not in sample data
        return pd.DataFrame()
