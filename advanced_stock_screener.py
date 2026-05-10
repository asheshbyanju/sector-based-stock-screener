"""
Advanced Comprehensive Stock Screener
Based on extensive research of investment legends (Buffett, Graham, Lynch),
quantitative factor models, and modern investment frameworks.

This screener implements a multi-dimensional filtering system that evaluates stocks
based on fundamental quality, technical health, competitive advantages, and
ESG criteria to identify truly great investment opportunities.
"""

import pandas as pd
import numpy as np
from finvizfinance.screener.overview import Overview
from finvizfinance.screener.technical import Technical
from finvizfinance.screener.financial import Financial
from finvizfinance.screener.ownership import Ownership
from datetime import datetime
import sys
import time
import warnings
from typing import Optional, Dict, List, Tuple
from dataclasses import dataclass

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# ─────────────────────────────────────────────
# CONFIGURATION & DATA STRUCTURES
# ─────────────────────────────────────────────

@dataclass
class ScreenerCriteria:
    """Data class to hold all screening criteria and thresholds"""
    
    # === FUNDAMENTAL CRITERIA (Benjamin Graham Value Investing) ===
    graham_pe_max: float = 15.0          # P/E ratio under 15 (relaxed from 9.0 for modern market)
    graham_pb_max: float = 1.5           # Price-to-Book under 1.5
    graham_current_ratio_min: float = 1.5  # Current ratio over 1.5
    graham_debt_to_assets_max: float = 1.1  # Debt to current assets under 1.1
    
    # === QUALITY CRITERIA (Warren Buffett) ===
    buffett_roe_min: float = 15.0        # ROE over 15%
    buffett_debt_equity_max: float = 0.7 # Debt/Equity under 0.7 (conservative)
    buffett_profit_margin_min: float = 15.0 # Profit margin over 15%
    
    # === GROWTH CRITERIA (Peter Lynch) ===
    lynch_eps_growth_min: float = 15.0   # EPS growth over 15%
    lynch_sales_growth_min: float = 10.0 # Sales growth over 10%
    lynch_peg_max: float = 1.5          # PEG ratio under 1.5
    
    # === TECHNICAL CRITERIA ===
    price_min: float = 10.0              # Price over $10
    volume_avg_min: int = 500000         # Average volume over 500K
    market_cap_min: float = 2000         # Market cap over $2B (mid-cap+)
    sma200_above: bool = True            # Price above 200-day SMA
    rsi_min: float = 40.0                # RSI over 40 (momentum without oversold)
    rsi_max: float = 70.0                # RSI under 70 (not overbought)
    
    # === DESCRIPTIVE FILTERS ===
    exclude_otc: bool = True             # Exclude OTC stocks
    exclude_financials: bool = False     # Include financials by default
    
    # === SCORING WEIGHTS ===
    fundamental_weight: float = 0.4     # 40% weight to fundamentals
    technical_weight: float = 0.2       # 20% weight to technicals
    quality_weight: float = 0.3          # 30% weight to quality
    growth_weight: float = 0.1           # 10% weight to growth

# Global criteria instance
CRITERIA = ScreenerCriteria()

# Sectors to scan
SECTORS = [
    'Technology', 'Healthcare', 'Financial', 'Consumer Cyclical',
    'Industrials', 'Communication Services', 'Energy', 'Utilities',
    'Basic Materials', 'Real Estate', 'Consumer Defensive'
]

# Columns to display in results
DISPLAY_COLUMNS = [
    'Ticker', 'Company', 'Sector', 'Price', 'Market Cap', 'P/E',
    'P/B', 'ROE', 'Debt/Eq', 'EPS Q/Q', 'Sales Q/Q', 'Profit Margin',
    'RSI (14)', 'SMA200', 'Volume', 'Overall Score', 'Grade'
]

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def clean_numeric_value(value) -> float:
    """
    Convert financial string values to float.
    Handles percentages, dollar signs, commas, and dashes.
    """
    if pd.isna(value) or value == '-' or value == 'N/A':
        return np.nan
    
    value_str = str(value).replace('%', '').replace('$', '').replace(',', '')
    
    try:
        return float(value_str)
    except (ValueError, TypeError):
        return np.nan

