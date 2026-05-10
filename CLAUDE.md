# CLAUDE.md — Sector-Based Growth Stock Screener

This file gives Claude (or any AI coding assistant) the full context needed to understand, extend, and debug this project.

---

## Project Purpose

A zero-dependency-UI Python CLI that:
1. Connects to the **Finviz** stock screener via the `finvizfinance` library.
2. Iterates through **11 major US market sectors**.
3. Applies a **high-conviction growth filter set** (mid-cap+, EPS/Sales growth >20%, ROE >15%, D/E <1, above SMA200, RSI 40–70).
4. Ranks passing stocks by weekly performance and prints the **top 5 per sector**.
5. Exports a **timestamped CSV** of all results.

---

## File Structure

```
stock_screener.py   ← single entry-point, all logic lives here
README.md           ← installation and usage guide
CLAUDE.md           ← this file
growth_screener_*.csv  ← generated at runtime, gitignore-worthy
```

---

## Key Dependencies

| Package | Role |
|---|---|
| `finvizfinance` | Wraps the Finviz screener web UI; no API key needed |
| `pandas` | DataFrame manipulation, sorting, CSV export |

Both are pure-Python and install via `pip install finvizfinance pandas`.

---

## Architecture

### Entry point
`main()` orchestrates everything:
- Loops over `SECTORS` list.
- Calls `fetch_sector(sector)` → returns raw DataFrame or None.
- Calls `rank_and_trim(df)` → returns top-N rows sorted by `RANK_BY`.
- Calls `print_sector_table(sector, df)` → pretty-prints to stdout.
- Calls `save_results(all_results)` → writes combined CSV.

### Filter system
`BASE_FILTERS` (dict) holds all Finviz filter key/value pairs. Finviz uses short-code values (e.g., `'o20'` = "over 20%", `'pa'` = "price above"). A per-sector `'sec'` key is merged in at call time by `build_filters(sector)`.

### Numeric sorting
`clean_numeric(series)` strips `%`, `$`, `,` characters and casts to float so percentage columns (like `Perf Week`) sort correctly.

### Error handling
`fetch_sector` wraps the Finviz call in try/except. A sector returning zero rows prints a warning and returns `None`; the loop continues.

---

## Finviz Filter Key Reference

These are the exact keys used in `BASE_FILTERS`. When Finviz changes dropdown options, update the **value** strings here.

```python
'cap':                  'mid'      # Market Cap ≥ $2B
'sh_price':             '10to'     # Price > $10
'sh_avgvol':            '500o'     # Avg Volume > 500K
'eps_epsq_growthqoq':   'o20'      # EPS Q/Q > 20%
'sales_growthqoq':      'o20'      # Sales Q/Q > 20%
'fa_roe':               'o15'      # ROE > 15%
'fa_debteq':            'u1'       # Debt/Equity < 1
'ta_sma200':            'pa'       # Price above SMA200
'ta_rsi':               '40to70'   # RSI 14 between 40–70
'sec':                  <sector>   # Injected per loop iteration
```

If a filter stops working, cross-reference against the Finviz screener URL params at `https://finviz.com/screener.ashx`.

---

## How to Extend This Project

### Add a new filter
Add a key/value pair to `BASE_FILTERS` in `stock_screener.py`. Find the correct key by using browser DevTools on the Finviz screener page and observing the URL query string changes as you toggle dropdowns.

### Change ranking column
Set `RANK_BY` to any column returned by the screener, e.g.:
```python
RANK_BY = 'EPS next Y'   # Forward EPS growth
RANK_BY = 'Change'        # Daily % change
```

### Add more output columns
Append column names to `DISPLAY_COLUMNS`. Only columns present in Finviz's overview response will appear; extras are silently dropped.

### Export to Excel instead of CSV
Replace the `to_csv` call in `save_results()` with:
```python
combined.to_excel(f"growth_screener_{timestamp}.xlsx", index=False)
# Requires: pip install openpyxl
```

### Schedule the screener
Use `cron` (Linux/macOS) or Windows Task Scheduler to run the script daily pre-market:
```bash
# crontab -e
30 8 * * 1-5 /path/to/venv/bin/python /path/to/stock_screener.py >> /path/to/screener.log 2>&1
```

### Add email alerts
After `save_results()`, use Python's `smtplib` or a service like SendGrid to email the CSV.

---

## Known Limitations

- **Rate limiting**: Finviz may throttle requests. `DELAY_SECONDS = 1` between sectors is the polite default; increase if you see connection errors.
- **Data freshness**: Finviz data is delayed ~15 minutes during market hours.
- **Filter accuracy**: `finvizfinance` filter key strings may become stale if Finviz updates its internal API. Check the GitHub repo for the library if filters stop returning expected results.
- **Python version**: The `pd.DataFrame | None` return type hint requires Python 3.10+. On older versions, replace with `Optional[pd.DataFrame]` and import `Optional` from `typing`.

---

## Testing Tips for Claude

- To test without hitting the network, mock `Overview.screener_view()` to return a hardcoded DataFrame.
- The `clean_numeric()` function can be unit-tested independently with a small Series containing mixed `%` and `-` values.
- If asked to add a feature, prefer keeping everything in `stock_screener.py` unless the change is substantial enough to warrant a separate module.
