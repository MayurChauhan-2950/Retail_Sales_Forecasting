"""Shared helpers: folder paths, raw-file loader (utf-8 then latin-1), date parser, markdown tables."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "superstore.csv"
STAGING = ROOT / "data" / "staging"
CLEAN = ROOT / "data" / "clean"
CURATED = ROOT / "data" / "curated"
FORECAST = ROOT / "data" / "forecast"
REPORTS = ROOT / "reports"
FIGS = REPORTS / "figures"
for _p in (STAGING, CLEAN, CURATED, FORECAST, REPORTS, FIGS):
    _p.mkdir(parents=True, exist_ok=True)

DATE_FORMATS = ["%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%b %d, %Y", "%d %b %Y"]


def read_raw():
    """Read the raw Superstore CSV. The Kaggle original is often latin-1, so fall back to it."""
    try:
        return pd.read_csv(RAW_FILE, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(RAW_FILE, encoding="latin-1")


def parse_dates(series):
    """Parse dates that may be in mixed formats: try each known format on the still-unparsed values."""
    s = series.astype("string").str.strip()
    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")
    for fmt in DATE_FORMATS:
        todo = out.isna() & s.notna()
        if not todo.any():
            break
        out[todo] = pd.to_datetime(s[todo], format=fmt, errors="coerce")
    return out


def md_table(df, index=False):
    """Tiny DataFrame -> markdown table (avoids needing the 'tabulate' package)."""
    d = df.reset_index() if index else df
    cols = [str(c) for c in d.columns]
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join(["---"] * len(cols)) + "|"]
    for row in d.itertuples(index=False):
        cells = []
        for v in row:
            cells.append(f"{v:,.4f}".rstrip("0").rstrip(".") if isinstance(v, float) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def monthly_sales(df):
    """Monthly total sales series (month-start index) from a clean dataframe with 'Order Date' and 'Sales'."""
    s = df.set_index("Order Date")["Sales"].resample("MS").sum()
    s.index.freq = "MS"
    return s