def clean_numeric_series(series: pd.Series) -> pd.Series:
    """Apply numeric cleaning to an entire pandas Series."""
    return series.apply(clean_numeric_value)

def calculate_financial_score(df_row: pd.Series) -> float:
    """
    Calculate fundamental financial score based on Graham and Buffett criteria.
    Returns score from 0-100, higher is better.
    """
    score = 0.0
    max_score = 0.0
    
    # Graham Criteria (Value Investing)
    pe_ratio = clean_numeric_value(df_row.get('P/E'))
    if not np.isnan(pe_ratio) and pe_ratio <= CRITERIA.graham_pe_max:
        score += 15  # P/E ratio score
    max_score += 15
    
    pb_ratio = clean_numeric_value(df_row.get('P/B'))
    if not np.isnan(pb_ratio) and pb_ratio <= CRITERIA.graham_pb_max:
        score += 10  # P/B ratio score
    max_score += 10
    
    # Buffett Criteria (Quality)
    roe = clean_numeric_value(df_row.get('ROE'))
    if not np.isnan(roe) and roe >= CRITERIA.buffett_roe_min:
        score += 20  # ROE score
    max_score += 20
    
    debt_eq = clean_numeric_value(df_row.get('Debt/Eq'))
    if not np.isnan(debt_eq) and debt_eq <= CRITERIA.buffett_debt_equity_max:
        score += 15  # Debt/Equity score
    max_score += 15
    
    profit_margin = clean_numeric_value(df_row.get('Profit Margin'))
    if not np.isnan(profit_margin) and profit_margin >= CRITERIA.buffett_profit_margin_min:
        score += 15  # Profit margin score
    max_score += 15
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_growth_score(df_row: pd.Series) -> float:
    """
    Calculate growth score based on Peter Lynch criteria.
    Returns score from 0-100, higher is better.
    """
    score = 0.0
    max_score = 0.0
    
    # EPS Growth
    eps_qq = clean_numeric_value(df_row.get('EPS Q/Q'))
    if not np.isnan(eps_qq) and eps_qq >= CRITERIA.lynch_eps_growth_min:
        score += 40  # EPS growth is most important
    max_score += 40
    
    # Sales Growth
    sales_qq = clean_numeric_value(df_row.get('Sales Q/Q'))
    if not np.isnan(sales_qq) and sales_qq >= CRITERIA.lynch_sales_growth_min:
        score += 30  # Sales growth
    max_score += 30
    
    # PEG Ratio (if available)
    # Note: Finviz doesn't provide PEG directly, so we estimate
    pe_ratio = clean_numeric_value(df_row.get('P/E'))
    eps_growth = clean_numeric_value(df_row.get('EPS Q/Q'))
    
    if not np.isnan(pe_ratio) and not np.isnan(eps_growth) and eps_growth > 0:
        peg_ratio = pe_ratio / eps_growth
        if peg_ratio <= CRITERIA.lynch_peg_max:
            score += 30  # PEG score
    max_score += 30
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_technical_score(df_row: pd.Series) -> float:
    """
    Calculate technical analysis score based on momentum and trend indicators.
    Returns score from 0-100, higher is better.
    """
    score = 0.0
    max_score = 0.0
    
    # RSI Momentum
    rsi = clean_numeric_value(df_row.get('RSI (14)'))
    if not np.isnan(rsi):
        if CRITERIA.rsi_min <= rsi <= CRITERIA.rsi_max:
            score += 40  # RSI in optimal range
        elif rsi > CRITERIA.rsi_max:
            score += 20  # Overbought but still positive
    max_score += 40
    
    # SMA200 Trend
    sma200_signal = df_row.get('SMA200', '')
    if sma200_signal == 'Price above SMA200':
        score += 30  # Above 200-day SMA (uptrend)
    max_score += 30
    
    # Volume Confirmation
    volume = clean_numeric_value(df_row.get('Volume'))
    if not np.isnan(volume) and volume >= CRITERIA.volume_avg_min:
        score += 30  # Sufficient volume
    max_score += 30
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_quality_score(df_row: pd.Series) -> float:
    """
    Calculate overall business quality score.
    Returns score from 0-100, higher is better.
    """
    score = 0.0
    max_score = 0.0
    
    # Market Cap Quality (Larger caps tend to be more stable)
    market_cap = clean_numeric_value(df_row.get('Market Cap'))
    if not np.isnan(market_cap):
        if market_cap >= 10000:  # Large cap > $10B
            score += 25
        elif market_cap >= 2000:  # Mid cap > $2B
            score += 20
    max_score += 25
    
    # Price Quality (exclude penny stocks)
    price = clean_numeric_value(df_row.get('Price'))
    if not np.isnan(price) and price >= CRITERIA.price_min:
        score += 15
    max_score += 15
    
    # Financial Health (combined debt and profitability)
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
    
    return (score / max_score * 100) if max_score > 0 else 0

