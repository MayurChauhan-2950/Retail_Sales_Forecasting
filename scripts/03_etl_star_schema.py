"""Step 3 - ETL into a star schema (Ch8 Data Engineering and Warehousing).
Zones (data-lake style):  raw -> (extract) staging -> (transform) clean -> (load) curated star schema.
Tables: dim_customer, dim_product, dim_date, dim_geography, fact_sales.
Then OLAP examples (roll-up, drill-down, slice, dice, pivot) run as real SQL on SQLite -> reports/olap_examples.md"""
import sqlite3
import pandas as pd
from common import read_raw, md_table, STAGING, CLEAN, CURATED, REPORTS

# ---------- EXTRACT: raw -> staging (as-is copy in a columnar format, plus load metadata)
raw = read_raw()
raw["_loaded_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
raw.astype(str).to_parquet(STAGING / "stg_superstore_raw.parquet", index=False)
print(f"[03] extract: {len(raw):,} raw rows staged")

# ---------- TRANSFORM: use the cleaned file produced by step 2
df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date", "Ship Date"],
                 dtype={"Postal Code": str})
print(f"[03] transform: {len(df):,} clean rows")

# dim_customer: one row per Customer ID (surrogate key = customer_key)
dim_customer = (df.sort_values("Order Date").drop_duplicates("Customer ID")
                [["Customer ID", "Customer Name", "Segment"]].sort_values("Customer ID").reset_index(drop=True))
dim_customer.insert(0, "customer_key", dim_customer.index + 1)

# dim_product: one row per Product ID (a few IDs have several names in the source -> keep first)
dim_product = (df.drop_duplicates("Product ID")[["Product ID", "Product Name", "Category", "Sub-Category"]]
               .sort_values("Product ID").reset_index(drop=True))
dim_product.insert(0, "product_key", dim_product.index + 1)

# dim_geography: one row per Country/Region/State/City/Postal Code
geo_cols = ["Country", "Region", "State", "City", "Postal Code"]
dim_geography = df[geo_cols].drop_duplicates().sort_values(geo_cols).reset_index(drop=True)
dim_geography.insert(0, "geography_key", dim_geography.index + 1)

# dim_date: complete calendar from first order to last ship date (date_key = YYYYMMDD)
days = pd.date_range(df["Order Date"].min().replace(month=1, day=1), df["Ship Date"].max().replace(month=12, day=31))
dim_date = pd.DataFrame({"date": days})
dim_date["date_key"] = dim_date["date"].dt.strftime("%Y%m%d").astype(int)
dim_date["year"] = dim_date["date"].dt.year
dim_date["quarter"] = dim_date["date"].dt.quarter
dim_date["month"] = dim_date["date"].dt.month
dim_date["month_name"] = dim_date["date"].dt.month_name()
dim_date["year_month"] = dim_date["date"].dt.strftime("%Y-%m")
dim_date["week_of_year"] = dim_date["date"].dt.isocalendar().week.astype(int)
dim_date["day"] = dim_date["date"].dt.day
dim_date["day_of_week"] = dim_date["date"].dt.day_name()
dim_date["is_weekend"] = (dim_date["date"].dt.dayofweek >= 5).astype(int)
dim_date = dim_date[["date_key", "date", "year", "quarter", "month", "month_name", "year_month",
                     "week_of_year", "day", "day_of_week", "is_weekend"]]

# fact_sales: grain = one order line; foreign keys to the dimensions + numeric measures
f = (df.merge(dim_customer[["customer_key", "Customer ID"]], on="Customer ID")
       .merge(dim_product[["product_key", "Product ID"]], on="Product ID")
       .merge(dim_geography[["geography_key"] + geo_cols], on=geo_cols))
f["order_date_key"] = f["Order Date"].dt.strftime("%Y%m%d").astype(int)
f["ship_date_key"] = f["Ship Date"].dt.strftime("%Y%m%d").astype(int)
fact_sales = (f.rename(columns={"Row ID": "row_id", "Order ID": "order_id", "Ship Mode": "ship_mode",
                                "Sales": "sales", "Quantity": "quantity", "Discount": "discount", "Profit": "profit"})
              [["row_id", "order_id", "order_date_key", "ship_date_key", "customer_key", "product_key",
                "geography_key", "ship_mode", "sales", "quantity", "discount", "profit"]]
              .sort_values("row_id").reset_index(drop=True))

# ---------- Integrity checks (PK unique, FK present, row count preserved)
checks = []
def check(name, ok):
    checks.append((name, "PASS" if ok else "FAIL"))
    assert ok, name
