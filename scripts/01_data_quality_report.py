"""Step 1 - Data profiling of the RAW file (Ch6: data integrity).
Checks: missing values, duplicates, data types, text inconsistencies, invalid values, date formats, outliers.
Output: reports/data_quality_report.md + printed summary."""
import numpy as np
import pandas as pd
from common import read_raw, parse_dates, md_table, REPORTS

df = read_raw()
n = len(df)
md = ["# Data Quality Report (raw data)", "", f"Source file: `data/raw/superstore.csv` - {n:,} rows x {df.shape[1]} columns", ""]

# 1. Data types and missing values per column
prof = pd.DataFrame({
    "dtype": df.dtypes.astype(str),
    "missing": df.isna().sum(),
    "missing_%": (df.isna().mean() * 100).round(2),
    "unique": df.nunique(),
})
md += ["## 1. Data types and missing values", md_table(prof, index=True).replace("| index |", "| column |"), ""]

# 2. Stray / empty rows (rows where every business column is empty, e.g. appended from another Excel sheet)
business_cols = [c for c in df.columns if c not in ("Row ID", "Order ID")]
empty_rows = int(df[business_cols].isna().all(axis=1).sum())
non_numeric_rowid = int(pd.to_numeric(df["Row ID"], errors="coerce").isna().sum())

# 3. Duplicates
full_dups = int(df.duplicated().sum())
rowid_dups = int(df["Row ID"].duplicated().sum())
real = df[~df[business_cols].isna().all(axis=1)]
dups_real = int(real.duplicated().sum())
md += ["## 2. Duplicates and stray rows",
       f"- Completely empty business rows (stray rows, no Order Date/Sales/...): **{empty_rows}**",
       f"- Non-numeric `Row ID` values: **{non_numeric_rowid}**",
       f"- Fully duplicated rows (all columns identical): **{full_dups}**  (among non-empty rows: **{dups_real}**)",
       f"- Duplicated `Row ID` values: **{rowid_dups}**", ""]

# 4. Text inconsistencies (whitespace / casing variants)
rows = []
for c in ["Ship Mode", "Segment", "Country", "City", "State", "Region", "Category", "Sub-Category"]:
    s = real[c].dropna().astype(str)
    spaces = int((s != s.str.strip()).sum() + s.str.contains(r"\s{2,}").sum())
    raw_levels = s.nunique()
    norm_levels = s.str.strip().str.replace(r"\s+", " ", regex=True).str.lower().nunique()
    rows.append({"column": c, "values_with_extra_spaces": spaces, "distinct_raw": raw_levels,
                 "distinct_normalised": norm_levels, "casing_variants": raw_levels - norm_levels})
md += ["## 3. Text consistency (spaces / casing)", md_table(pd.DataFrame(rows)), ""]

# 5. Date formats and parseability
od = parse_dates(real["Order Date"])
sd = parse_dates(real["Ship Date"])
bad_od = int(od.isna().sum() - real["Order Date"].isna().sum())
fmt_counts = real["Order Date"].dropna().astype(str).str.replace(r"\d", "9", regex=True).value_counts().head(6)
md += ["## 4. Dates",
       f"- Order Date range: {od.min().date()} to {od.max().date()}",
       f"- Unparseable Order Dates (after trying several formats): **{bad_od}**",
       f"- Ship Date before Order Date: **{int((sd < od).sum())}**",
       "- Date string patterns seen (9 = a digit):", ""]
md += [f"  - `{k}`: {v:,}" for k, v in fmt_counts.items()] + [""]

# 6. Invalid numeric values
q = pd.to_numeric(real["Quantity"], errors="coerce")
sa = pd.to_numeric(real["Sales"], errors="coerce")
di = pd.to_numeric(real["Discount"], errors="coerce")
md += ["## 5. Invalid values (business rules)",
       f"- Quantity <= 0: **{int((q <= 0).sum())}**",
       f"- Sales <= 0: **{int((sa <= 0).sum())}**",
       f"- Discount outside 0..1: **{int(((di < 0) | (di > 1)).sum())}**",
       f"- Negative Profit rows (valid, loss-making orders): {int((real['Profit'] < 0).sum()):,}", ""]

# 7. Outliers with the IQR rule (kept, only flagged)
rows = []
for c in ["Sales", "Quantity", "Discount", "Profit"]:
    x = pd.to_numeric(real[c], errors="coerce").dropna()
    q1, q3 = x.quantile([.25, .75])
    lo, hi = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
    rows.append({"column": c, "Q1": q1, "Q3": q3, "lower_fence": lo, "upper_fence": hi,
                 "outliers": int(((x < lo) | (x > hi)).sum()), "skew": x.skew()})
md += ["## 6. Outliers (IQR rule, flagged not removed)", md_table(pd.DataFrame(rows)), ""]

# 8. Referential consistency
cust = real.groupby("Customer ID")["Customer Name"].nunique()
prod = real.groupby("Product ID")["Product Name"].nunique()
md += ["## 7. Key consistency",
       f"- Customer IDs with more than one name: **{int((cust > 1).sum())}**",
       f"- Product IDs with more than one product name: **{int((prod > 1).sum())}** (handled in the star schema)",
       f"- Postal Code stored as `{df['Postal Code'].dtype}` (should be text; leading zeros are lost)", ""]

(REPORTS / "data_quality_report.md").write_text("\n".join(md), encoding="utf-8")
print(f"[01] rows={n:,} stray_empty_rows={empty_rows} full_duplicates={full_dups} "
      f"missing_postal={int(real['Postal Code'].isna().sum())} unparseable_dates={bad_od}")
print("[01] wrote reports/data_quality_report.md")