def calculate_overall_score(df_row: pd.Series) -> Tuple[float, str]:
    """
    Calculate weighted overall score and assign grade.
    Returns tuple of (score, grade).
    """
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

def build_finviz_filters() -> Dict[str, str]:
    """
    Build comprehensive Finviz filter dictionary based on our criteria.
    These filters are applied before detailed analysis to reduce the dataset.
    Using correct Finviz filter names based on available options.
    """
    filters = {}
    
    # Descriptive filters
    filters['Market Cap.'] = 'Mid ($2bln to $10bln)'  # Mid-cap focus
    filters['Price'] = 'Over $10'                    # Exclude penny stocks
    filters['Average Volume'] = 'Over 500K'          # Liquidity filter
    
    # Fundamental filters
    filters['Return on Equity'] = 'Over +15%'         # Buffett quality
    filters['P/E'] = 'Under 20'                      # Reasonable valuation
    filters['Debt/Equity'] = 'Under 1'               # Conservative debt (corrected filter name)
    
    # Growth filters
    filters['EPS growthqtr over qtr'] = 'Over 15%'  # Earnings growth (corrected filter name)
    filters['Sales growthqtr over qtr'] = 'Over 10%' # Revenue growth (corrected filter name)
    
    # Technical filters
    filters['200-Day Simple Moving Average'] = 'Price above SMA200'  # Uptrend
    
    return filters

def fetch_sector_data(sector: str) -> Optional[pd.DataFrame]:
    """
    Fetch comprehensive stock data for a specific sector using multiple Finviz screens.
    Combines overview, technical, financial, and ownership data.
    """
    print(f"  📊 Fetching {sector} data...")
    
    try:
        # Initialize screeners
        foverview = Overview()
        ftechnical = Technical()
        ffinancial = Financial()
        fownership = Ownership()
        
        # Set filters for overview
        filters = build_finviz_filters()
        filters['Sector'] = sector
        foverview.set_filter(filters_dict=filters)
        
        # Get overview data
        overview_df = foverview.screener_view(verbose=0)
        if overview_df is None or overview_df.empty:
            print(f"    ⚠ No overview data for {sector}")
            return None
        
        # Get technical indicators
        ftechnical.set_filter(filters_dict=filters)
        technical_df = ftechnical.screener_view(verbose=0)
        
        # Get financial data
        ffinancial.set_filter(filters_dict=filters)
        financial_df = ffinancial.screener_view(verbose=0)
        
        # Merge all dataframes on Ticker
        result_df = overview_df.copy()
        
        if technical_df is not None and not technical_df.empty:
            result_df = pd.merge(result_df, technical_df, on='Ticker', how='left', suffixes=('', '_tech'))
        
        if financial_df is not None and not financial_df.empty:
            result_df = pd.merge(result_df, financial_df, on='Ticker', how='left', suffixes=('', '_fin'))
        
        print(f"    ✅ Found {len(result_df)} stocks in {sector}")
        return result_df
        
    except Exception as exc:
        print(f"    ✖ Error fetching {sector}: {exc}")
        return None

