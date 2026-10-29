"""Step 11 - Data engineering depth (Ch8).
Data dictionary, data-quality scorecard, lineage note, row-count reconciliation, extra OLAP SQL examples,
and a small pre-aggregated table for Power BI.
Outputs: reports/data_dictionary.md, reports/data_quality_scorecard.md, reports/lineage_and_reconciliation.md,
reports/olap_extra_examples.md, data/curated/agg_monthly_category_region.csv (+ data/reconciliation_counts.csv)"""
import sqlite3
import pandas as pd
import numpy as np
from common import read_raw, md_table, CLEAN, CURATED, STAGING, REPORTS, ROOT

raw = read_raw()
stg = pd.read_parquet(STAGING / "stg_superstore_raw.parquet")
clean = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date", "Ship Date"], dtype={"Postal Code": str})
T = {n: pd.read_csv(CURATED / f"{n}.csv", dtype={"Postal Code": str}) for n in
     ["fact_sales", "dim_customer", "dim_product", "dim_geography", "dim_date"]}

# ---------- 1. reconciliation
real_raw = raw.dropna(subset=["Order ID", "Sales"])
rec = pd.DataFrame([
    ("raw file rows", len(raw), "data/raw/superstore.csv"),
    ("  of which stray empty rows (no Order ID/Sales)", len(raw) - len(real_raw), "removed in step 02"),
    ("  of which real order lines", len(real_raw), ""),
    ("staging rows", len(stg), "as-is parquet copy (step 03 extract)"),
    ("clean rows", len(clean), "data/clean/superstore_clean.csv"),
    ("fact_sales rows", len(T["fact_sales"]), "grain = order line"),
    ("dim_customer rows", len(T["dim_customer"]), "= distinct Customer ID in clean"),
    ("dim_product rows", len(T["dim_product"]), "= distinct Product ID in clean"),
    ("dim_geography rows", len(T["dim_geography"]), "= distinct Country/Region/State/City/Postal Code"),
    ("dim_date rows", len(T["dim_date"]), "calendar days incl. ship dates"),
], columns=["stage", "rows", "note"])
checks = pd.DataFrame([
    ("raw - stray rows = clean rows", len(raw) - (len(raw) - len(real_raw)) == len(clean)),
    ("staging rows = raw rows", len(stg) == len(raw)),
    ("clean rows = fact rows", len(clean) == len(T["fact_sales"])),
    ("sum(Sales) clean = fact", abs(clean.Sales.sum() - T["fact_sales"].sales.sum()) < 1e-6),
    ("sum(Profit) clean = fact", abs(clean.Profit.sum() - T["fact_sales"].profit.sum()) < 1e-6),
    ("sum(Quantity) clean = fact", clean.Quantity.sum() == T["fact_sales"].quantity.sum()),
    ("distinct customers clean = dim", clean["Customer ID"].nunique() == len(T["dim_customer"])),
    ("distinct products clean = dim", clean["Product ID"].nunique() == len(T["dim_product"])),
    ("sum(Sales) real raw rows = clean", abs(real_raw.Sales.sum() - clean.Sales.sum()) < 1e-6),
], columns=["reconciliation check", "ok"])
checks["result"] = np.where(checks.ok, "PASS", "FAIL"); checks = checks.drop(columns="ok")
rec.to_csv(ROOT / "data" / "reconciliation_counts.csv", index=False)

# ---------- 2. data-quality scorecard (on clean data; raw completeness shown for contrast)
n = len(clean)
dims = []
def add(dim, rule, passed, total, note=""):
    dims.append({"dimension": dim, "rule": rule, "passing": int(passed), "checked": int(total), "score_%": passed / total * 100, "note": note})
