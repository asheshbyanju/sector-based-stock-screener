# Sector-Based Growth Stock Screener

A Python CLI tool that scans all major US market sectors using Finviz's free screener to surface high-conviction growth stocks — no API key, no UI, just clean terminal output and a CSV export.

---

## Strategy Overview

| Category | Filter | Value | Rationale |
|---|---|---|---|
| Descriptive | Market Cap | Mid Cap (Over $2B) | Institutional liquidity |
| Descriptive | Price | Over $10 | Excludes penny stocks |
| Descriptive | Avg Volume | Over 500K | Easy entry/exit |
| Fundamental | EPS Q/Q | Over 20% | Earnings acceleration |
| Fundamental | Sales Q/Q | Over 20% | Demand-driven growth |
| Fundamental | ROE | Over 15% | Management efficiency |
| Fundamental | Debt/Equity | Under 1 | Financial solvency |
| Technical | SMA200 | Price above | Confirmed Stage 2 uptrend |
| Technical | RSI (14) | 40–70 | Momentum, not overbought |

Sectors covered: Technology, Healthcare, Financial, Consumer Cyclical, Industrials, Communication Services, Energy, Utilities, Basic Materials, Real Estate, Consumer Defensive.

---

## Requirements

- Python **3.10 or higher** (uses `X | Y` type union syntax)
- pip (comes bundled with Python)
- Internet connection (fetches live data from Finviz)

---

## Installation

### 1. Clone or download the project

```bash
# If you have git
git clone <your-repo-url>
cd stock-screener

# Or just place stock_screener.py in a folder of your choice
```

### 2. (Recommended) Create a virtual environment

```bash
python -m venv venv

# Activate it:
# macOS / Linux
source venv/bin/activate

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Windows (PowerShell)
venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install finvizfinance pandas
```

That's it — no other packages required.

---

## Usage

```bash
python stock_screener.py
```

### What happens

1. The script iterates through all 11 sectors.
2. For each sector it applies the full growth filter set against the live Finviz screener.
3. Results are ranked by **Perf Week** (1-week price performance) and the **top 5** stocks per sector are printed to the terminal.
4. A timestamped CSV (`growth_screener_YYYYMMDD_HHMMSS.csv`) is written to the current directory containing every stock that passed the filters.

### Sample terminal output

```
══════════════════════════════════════════════════════════════════════
  📊  TECHNOLOGY  —  Top 5 stocks
══════════════════════════════════════════════════════════════════════
 Ticker  Company               Sector       Price  Change   Perf Week ...
  NVDA   NVIDIA Corporation    Technology  120.50   1.23%      4.51% ...
  ...
```

---

## Configuration

All tuneable parameters live at the top of `stock_screener.py`:

| Variable | Default | Description |
|---|---|---|
| `TOP_N` | `5` | How many stocks to show per sector |
| `RANK_BY` | `'Perf Week'` | Column used for ranking (`'EPS next Y'` is another good choice) |
| `DELAY_SECONDS` | `1` | Pause between sector requests (be polite to Finviz) |
| `BASE_FILTERS` | see code | All Finviz filter keys/values — edit to tighten or relax criteria |

### Changing the ranking column

Open `stock_screener.py` and change:

```python
RANK_BY = 'EPS next Y'   # Rank by forward EPS growth estimate instead
```

### Relaxing a filter

To lower the EPS Q/Q threshold from 20% to 10%:

```python
BASE_FILTERS = {
    ...
    'eps_epsq_growthqoq': 'o10',   # was 'o20'
    ...
}
```

---

## Output Files

| File | Description |
|---|---|
| `growth_screener_<timestamp>.csv` | All passing stocks, all sectors, full column set |

Open the CSV in Excel, Google Sheets, or any data tool for further analysis.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError: finvizfinance` | Run `pip install finvizfinance` |
| `No results for sector: X` | Filters are very strict — try loosening `EPS Q/Q` or `Sales Q/Q` |
| `ConnectionError` / timeout | Check your internet connection; Finviz may be temporarily unavailable |
| Script runs but CSV is empty | All sectors returned zero results — see relaxing filters above |
| `SyntaxError` on `X \| Y` | You're on Python < 3.10; upgrade or change `pd.DataFrame | None` to `Optional[pd.DataFrame]` |

---

## Disclaimer

This tool is for **educational and research purposes only**. It is not financial advice. Always do your own due diligence before making any investment decisions.