check("fact rows == clean rows", len(fact_sales) == len(df))
check("fact_sales.row_id unique", fact_sales["row_id"].is_unique)
for dim, key, fk in [(dim_customer, "customer_key", "customer_key"), (dim_product, "product_key", "product_key"),
                     (dim_geography, "geography_key", "geography_key"), (dim_date, "date_key", "order_date_key"),
                     (dim_date, "date_key", "ship_date_key")]:
    check(f"{key} unique in dim", dim[key].is_unique)
    check(f"no orphan {fk}", fact_sales[fk].isin(dim[key]).all())
check("total sales preserved", abs(fact_sales["sales"].sum() - df["Sales"].sum()) < 1e-6)

# ---------- LOAD: curated zone (csv for Power BI + parquet)
tables = {"dim_customer": dim_customer, "dim_product": dim_product, "dim_date": dim_date,
          "dim_geography": dim_geography, "fact_sales": fact_sales}
for name, t in tables.items():
    t.to_csv(CURATED / f"{name}.csv", index=False)
    t.to_parquet(CURATED / f"{name}.parquet", index=False)
    print(f"[03] load: {name:14s} {len(t):>6,} rows")

# ---------- OLAP examples with SQL (SQLite in memory)
con = sqlite3.connect(":memory:")
for name, t in tables.items():
    t.assign(**{c: t[c].astype(str) for c in t.select_dtypes("datetime").columns}).to_sql(name, con, index=False)

JOIN = ("FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key "
        "JOIN dim_product p ON f.product_key = p.product_key "
        "JOIN dim_geography g ON f.geography_key = g.geography_key "
        "JOIN dim_customer c ON f.customer_key = c.customer_key")
queries = [
    ("Roll-up: sales by year (highest level)", "Aggregate months up to years.",
     f"SELECT d.year, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit {JOIN} GROUP BY d.year ORDER BY d.year"),
    ("Roll-up: year -> quarter", "One level below year; summing the quarters gives the year totals above.",
     f"SELECT d.year, d.quarter, ROUND(SUM(f.sales),2) AS sales {JOIN} GROUP BY d.year, d.quarter ORDER BY d.year, d.quarter"),
    ("Drill-down: 2017 sales by month", "Go from year to month detail.",
     f"SELECT d.month, d.month_name, ROUND(SUM(f.sales),2) AS sales {JOIN} WHERE d.year = 2017 GROUP BY d.month, d.month_name ORDER BY d.month"),
    ("Slice: Region = 'West' (one dimension fixed)", "Category totals for the West region only.",
     f"SELECT p.category, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit {JOIN} WHERE g.region = 'West' GROUP BY p.category ORDER BY sales DESC"),
    ("Dice: 2016-2017, Technology/Furniture, East/West", "Several dimensions restricted at once.",
     f"SELECT d.year, g.region, p.category, ROUND(SUM(f.sales),2) AS sales, SUM(f.quantity) AS units {JOIN} "
     f"WHERE d.year IN (2016,2017) AND p.category IN ('Technology','Furniture') AND g.region IN ('East','West') "
     f"GROUP BY d.year, g.region, p.category ORDER BY d.year, g.region, p.category"),
    ("Cross-tab (pivot): Segment x Category sales", "Two dimensions against a measure.",
     f"SELECT c.segment, ROUND(SUM(CASE WHEN p.category='Furniture' THEN f.sales END),2) AS furniture, "
     f"ROUND(SUM(CASE WHEN p.category='Office Supplies' THEN f.sales END),2) AS office_supplies, "
     f"ROUND(SUM(CASE WHEN p.category='Technology' THEN f.sales END),2) AS technology {JOIN} GROUP BY c.segment ORDER BY c.segment"),
    ("Top 5 states by profit", "Ranking over the geography dimension.",
     f"SELECT g.state, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit {JOIN} GROUP BY g.state ORDER BY profit DESC LIMIT 5"),
]
md = ["# OLAP-style Examples on the Star Schema", "",
      "Star schema: `fact_sales` (grain = one order line) with `dim_date`, `dim_product`, `dim_customer`, `dim_geography`.",
      "Each query below was executed with SQL on the curated tables (SQLite); results are the real output.", "",
      "## Integrity checks", md_table(pd.DataFrame(checks, columns=["check", "result"])), ""]
for title, why, sql in queries:
    res = pd.read_sql(sql, con)
    md += [f"## {title}", why, "", "```sql", sql.replace(" FROM", "\nFROM").replace(" JOIN", "\nJOIN")
           .replace(" WHERE", "\nWHERE").replace(" GROUP BY", "\nGROUP BY").replace(" ORDER BY", "\nORDER BY"), "```", "",
           md_table(res), ""]
(REPORTS / "olap_examples.md").write_text("\n".join(md), encoding="utf-8")
print("[03] integrity checks:", ", ".join(f"{c}={r}" for c, r in checks[:3]), "... all PASS")
print("[03] wrote reports/olap_examples.md")