bcols = ["Order Date", "Ship Date", "Customer ID", "Product ID", "Sales", "Quantity", "Discount", "Profit", "Category", "Region", "State"]
add("Completeness", "no nulls in 11 key business columns (clean)", clean[bcols].notna().all(axis=1).sum(), n)
add("Completeness", "Postal Code present (clean, 'Unknown' counts as filled)", clean["Postal Code"].notna().sum(), n, "11 Burlington VT rows set to 'Unknown'")
add("Completeness", "RAW: non-empty business rows", len(real_raw), len(raw), "806 stray rows in the raw copy")
add("Uniqueness", "Row ID unique", clean["Row ID"].is_unique * n, n)
add("Uniqueness", "no fully duplicated rows", n - clean.duplicated().sum(), n)
add("Validity", "Sales > 0", (clean.Sales > 0).sum(), n)
add("Validity", "Quantity >= 1", (clean.Quantity >= 1).sum(), n)
add("Validity", "Discount within [0, 1]", clean.Discount.between(0, 1).sum(), n)
add("Validity", "Ship Date >= Order Date", (clean["Ship Date"] >= clean["Order Date"]).sum(), n)
add("Validity", "Ship Days <= 14", ((clean["Ship Date"] - clean["Order Date"]).dt.days <= 14).sum(), n)
add("Consistency", "Profit margin = Profit/Sales within 1e-3", (np.abs(clean.Profit / clean.Sales - clean["Profit Margin"]) < 1e-3).sum(), n)
pn = clean.groupby("Product ID")["Product Name"].nunique()
add("Consistency", "Product ID maps to exactly one Product Name", (pn == 1).sum(), len(pn), f"{(pn > 1).sum()} Product IDs carry several names (dim_product keeps first)")
cr = clean.groupby("Customer ID")["Customer Name"].nunique()
add("Consistency", "Customer ID maps to exactly one name", (cr == 1).sum(), len(cr))
cs = clean.groupby("Customer ID")["Segment"].nunique()
add("Consistency", "Customer ID maps to exactly one Segment", (cs == 1).sum(), len(cs))
sr = clean.groupby("State")["Region"].nunique()
add("Consistency", "State maps to exactly one Region", (sr == 1).sum(), len(sr))
add("Timeliness", "Order Date within 2015-01-01..2018-12-31", clean["Order Date"].between("2015-01-01", "2018-12-31").sum(), n, "historic sample data, not a live feed")
add("Referential integrity", "fact FKs all present in dimensions",
    sum(T["fact_sales"][fk].isin(T[d][k]).sum() for fk, d, k in [("customer_key", "dim_customer", "customer_key"), ("product_key", "dim_product", "product_key"),
                                                               ("geography_key", "dim_geography", "geography_key"), ("order_date_key", "dim_date", "date_key"), ("ship_date_key", "dim_date", "date_key")]),
    5 * len(T["fact_sales"]))
sc = pd.DataFrame(dims)
dim_sc = sc.groupby("dimension")["score_%"].mean().rename("mean_score_%").reset_index()
overall = sc["score_%"].mean()
(REPORTS / "data_quality_scorecard.md").write_text("\n".join([
    "# Data Quality Scorecard (script 11)", "",
    "Each rule is a pass/fail test per row (or per key). Score = share passing. Computed on the cleaned data unless marked RAW.", "",
    md_table(sc.round(2)), "", "## Score per dimension", md_table(dim_sc.round(2)), "",
    f"**Unweighted mean of all rule scores: {overall:.2f}%.** The RAW completeness rule shows what cleaning fixed.", ""]), encoding="utf-8")

# ---------- 3. data dictionary
meaning = {
    "Row ID": "Source row number of the order line (unique key)", "Order ID": "Order number, one order has several lines",
    "Order Date": "Date the order was placed", "Ship Date": "Date the order was shipped", "Ship Mode": "Shipping service level",
    "Customer ID": "Customer code", "Customer Name": "Customer full name", "Segment": "Customer segment: Consumer, Corporate, Home Office",
    "Country": "Country (always United States)", "City": "Delivery city", "State": "Delivery US state", "Postal Code": "ZIP code kept as text; 'Unknown' where missing",
    "Region": "Sales region: East, West, Central, South", "Product ID": "Product code", "Category": "Top-level product category",
    "Sub-Category": "Product sub-category (17)", "Product Name": "Product description", "Sales": "Line revenue in USD after discount",
    "Quantity": "Units on the line", "Discount": "Discount fraction 0-0.8", "Profit": "Line profit in USD (negative = loss)",
    "Order Year": "Derived: year of Order Date", "Order Month": "Derived: month number of Order Date", "Order YearMonth": "Derived: YYYY-MM of Order Date",
    "Ship Days": "Derived: Ship Date minus Order Date in days", "Profit Margin": "Derived: Profit / Sales", "Unit Price": "Derived: Sales / Quantity"}
dd = []
for c in clean.columns:
    s = clean[c]
    ex = s.dropna().iloc[0]
    dd.append({"table": "superstore_clean", "column": c, "type": str(s.dtype), "meaning": meaning.get(c, ""),
               "nullable": "yes" if s.isna().any() else "no", "distinct": s.nunique(),
               "example": str(ex)[:30], "range_or_note": (f"{s.min():,.4g} to {s.max():,.4g}" if pd.api.types.is_numeric_dtype(s) else
                                                         f"{s.min():%Y-%m-%d} to {s.max():%Y-%m-%d}" if pd.api.types.is_datetime64_any_dtype(s) else "")})
