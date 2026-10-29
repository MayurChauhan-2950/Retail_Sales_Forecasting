# Data Lineage and Row-Count Reconciliation (script 11)

## Lineage
```
data/raw/superstore.csv                (raw zone: untouched download, 10,800 rows incl. stray rows)
   |  step 01  profile only (reports/data_quality_report.md)
   |  step 03  extract -> data/staging/stg_superstore_raw.parquet (as-is, all text, _loaded_at added)
   v  step 02  clean: drop stray rows, parse dates, type fixes, fill postal code, derive columns (data/clean/)
data/clean/superstore_clean.csv/.parquet (clean zone: 9,994 rows, 27 columns)
   |  step 03  transform + load: surrogate keys, dimensions, fact (integrity asserts)
   v
data/curated/ dim_*.csv/.parquet + fact_sales  (curated zone: star schema for Power BI)
   |  step 11  data/curated/agg_monthly_category_region.csv (pre-aggregated for fast visuals)
   |  steps 04,07-09  data/forecast/*.csv   |  step 10  data/analytics/*.csv
```

Note: step 03 reads the raw file for staging and the clean file for the transform; step 02 must therefore run before 03 (run_all keeps this order).

## Row-count reconciliation
| stage | rows | note |
|---|---|---|
| raw file rows | 10800 | data/raw/superstore.csv |
|   of which stray empty rows (no Order ID/Sales) | 806 | removed in step 02 |
|   of which real order lines | 9994 |  |
| staging rows | 10800 | as-is parquet copy (step 03 extract) |
| clean rows | 9994 | data/clean/superstore_clean.csv |
| fact_sales rows | 9994 | grain = order line |
| dim_customer rows | 793 | = distinct Customer ID in clean |
| dim_product rows | 1862 | = distinct Product ID in clean |
| dim_geography rows | 632 | = distinct Country/Region/State/City/Postal Code |
| dim_date rows | 1826 | calendar days incl. ship dates |

## Reconciliation checks
| reconciliation check | result |
|---|---|
| raw - stray rows = clean rows | PASS |
| staging rows = raw rows | PASS |
| clean rows = fact rows | PASS |
| sum(Sales) clean = fact | PASS |
| sum(Profit) clean = fact | PASS |
| sum(Quantity) clean = fact | PASS |
| distinct customers clean = dim | PASS |
| distinct products clean = dim | PASS |
| sum(Sales) real raw rows = clean | PASS |

## Cleaning log (from step 02)
| step | rule | rows_or_cells_affected | action | rows_after |
|---|---|---|---|---|
| 1 stray rows | all columns except Row ID/Order ID empty | 806 | dropped | 9994 |
| 2 duplicates | fully identical rows | 0 | kept first, dropped rest | 9994 |
| 2b duplicate Row ID | same Row ID twice | 0 | kept first | 9994 |
| 3 text consistency | strip/collapse spaces; Title Case for category-like columns | 32 | standardised | 9994 |
| 4 data types | Row ID/Sales/Quantity/Discount/Profit -> numeric; dates parsed from mixed formats | 0 | 0 values could not be parsed -> NaT (handled in step 5) | 9994 |
| 5a missing critical fields | any of 9 key fields missing | 0 | dropped | 9994 |
| 5b missing Discount | Discount empty | 0 | imputed with 0 (no discount) | 9994 |
| 5c missing Postal Code | Postal Code empty | 11 | filled with mode of same City+State; 11 still 'Unknown'; stored as 5-char text | 9994 |
| 5d other missing text | category-like columns empty | 0 | filled with 'Unknown' | 9994 |
| 6a invalid Quantity/Sales | Quantity <= 0 or Sales <= 0 | 0 | dropped | 9994 |
| 6b Discount range | Discount outside 0..1 | 0 | clipped to 0..1 | 9994 |
| 6c Ship before Order | Ship Date < Order Date | 0 | dropped | 9994 |
| 7a Customer ID -> name | one ID should have one name | 0 | checked (no change) | 9994 |
| 7b Product ID -> name | one ID should have one name | 32 | checked; star schema keeps first name per Product ID | 9994 |
| 7c Sales outliers | above Q3 + 1.5*IQR | 1167 | kept (genuine large orders); flagged only | 9994 |
| 8 derived columns | Order Year/Month/YearMonth, Ship Days, Profit Margin, Unit Price | 9994 | added | 9994 |
