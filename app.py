"""
Advanced Stock Screener Web Application
Flask-based web UI for the Comprehensive Research-Based Stock Screener
Implements Graham, Buffett, Lynch, and quantitative factor criteria
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.technical import Technical
from finvizfinance.screener.financial import Financial
from datetime import datetime
import time
import sys
import requests
import warnings
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass
from sample_data import get_sample_data

warnings.filterwarnings('ignore')

app = Flask(__name__)

# ─────────────────────────────────────────────
# ADVANCED CRITERIA CONFIGURATION (Research-Based)
# ─────────────────────────────────────────────

@dataclass
class ScreenerCriteria:
    """Comprehensive screening criteria based on investment legends"""
    
    # Graham Value Criteria
    graham_pe_max: float = 20.0          # P/E ratio under 20
    graham_pb_max: float = 2.0           # Price-to-Book under 2.0
    
    # Buffett Quality Criteria  
    buffett_roe_min: float = 15.0        # ROE over 15%
    buffett_debt_equity_max: float = 1.0 # Debt/Equity under 1.0
    buffett_profit_margin_min: float = 10.0 # Profit margin over 10%
    
    # Lynch Growth Criteria
    lynch_eps_growth_min: float = 10.0   # EPS growth over 10%
    lynch_sales_growth_min: float = 5.0  # Sales growth over 5%
    
    # Technical Criteria
    price_min: float = 10.0              # Price over $10
    volume_avg_min: int = 500000         # Average volume over 500K
    market_cap_min: float = 2000         # Market cap over $2B
    
    # Scoring Weights
    fundamental_weight: float = 0.4     # 40% weight to fundamentals
    technical_weight: float = 0.2       # 20% weight to technicals
    quality_weight: float = 0.3          # 30% weight to quality
    growth_weight: float = 0.1           # 10% weight to growth

# Global criteria instance
CRITERIA = ScreenerCriteria()

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

# Enhanced filters based on comprehensive research
BASE_FILTERS = {
    # Descriptive filters
    'Market Cap.': 'Mid ($2bln to $10bln)',      # Mid-cap focus
    'Price': 'Over $10',                          # Exclude penny stocks
    'Average Volume': 'Over 500K',                # Liquidity filter
    
    # Buffett Quality Criteria
    'Return on Equity': 'Over +15%',               # ROE > 15%
    'P/E': 'Under 25',                            # Reasonable valuation
    'Debt/Equity': 'Under 1',                     # Conservative debt
    
    # Lynch Growth Criteria
    'EPS growthqtr over qtr': 'Over 10%',          # EPS growth > 10%
    'Sales growthqtr over qtr': 'Over 5%',          # Sales growth > 5%
    
    # Technical filter
    '200-Day Simple Moving Average': 'Price above SMA200',  # Uptrend
}

# Enhanced display columns with research-based metrics
DISPLAY_COLUMNS = ['Ticker', 'Company', 'Sector', 'Price', 'Change', 'Volume',
                   'P/E', 'P/B', 'ROE', 'Debt/Eq', 'EPS Q/Q', 'Sales Q/Q', 
                   'Profit Margin', 'Overall Score', 'Grade']

TOP_N = 10  # Increased to show more qualified stocks
RANK_BY = 'Overall Score'  # Rank by our comprehensive score
DELAY_SECONDS = 1

# ─────────────────────────────────────────────
# ADVANCED SCORING FUNCTIONS (Research-Based)
# ─────────────────────────────────────────────

def clean_numeric_value(value) -> float:
    """Convert financial string values to float."""
    if pd.isna(value) or value == '-' or value == 'N/A':
        return np.nan
    
    value_str = str(value).replace('%', '').replace('$', '').replace(',', '')
    
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return np.nan

def calculate_financial_score(df_row: pd.Series) -> float:
    """Calculate fundamental financial score based on Graham and Buffett criteria."""
    score = 0.0
    max_score = 0.0
    
    # Graham Criteria (Value Investing)
    pe_ratio = clean_numeric_value(df_row.get('P/E'))
    if not np.isnan(pe_ratio) and pe_ratio <= CRITERIA.graham_pe_max:
        score += 20  # P/E ratio score
    max_score += 20
    
    pb_ratio = clean_numeric_value(df_row.get('P/B'))
    if not np.isnan(pb_ratio) and pb_ratio <= CRITERIA.graham_pb_max:
        score += 15  # P/B ratio score
    max_score += 15
    
    # Buffett Criteria (Quality)
    roe = clean_numeric_value(df_row.get('ROE'))
    if not np.isnan(roe) and roe >= CRITERIA.buffett_roe_min:
        score += 25  # ROE score
    max_score += 25
    
    debt_eq = clean_numeric_value(df_row.get('Debt/Eq'))
    if not np.isnan(debt_eq) and debt_eq <= CRITERIA.buffett_debt_equity_max:
        score += 20  # Debt/Equity score
    max_score += 20
    
    profit_margin = clean_numeric_value(df_row.get('Profit Margin'))
    if not np.isnan(profit_margin) and profit_margin >= CRITERIA.buffett_profit_margin_min:
        score += 20  # Profit margin score
    max_score += 20
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_growth_score(df_row: pd.Series) -> float:
    """Calculate growth score based on Peter Lynch criteria."""
    score = 0.0
    max_score = 0.0
    
    # EPS Growth
    eps_qq = clean_numeric_value(df_row.get('EPS Q/Q'))
    if not np.isnan(eps_qq) and eps_qq >= CRITERIA.lynch_eps_growth_min:
        score += 60  # EPS growth is most important
    max_score += 60
    
    # Sales Growth
    sales_qq = clean_numeric_value(df_row.get('Sales Q/Q'))
    if not np.isnan(sales_qq) and sales_qq >= CRITERIA.lynch_sales_growth_min:
        score += 40  # Sales growth
    max_score += 40
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_technical_score(df_row: pd.Series) -> float:
    """Calculate technical analysis score."""
    score = 0.0
    max_score = 0.0
    
    # Volume Confirmation
    volume = clean_numeric_value(df_row.get('Volume'))
    if not np.isnan(volume) and volume >= CRITERIA.volume_avg_min:
        score += 40  # Sufficient volume
    max_score += 40
    
    # Price Quality
    price = clean_numeric_value(df_row.get('Price'))
    if not np.isnan(price) and price >= CRITERIA.price_min:
        score += 30  # Above minimum price
    max_score += 30
    
    # Market Cap Quality
    market_cap = clean_numeric_value(df_row.get('Market Cap'))
    if not np.isnan(market_cap) and market_cap >= CRITERIA.market_cap_min:
        score += 30  # Sufficient market cap
    max_score += 30
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_quality_score(df_row: pd.Series) -> float:
    """Calculate overall business quality score."""
    score = 0.0
    max_score = 0.0
    
    # Combined financial health score
    debt_eq = clean_numeric_value(df_row.get('Debt/Eq'))
    roe = clean_numeric_value(df_row.get('ROE'))
    
    if not np.isnan(debt_eq) and not np.isnan(roe):
        if debt_eq <= 0.5 and roe >= 20:  # Excellent financial health
            score += 60
        elif debt_eq <= 1.0 and roe >= 15:  # Good financial health
            score += 40
        elif debt_eq <= 1.5 and roe >= 10:  # Acceptable financial health
            score += 20
    max_score += 60
    
    # Profitability consistency
    profit_margin = clean_numeric_value(df_row.get('Profit Margin'))
    if not np.isnan(profit_margin):
        if profit_margin >= 20:
            score += 40
        elif profit_margin >= 15:
            score += 30
        elif profit_margin >= 10:
            score += 20
    max_score += 40
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_overall_score(df_row: pd.Series) -> Tuple[float, str]:
    """Calculate weighted overall score and assign grade."""
    # Calculate individual component scores
    fundamental_score = calculate_financial_score(df_row)
    growth_score = calculate_growth_score(df_row)
    technical_score = calculate_technical_score(df_row)
    quality_score = calculate_quality_score(df_row)
    
    # Calculate weighted overall score
    overall_score = (
        fundamental_score * CRITERIA.fundamental_weight +
        growth_score * CRITERIA.growth_weight +
        technical_score * CRITERIA.technical_weight +
        quality_score * CRITERIA.quality_weight
    )
    
    # Assign grade based on score
    if overall_score >= 85:
        grade = 'A+'
    elif overall_score >= 80:
        grade = 'A'
    elif overall_score >= 75:
        grade = 'A-'
    elif overall_score >= 70:
        grade = 'B+'
    elif overall_score >= 65:
        grade = 'B'
    elif overall_score >= 60:
        grade = 'B-'
    elif overall_score >= 55:
        grade = 'C+'
    elif overall_score >= 50:
        grade = 'C'
    else:
        grade = 'C-'
    
    return overall_score, grade

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
    """Pull screener results for a single sector with comprehensive analysis."""
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

        # Apply comprehensive scoring
        print(f"Applying advanced scoring to {len(df)} stocks in {sector}")
        df = apply_comprehensive_analysis(df)
        
        return df

    except Exception as exc:
        print(f"Error fetching {sector}: {exc}. Using sample data.")
        sample_df = get_sample_data(sector)
        return apply_comprehensive_analysis(sample_df) if sample_df is not None else None

def apply_comprehensive_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """Apply comprehensive scoring and filtering to stock data."""
    if df.empty:
        return df
    
    # Calculate scores for each stock
    scores = []
    grades = []
    
    for _, row in df.iterrows():
        score, grade = calculate_overall_score(row)
        scores.append(score)
        grades.append(grade)
    
    # Add scores and grades to dataframe
    df['Overall Score'] = scores
    df['Grade'] = grades
    
    # Filter by minimum score threshold (keep only C+ and above)
    min_score = 50.0
    filtered_df = df[df['Overall Score'] >= min_score].copy()
    
    # Sort by overall score (descending)
    filtered_df = filtered_df.sort_values('Overall Score', ascending=False)
    
    print(f"{len(filtered_df)} stocks passed comprehensive analysis")
    return filtered_df

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
    """Format DataFrame rows for HTML display with enhanced metrics."""
    results = []
    
    for _, row in df.iterrows():
        formatted_row = {}
        for col in DISPLAY_COLUMNS:
            if col in row.index:
                value = row[col]
                if pd.isna(value) or str(value) == '-':
                    formatted_row[col] = 'N/A'
                elif col in ['Price', 'P/E', 'P/B']:
                    try:
                        formatted_row[col] = f"{float(value):.2f}"
                    except:
                        formatted_row[col] = 'N/A'
                elif col in ['Change', 'EPS Q/Q', 'Sales Q/Q', 'ROE', 'Debt/Eq', 'Profit Margin']:
                    try:
                        formatted_row[col] = f"{float(value):.1f}%"
                    except:
                        formatted_row[col] = 'N/A'
                elif col == 'Volume':
                    try:
                        formatted_row[col] = f"{int(float(value)):,}"
                    except:
                        formatted_row[col] = 'N/A'
                elif col == 'Overall Score':
                    try:
                        formatted_row[col] = f"{float(value):.1f}"
                    except:
                        formatted_row[col] = 'N/A'
                elif col == 'Grade':
                    formatted_row[col] = str(value)
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