star_meaning = {"customer_key": "Surrogate key of customer", "product_key": "Surrogate key of product", "geography_key": "Surrogate key of geography",
                "date_key": "Date as YYYYMMDD integer key", "order_date_key": "FK to dim_date for order date", "ship_date_key": "FK to dim_date for ship date",
                "sales": "Measure: revenue USD (additive)", "quantity": "Measure: units (additive)", "discount": "Attribute: discount fraction (non-additive, average it)",
                "profit": "Measure: profit USD (additive)", "row_id": "Degenerate key from source", "order_id": "Degenerate dimension: order number", "ship_mode": "Ship mode (kept on fact)"}
for tname, t in T.items():
    for c in t.columns:
        s = t[c]
        dd.append({"table": tname, "column": c, "type": str(s.dtype), "meaning": star_meaning.get(c, meaning.get(c, meaning.get(c.title(), ""))),
                   "nullable": "yes" if s.isna().any() else "no", "distinct": s.nunique(), "example": str(s.dropna().iloc[0])[:30], "range_or_note": ""})
dd = pd.DataFrame(dd)
dd.to_csv(ROOT / "data" / "data_dictionary.csv", index=False)
(REPORTS / "data_dictionary.md").write_text("\n".join([
    "# Data Dictionary (script 11)", "", "Types are the pandas dtypes after loading the files. Curated tables are in `data/curated/`.", "",
    "## Cleaned table and star schema columns", md_table(dd.drop(columns="range_or_note")), "",
    "## Numeric and date ranges of the cleaned table", md_table(dd[(dd.table == "superstore_clean") & (dd.range_or_note != "")][["column", "range_or_note"]]), ""]), encoding="utf-8")

# ---------- 4. lineage + reconciliation
log = pd.read_csv(CLEAN / "cleaning_log.csv")
(REPORTS / "lineage_and_reconciliation.md").write_text("\n".join([
    "# Data Lineage and Row-Count Reconciliation (script 11)", "",
    "## Lineage", "```",
    "data/raw/superstore.csv                (raw zone: untouched download, 10,800 rows incl. stray rows)",
    "   |  step 01  profile only (reports/data_quality_report.md)",
    "   |  step 03  extract -> data/staging/stg_superstore_raw.parquet (as-is, all text, _loaded_at added)",
    "   v  step 02  clean: drop stray rows, parse dates, type fixes, fill postal code, derive columns (data/clean/)",
    "data/clean/superstore_clean.csv/.parquet (clean zone: 9,994 rows, 27 columns)",
    "   |  step 03  transform + load: surrogate keys, dimensions, fact (integrity asserts)",
    "   v",
    "data/curated/ dim_*.csv/.parquet + fact_sales  (curated zone: star schema for Power BI)",
    "   |  step 11  data/curated/agg_monthly_category_region.csv (pre-aggregated for fast visuals)",
    "   |  steps 04,07-09  data/forecast/*.csv   |  step 10  data/analytics/*.csv",
    "```", "",
    "Note: step 03 reads the raw file for staging and the clean file for the transform; step 02 must therefore run before 03 (run_all keeps this order).", "",
    "## Row-count reconciliation", md_table(rec), "", "## Reconciliation checks", md_table(checks), "",
    "## Cleaning log (from step 02)", md_table(log), ""]), encoding="utf-8")

# ---------- 5. aggregate table for Power BI
f = T["fact_sales"].merge(T["dim_date"][["date_key", "year", "quarter", "month", "year_month"]], left_on="order_date_key", right_on="date_key") \
    .merge(T["dim_product"][["product_key", "Category", "Sub-Category"]], on="product_key") \
    .merge(T["dim_geography"][["geography_key", "Region", "State"]], on="geography_key") \
    .merge(T["dim_customer"][["customer_key", "Segment"]], on="customer_key")
agg = (f.groupby(["year", "quarter", "month", "year_month", "Category", "Sub-Category", "Region", "Segment"], as_index=False)
       .agg(order_lines=("row_id", "size"), orders=("order_id", "nunique"), sales=("sales", "sum"), profit=("profit", "sum"),
            quantity=("quantity", "sum"), discount_weighted_sum=("discount", "sum")))
agg["month_start"] = pd.to_datetime(agg.year_month + "-01")
agg.round(4).to_csv(CURATED / "agg_monthly_category_region.csv", index=False)
assert abs(agg.sales.sum() - clean.Sales.sum()) < 1e-6 and abs(agg.profit.sum() - clean.Profit.sum()) < 1e-6
print(f"[11] aggregate table: {len(agg):,} rows, totals reconcile to clean")

