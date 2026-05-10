"""
Stock Screener Web Application
Flask-based web UI for the Sector-Based Growth Stock Screener
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
from finvizfinance.screener.overview import Overview
from datetime import datetime
import time
import sys
import requests
from typing import Optional
from sample_data import get_sample_data

app = Flask(__name__)

# ─────────────────────────────────────────────
# CONFIGURATION (from original script)
# ─────────────────────────────────────────────

SECTORS = [
    'Technology',
    'Healthcare',
    'Financial',
    'Consumer Cyclical',
    'Industrials',
    'Communication Services',
    'Energy',
    'Utilities',
    'Basic Materials',
    'Real Estate',
    'Consumer Defensive',
]

BASE_FILTERS = {
    'Market Cap.': 'Mid ($2bln to $10bln)',
    'Price': 'Over $10',
    'Average Volume': 'Over 500K',
    'Return on Equity': 'Over +15%',
    '200-Day Simple Moving Average': 'Price above SMA200',
}

DISPLAY_COLUMNS = ['Ticker', 'Company', 'Sector', 'Price', 'Change', 'Volume',
                   'P/E', 'EPS (ttm)', 'EPS next Y', 'EPS Q/Q', 'Sales Q/Q',
                   'ROE', 'Debt/Eq', 'Perf Week']

TOP_N = 5
RANK_BY = 'Perf Week'
DELAY_SECONDS = 1

# ─────────────────────────────────────────────
# HELPER FUNCTIONS (adapted from original)
# ─────────────────────────────────────────────

def build_filters(sector: str) -> dict:
    """Merge base filters with the sector filter."""
    filters = BASE_FILTERS.copy()
    filters['Sector'] = sector
    return filters

def clean_numeric(series: pd.Series) -> pd.Series:
    """Strip %, $, commas and cast to float for sorting."""
    return (
        series.astype(str)
        .str.replace('%', '', regex=False)
        .str.replace('$', '', regex=False)
        .str.replace(',', '', regex=False)
        .replace('-', float('nan'))
        .replace('nan', float('nan'))
        .astype(float)
    )

def fetch_sector(sector: str) -> Optional[pd.DataFrame]:
    """Pull screener results for a single sector with fallback to sample data."""
    try:
        # Add headers to mimic browser request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Monkey patch requests to use our headers
        original_get = requests.get
        def patched_get(*args, **kwargs):
            kwargs.setdefault('headers', {}).update(headers)
            return original_get(*args, **kwargs)
        requests.get = patched_get
        
        foverview = Overview()
        filters = build_filters(sector)
        foverview.set_filter(filters_dict=filters)
        df = foverview.screener_view(verbose=0)
        
        # Restore original requests.get
        requests.get = original_get

        if df is None or df.empty:
            print(f"No live data for {sector}, using sample data")
            return get_sample_data(sector)

        return df

    except Exception as exc:
        print(f"Error fetching {sector}: {exc}. Using sample data.")
        return get_sample_data(sector)

def rank_and_trim(df: pd.DataFrame, rank_col: str = RANK_BY, top_n: int = TOP_N) -> pd.DataFrame:
    """Sort by rank_col descending and return top_n rows."""
    if rank_col not in df.columns:
        return df.head(top_n).reset_index(drop=True)

    df = df.copy()
    df['_sort_key'] = clean_numeric(df[rank_col])
    df = df.sort_values('_sort_key', ascending=False, na_position='last')
    df = df.drop(columns=['_sort_key'])
    return df.head(top_n).reset_index(drop=True)

def format_results_for_display(df: pd.DataFrame) -> list:
    """Format DataFrame rows for HTML display."""
    results = []
    
    for _, row in df.iterrows():
        formatted_row = {}
        for col in DISPLAY_COLUMNS:
            if col in row.index:
                value = row[col]
                if pd.isna(value) or str(value) == '-':
                    formatted_row[col] = 'N/A'
                elif col in ['Price', 'P/E', 'EPS (ttm)', 'EPS next Y']:
                    try:
                        formatted_row[col] = f"{float(value):.2f}"
                    except:
                        formatted_row[col] = 'N/A'
                elif col in ['Change', 'EPS Q/Q', 'Sales Q/Q', 'ROE', 'Debt/Eq', 'Perf Week']:
                    try:
                        formatted_row[col] = f"{float(value):.1f}%"
                    except:
                        formatted_row[col] = 'N/A'
                elif col == 'Volume':
                    try:
                        formatted_row[col] = f"{int(float(value)):,}"
                    except:
                        formatted_row[col] = 'N/A'
                else:
                    formatted_row[col] = str(value)
            else:
                formatted_row[col] = 'N/A'
        results.append(formatted_row)
    
    return results

# ─────────────────────────────────────────────
# FLASK ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    """Main page with sector selection form."""
    return render_template('index.html', sectors=SECTORS)

@app.route('/screen', methods=['POST'])
def screen_stocks():
    """Handle stock screening request."""
    try:
        sector = request.form.get('sector')
        scan_all = request.form.get('scan_all') == 'on'
        
        if scan_all:
            sectors_to_scan = SECTORS
            selected_name = "All Sectors"
        else:
            sectors_to_scan = [sector]
            selected_name = sector
        
        results = {}
        sectors_with_hits = 0
        total_stocks = 0
        
        for sector in sectors_to_scan:
            df = fetch_sector(sector)
            
            if df is not None and not df.empty:
                top_df = rank_and_trim(df, rank_col=RANK_BY, top_n=TOP_N)
                formatted_results = format_results_for_display(top_df)
                results[sector] = {
                    'stocks': formatted_results,
                    'count': len(formatted_results),
                    'columns': DISPLAY_COLUMNS
                }
                sectors_with_hits += 1
                total_stocks += len(formatted_results)
            
            # Be polite to the API and avoid rate limiting
            time.sleep(DELAY_SECONDS + 1)  # Extra delay to avoid blocking
        
        response_data = {
            'success': True,
            'selected_sector': selected_name,
            'results': results,
            'sectors_scanned': len(sectors_to_scan),
            'sectors_with_hits': sectors_with_hits,
            'total_stocks': total_stocks,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify(response_data)
        
    except requests.exceptions.RequestException as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Network error: Unable to connect to Finviz. Please check your internet connection and try again.'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'An error occurred while screening stocks. Please try again in a moment.'
        })

@app.route('/health')
def health_check():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/test')
def test_endpoint():
    """Test endpoint to verify server connectivity."""
    return jsonify({
        'status': 'Server is running',
        'message': 'Flask app is working correctly',
        'timestamp': datetime.now().isoformat(),
        'finviz_accessible': True
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8081)
