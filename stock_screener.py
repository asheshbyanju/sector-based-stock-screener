"""
Sector-Based Growth Stock Screener
Uses finvizfinance to screen stocks across all major market sectors
based on a high-conviction growth strategy.
"""

import pandas as pd
from finvizfinance.screener.overview import Overview
from datetime import datetime
import sys
import time
from typing import Optional


# ─────────────────────────────────────────────
# CONFIGURATION
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

# Finviz filter keys and values
BASE_FILTERS = {
    # Descriptive
    'Market Cap.': 'Mid ($2bln to $10bln)',            # Mid Cap (Over $2B)
    'Price': 'Over $10',             # Price Over $10
    'Average Volume': 'Over 500K',   # Average Volume Over 500K

    # Fundamental
    'Return on Equity': 'Over +15%',           # ROE Over 15%

    # Technical
    '200-Day Simple Moving Average': 'Price above SMA200',  # Price above SMA200
}

# Columns to display in the output summary
DISPLAY_COLUMNS = ['Ticker', 'Company', 'Sector', 'Price', 'Change', 'Volume',
                   'P/E', 'EPS (ttm)', 'EPS next Y', 'EPS Q/Q', 'Sales Q/Q',
                   'ROE', 'Debt/Eq', 'Perf Week']

TOP_N = 5          # Top stocks per sector
RANK_BY = 'Perf Week'  # Column used for ranking within each sector
DELAY_SECONDS = 1  # Polite delay between sector requests


# ─────────────────────────────────────────────
# HELPERS
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
    """
    Pull screener results for a single sector.
    Returns a DataFrame or None if no results / error.
    """
    foverview = Overview()
    filters = build_filters(sector)

    try:
        foverview.set_filter(filters_dict=filters)
        df = foverview.screener_view(verbose=0)

        if df is None or df.empty:
            print(f"  ⚠  No results for sector: {sector}")
            return None

        return df

    except Exception as exc:
        print(f"  ✖  Error fetching {sector}: {exc}")
        return None


def rank_and_trim(df: pd.DataFrame, rank_col: str = RANK_BY, top_n: int = TOP_N) -> pd.DataFrame:
    """Sort by rank_col descending and return top_n rows."""
    if rank_col not in df.columns:
        # Fallback: just return first N rows
        return df.head(top_n).reset_index(drop=True)

    df = df.copy()
    df['_sort_key'] = clean_numeric(df[rank_col])
    df = df.sort_values('_sort_key', ascending=False, na_position='last')
    df = df.drop(columns=['_sort_key'])
    return df.head(top_n).reset_index(drop=True)


def print_sector_table(sector: str, df: pd.DataFrame) -> None:
    """Pretty-print a sector result table to stdout with improved formatting."""
    print(f"\n{'═' * 80}")
    print(f"  📊  {sector.upper()}  —  Top {len(df)} stocks")
    print(f"{'═' * 80}")

    # Only keep columns that actually exist in this result set
    cols = [c for c in DISPLAY_COLUMNS if c in df.columns]
    display = df[cols].copy()

    # Format numeric columns for better readability
    for col in ['Price', 'Change', 'Volume', 'P/E', 'EPS (ttm)', 'EPS next Y', 'EPS Q/Q', 
                'Sales Q/Q', 'ROE', 'Debt/Eq', 'Perf Week']:
        if col in display.columns:
            if col in ['Price', 'P/E', 'EPS (ttm)', 'EPS next Y']:
                display[col] = display[col].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) and str(x) != '-' else "N/A")
            elif col in ['Change', 'EPS Q/Q', 'Sales Q/Q', 'ROE', 'Debt/Eq', 'Perf Week']:
                display[col] = display[col].apply(lambda x: f"{float(x):.1f}%" if pd.notna(x) and str(x) != '-' else "N/A")
            elif col == 'Volume':
                display[col] = display[col].apply(lambda x: f"{int(float(x)):,}" if pd.notna(x) and str(x) != '-' else "N/A")

    # Format for better table display
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 120)
    pd.set_option('display.max_colwidth', 25)
    pd.set_option('display.float_format', lambda x: '%.2f' if pd.notna(x) else 'N/A')
    
    # Print formatted table
    print(display.to_string(index=False, justify='center'))


def save_results(all_results: list) -> None:
    """Save combined results to a CSV file."""
    if not all_results:
        print("\nNo results to save.")
        return

    combined = pd.concat([r['df'] for r in all_results], ignore_index=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"growth_screener_{timestamp}.csv"
    combined.to_csv(filename, index=False)
    print(f"\n✅  Results saved to: {filename}")
    print(f"    Total stocks found: {len(combined)}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def display_sector_menu() -> str:
    """Display sector selection menu and return user's choice."""
    print("\n" + "=" * 70)
    print("  SELECT SECTOR TO SCAN")
    print("=" * 70)
    
    for i, sector in enumerate(SECTORS, 1):
        print(f"  {i:2d}. {sector}")
    print(f"  {len(SECTORS)+1:2d}. Scan ALL sectors")
    print("=" * 70)
    
    while True:
        try:
            choice = input(f"\nEnter your choice (1-{len(SECTORS)+1}): ").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(SECTORS):
                return SECTORS[choice_num - 1]
            elif choice_num == len(SECTORS) + 1:
                return "ALL"
            else:
                print(f"⚠  Please enter a number between 1 and {len(SECTORS)+1}")
        except ValueError:
            print("⚠  Please enter a valid number")


def main() -> None:
    print("=" * 70)
    print("  SECTOR-BASED GROWTH STOCK SCREENER")
    print(f"  Run date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Strategy : High-Conviction Growth (Mid-Cap+)")
    print(f"  Ranking  : {RANK_BY}  |  Top {TOP_N} per sector")
    print("=" * 70)

    # Get user sector selection
    selected_sector = display_sector_menu()
    
    if selected_sector == "ALL":
        sectors_to_scan = SECTORS
        print(f"\n🚀  Scanning ALL {len(SECTORS)} sectors...")
    else:
        sectors_to_scan = [selected_sector]
        print(f"\n🎯  Scanning selected sector: {selected_sector}")

    all_results = []
    sectors_with_hits = 0

    for sector in sectors_to_scan:
        print(f"\n🔍  Scanning sector: {sector} …")
        df = fetch_sector(sector)

        if df is not None and not df.empty:
            top_df = rank_and_trim(df, rank_col=RANK_BY, top_n=TOP_N)
            print_sector_table(sector, top_df)
            all_results.append({'sector': sector, 'df': top_df})
            sectors_with_hits += 1
        
        # Be a good citizen — don't hammer the endpoint
        time.sleep(DELAY_SECONDS)

    # ── Summary ──────────────────────────────
    print(f"\n\n{'═' * 70}")
    print(f"  SCAN COMPLETE")
    print(f"  Sectors scanned : {len(sectors_to_scan)}")
    print(f"  Sectors with hits: {sectors_with_hits}")
    print(f"{'═' * 70}")

    if all_results:
        save_results(all_results)
    else:
        print("\n⚠  No stocks passed all filters across any sector.")
        print("   Consider relaxing one or more criteria and re-running.")
        sys.exit(1)


if __name__ == '__main__':
    main()