# ---------- 6. extra OLAP examples (SQLite)
con = sqlite3.connect(":memory:")
for name, t in T.items():
    t.to_sql(name, con, index=False)
JOIN = ("FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key "
        "JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key")
Q = [
    ("Roll-up with subtotals: year x category (UNION of levels)", "Detail rows plus year subtotals, emulating ROLLUP (SQLite has no ROLLUP).",
     f"SELECT d.year, p.[Category], ROUND(SUM(f.sales),2) AS sales {JOIN} GROUP BY d.year, p.[Category] UNION ALL "
     f"SELECT d.year, 'ALL CATEGORIES', ROUND(SUM(f.sales),2) {JOIN} GROUP BY d.year ORDER BY 1, 2"),
    ("Roll-up: region -> state (top 8 states in the West)", "Drill from region to the states inside it.",
     f"SELECT g.[Region], g.[State], ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit {JOIN} WHERE g.[Region]='West' GROUP BY g.[Region], g.[State] ORDER BY sales DESC LIMIT 8"),
    ("Drill-down: category -> sub-category (Technology)", "From a category to its sub-categories.",
     f"SELECT p.[Category], p.[Sub-Category], ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit {JOIN} WHERE p.[Category]='Technology' GROUP BY p.[Category], p.[Sub-Category] ORDER BY sales DESC"),
    ("Drill-down: Q4 2018 by month and category", "Year -> quarter -> month detail for one quarter.",
     f"SELECT d.year_month, p.[Category], ROUND(SUM(f.sales),2) AS sales {JOIN} WHERE d.year=2018 AND d.quarter=4 GROUP BY d.year_month, p.[Category] ORDER BY d.year_month, p.[Category]"),
    ("Slice: Consumer segment, all years", "Fix Segment = Consumer; sales and profit by year.",
     f"SELECT d.year, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit {JOIN} WHERE c.[Segment]='Consumer' GROUP BY d.year ORDER BY d.year"),
    ("Slice: discount above 30%", "Loss-making rows by sub-category when heavily discounted.",
     f"SELECT p.[Sub-Category], COUNT(*) AS lines, ROUND(SUM(f.profit),2) AS profit {JOIN} WHERE f.discount > 0.3 GROUP BY p.[Sub-Category] ORDER BY profit LIMIT 6"),
    ("Dice: 2017-2018, Central/South, Furniture/Technology, Corporate", "Restrict four dimensions at once.",
     f"SELECT d.year, g.[Region], p.[Category], ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit {JOIN} "
     f"WHERE d.year IN (2017,2018) AND g.[Region] IN ('Central','South') AND p.[Category] IN ('Furniture','Technology') AND c.[Segment]='Corporate' GROUP BY d.year, g.[Region], p.[Category] ORDER BY 1,2,3"),
    ("Year-over-year growth by category", "Window function LAG over yearly totals.",
     f"SELECT [Category] AS category, year, sales, ROUND((sales - LAG(sales) OVER (PARTITION BY [Category] ORDER BY year)) / LAG(sales) OVER (PARTITION BY [Category] ORDER BY year) * 100, 2) AS yoy_pct "
     f"FROM (SELECT p.[Category], d.year, SUM(f.sales) AS sales {JOIN} GROUP BY p.[Category], d.year) ORDER BY [Category], year"),
    ("Running total of monthly sales 2018", "Window function SUM OVER ordered months.",
     f"SELECT year_month, ROUND(sales,2) AS sales, ROUND(SUM(sales) OVER (ORDER BY year_month),2) AS running_sales FROM "
     f"(SELECT d.year_month, SUM(f.sales) AS sales {JOIN} WHERE d.year=2018 GROUP BY d.year_month) ORDER BY year_month"),
    ("Aggregate table query (what Power BI reads)", "Same answer as the fact join, from the pre-aggregated table.",
     "SELECT year, Category, ROUND(SUM(sales),2) AS sales, ROUND(SUM(profit),2) AS profit FROM agg_monthly_category_region GROUP BY year, Category ORDER BY year, Category"),
]
agg.to_sql("agg_monthly_category_region", con, index=False)
md = ["# Additional OLAP Query Examples (script 11)", "", "Executed as SQL on SQLite over the curated tables; results are real output.", ""]
for title, why, sql in Q:
    res = pd.read_sql(sql, con)
    md += [f"## {title}", why, "", "```sql", sql, "```", "", md_table(res), ""]
(REPORTS / "olap_extra_examples.md").write_text("\n".join(md), encoding="utf-8")
print(f"[11] overall DQ score {overall:.2f}%; reconciliation:", checks.result.value_counts().to_dict())
print("[11] wrote data dictionary, scorecard, lineage, extra OLAP, aggregate table")