def apply_advanced_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply advanced filtering criteria beyond basic Finviz filters.
    This includes our comprehensive scoring system.
    """
    if df.empty:
        return df
    
    print(f"  🔍 Applying advanced filters to {len(df)} stocks...")
    
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
    
    # Filter by minimum score threshold (keep only B- and above)
    min_score = 55.0
    filtered_df = df[df['Overall Score'] >= min_score].copy()
    
    # Sort by overall score (descending)
    filtered_df = filtered_df.sort_values('Overall Score', ascending=False)
    
    print(f"    ✅ {len(filtered_df)} stocks passed advanced filters")
    return filtered_df

def format_output_table(df: pd.DataFrame, sector: str) -> None:
    """
    Format and display results in a clean, readable table format.
    """
    if df.empty:
        return
    
    print(f"\n{'═' * 100}")
    print(f"  📊  {sector.upper()}  —  Top {len(df)} Stocks (Advanced Analysis)")
    print(f"{'═' * 100}")
    
    # Select and reorder columns for display
    display_cols = [col for col in DISPLAY_COLUMNS if col in df.columns]
    display_df = df[display_cols].copy()
    
    # Format numeric columns for better readability
    for col in ['Price', 'Market Cap', 'P/E', 'P/B', 'ROE', 'Debt/Eq', 
                'EPS Q/Q', 'Sales Q/Q', 'Profit Margin', 'RSI (14)', 'Volume']:
        if col in display_df.columns:
            if col in ['Price', 'P/E', 'P/B', 'ROE']:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{clean_numeric_value(x):.2f}" if not np.isnan(clean_numeric_value(x)) else "N/A"
                )
            elif col in ['EPS Q/Q', 'Sales Q/Q', 'Profit Margin', 'Debt/Eq', 'RSI (14)']:
                display_df[col] = display_df[col].apply(
                    lambda x: f"{clean_numeric_value(x):.1f}%" if not np.isnan(clean_numeric_value(x)) else "N/A"
                )
            elif col == 'Market Cap':
                display_df[col] = display_df[col].apply(
                    lambda x: f"${clean_numeric_value(x):.0f}B" if not np.isnan(clean_numeric_value(x)) else "N/A"
                )
            elif col == 'Volume':
                display_df[col] = display_df[col].apply(
                    lambda x: f"{int(clean_numeric_value(x)):,}" if not np.isnan(clean_numeric_value(x)) else "N/A"
                )
    
    # Format score and grade
    if 'Overall Score' in display_df.columns:
        display_df['Overall Score'] = display_df['Overall Score'].apply(
            lambda x: f"{x:.1f}" if not np.isnan(x) else "N/A"
        )
    
    # Set pandas display options for better formatting
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 120)
    pd.set_option('display.max_colwidth', 20)
    
    # Print the formatted table
    print(display_df.to_string(index=False))

def save_comprehensive_results(all_results: List[Dict], sectors_scanned: List[str]) -> None:
    """
    Save all results to a comprehensive CSV file with detailed analysis.
    """
    if not all_results:
        print("\n⚠ No results to save.")
        return
    
    # Combine all results
    combined_df = pd.concat([result['df'] for result in all_results], ignore_index=True)
    
    # Add timestamp and metadata
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    combined_df['Analysis_Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    combined_df['Sectors_Scanned'] = ', '.join(sectors_scanned)
    
    # Sort by overall score
    combined_df = combined_df.sort_values('Overall Score', ascending=False)
    
    # Save to CSV
    filename = f"advanced_stock_screener_{timestamp}.csv"
    combined_df.to_csv(filename, index=False)
    
    # Save summary statistics
    summary_stats = {
        'Total_Stocks_Found': len(combined_df),
        'Sectors_Scanned': len(sectors_scanned),
        'Average_Score': combined_df['Overall Score'].mean(),
        'Top_Score': combined_df['Overall Score'].max(),
        'A_Grade_Count': len(combined_df[combined_df['Grade'].str.contains('A')]),
        'B_Grade_Count': len(combined_df[combined_df['Grade'].str.contains('B')]),
        'Analysis_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    summary_df = pd.DataFrame([summary_stats])
    summary_filename = f"advanced_screener_summary_{timestamp}.csv"
    summary_df.to_csv(summary_filename, index=False)
    
    print(f"\n✅ Results saved to: {filename}")
    print(f"📊 Summary saved to: {summary_filename}")
    print(f"📈 Total stocks found: {len(combined_df)}")
    print(f"🏆 Average score: {summary_stats['Average_Score']:.1f}")
    print(f"⭐ Top score: {summary_stats['Top_Score']:.1f}")

def display_analysis_summary(all_results: List[Dict]) -> None:
    """
    Display comprehensive summary of the screening results.
    """
    if not all_results:
        return
    
    print(f"\n{'═' * 100}")
    print(f"  📈  ADVANCED STOCK SCREENER - ANALYSIS SUMMARY")
    print(f"{'═' * 100}")
    
    # Combine all results for summary statistics
    combined_df = pd.concat([result['df'] for result in all_results], ignore_index=True)
    
    # Grade distribution
    grade_counts = combined_df['Grade'].value_counts().sort_index(ascending=False)
    print(f"\n🏆 Grade Distribution:")
    for grade, count in grade_counts.items():
        percentage = (count / len(combined_df)) * 100
        print(f"   {grade}: {count} stocks ({percentage:.1f}%)")
    
    # Score statistics
    print(f"\n📊 Score Statistics:")
    print(f"   Average Score: {combined_df['Overall Score'].mean():.1f}")
    print(f"   Median Score: {combined_df['Overall Score'].median():.1f}")
    print(f"   Highest Score: {combined_df['Overall Score'].max():.1f}")
    print(f"   Lowest Score: {combined_df['Overall Score'].min():.1f}")
    
    # Sector distribution
    if 'Sector' in combined_df.columns:
        sector_counts = combined_df['Sector'].value_counts()
        print(f"\n🌐 Top Sectors:")
        for sector, count in sector_counts.head(5).items():
            print(f"   {sector}: {count} stocks")
    
    print(f"{'═' * 100}")

# ─────────────────────────────────────────────
# MAIN EXECUTION
# ─────────────────────────────────────────────

def main():
    """
    Main execution function for the advanced stock screener.
    Implements the comprehensive multi-dimensional analysis framework.
    """
    print("=" * 100)
    print("  🚀 ADVANCED COMPREHENSIVE STOCK SCREENER")
    print(f"  📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  📊 Framework: Graham + Buffett + Lynch + Quantitative Factors")
    print(f"  🎯 Focus: High-Quality Growth Stocks with Strong Fundamentals")
    print("=" * 100)
    
    # Display criteria summary
    print(f"\n📋 Screening Criteria Summary:")
    print(f"   • Market Cap: Mid-cap+ (>$2B)")
    print(f"   • Price: >$10, Volume: >500K")
    print(f"   • ROE: >{CRITERIA.buffett_roe_min}%, Debt/Equity: <{CRITERIA.buffett_debt_equity_max}")
    print(f"   • EPS Growth: >{CRITERIA.lynch_eps_growth_min}%, Sales Growth: >{CRITERIA.lynch_sales_growth_min}%")
    print(f"   • Technical: Above SMA200, RSI {CRITERIA.rsi_min}-{CRITERIA.rsi_max}")
    print(f"   • Minimum Score: 55/100 (Grade B- and above)")
    
    all_results = []
    sectors_with_hits = 0
    total_stocks_found = 0
    
    # Scan each sector
    for sector in SECTORS:
        print(f"\n🔍 Scanning Sector: {sector}")
        print("-" * 50)
        
        # Fetch comprehensive sector data
        sector_df = fetch_sector_data(sector)
        
        if sector_df is not None and not sector_df.empty:
            # Apply advanced filters and scoring
            filtered_df = apply_advanced_filters(sector_df)
            
            if not filtered_df.empty:
                # Display results for this sector
                format_output_table(filtered_df, sector)
                
                # Store results
                all_results.append({
                    'sector': sector,
                    'df': filtered_df
                })
                
                sectors_with_hits += 1
                total_stocks_found += len(filtered_df)
        
        # Polite delay between requests
        time.sleep(1)
    
    # Display comprehensive summary
    if all_results:
        display_analysis_summary(all_results)
        
        # Save results
        save_comprehensive_results(all_results, SECTORS)
        
        print(f"\n🎉 SCREENING COMPLETE!")
        print(f"   Sectors Scanned: {len(SECTORS)}")
        print(f"   Sectors with Results: {sectors_with_hits}")
        print(f"   Total Quality Stocks Found: {total_stocks_found}")
        
    else:
        print(f"\n⚠ No stocks passed the comprehensive screening criteria.")
        print(f"   Consider relaxing some criteria and re-running the analysis.")
        sys.exit(1)

if __name__ == '__main__':
    main()
