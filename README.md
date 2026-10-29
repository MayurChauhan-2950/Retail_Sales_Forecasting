# Retail Sales Forecasting: A Comparison of ARIMA, SARIMA and Holt-Winters Using an Interactive Power BI Dashboard

DSC individual project (Mayur Chauhan, L.J. Institute of Engineering and Technology). Everything except the Power BI dashboard is complete and tested. The Power BI part is a blank placeholder (`powerbi/README_TODO.md`).

## Data source: REAL, with one caveat
`data/raw/superstore.csv` is a **real copy of the public "Sample - Superstore" dataset**, downloaded from
`https://raw.githubusercontent.com/leonism/sample-superstore/master/data/superstore.csv` (9,994 genuine order lines, orders 2015-2018).
Caveat found while profiling: this copy has **806 stray rows appended at the end** (remnants of the other Excel sheets, all business columns empty), giving 10,800 rows. Cleaning removes them. The 504 "duplicate rows" and most "missing values" in the raw profile come from these stray rows. The real order data has only 11 missing Postal Codes (Burlington, Vermont) and no other defects, so several cleaning checks show zero; this is the honest result.
You may replace the file with the Kaggle original; scripts read utf-8 then fall back to latin-1 and work unchanged.

## Folder map
```
data/raw/        original CSV (data lake "raw" zone)
data/staging/    as-is parquet copy made by the ETL extract step
data/clean/      cleaned CSV/parquet, cleaning log, ML-ready demo (scaled + encoded)
data/curated/    star schema: dim_customer, dim_product, dim_date, dim_geography, fact_sales (csv + parquet)
data/forecast/   forecast CSVs to import into Power BI
scripts/         01..11 + run_all.py + common.py, style.py, tsmodels.py
reports/         generated markdown reports + figures/ (PNG)
docs/            project_report_outline.md
presentation/    slides (.pptx)
powerbi/         README_TODO.md (blank placeholder)
```

## How to run (Windows, Python 3.11)
```
cd C:\Users\devch\Downloads\DSC\Projects\IP_Retail_Sales_Analytics
pip install -r requirements.txt
python scripts/run_all.py
```
Or one by one: `01_data_quality_report.py`, `02_clean_transform.py`, `03_etl_star_schema.py`, `04_timeseries_forecast.py`, `05_gradient_descent_trend.py`, `06_eda_charts.py`, then the extended analysis: `07_cv_evaluation.py` (rolling-origin CV, appends to reports/model_accuracy.md), `08_diagnostics_forecast.py` (stationarity, Ljung-Box, residual plots, 2019 interval forecast), `09_segment_forecasts.py` (category/region/segment forecasts), `10_business_analytics.py` (RFM, Pareto, discount vs profit), `11_data_engineering_extras.py` (data dictionary, quality scorecard, reconciliation, extra OLAP SQL). Order matters: 02 feeds 03-06 and 07-11; 04 runs before 07 and 08, which add sections to the report 04 writes. Shared code: common.py, style.py, tsmodels.py. Real results and caveats: `reports/RESULTS_SUMMARY.md`.

## DSC chapter mapping
| Chapter | Topic | Script | Output |
|---|---|---|---|
| Ch6 | Missing values, duplicates, consistency, types | 01, 02 | reports/data_quality_report.md, reports/cleaning_log.md, data/clean/ |
| Ch6 | Scaling (min-max, z-score, log), encoding (one-hot, label, target) | 02 | data/clean/superstore_ml_ready_demo.csv |
| Ch7 | Cost function (MSE), gradient descent vs closed form | 05 | reports/gradient_descent_report.md, figures/gd_*.png |
| Ch8 | ETL, staging, star schema, zones, OLAP roll-up/slice/dice | 03 | data/staging, data/curated, reports/olap_examples.md |
| Ch9 | Decomposition; Holt-Winters vs ARIMA vs SARIMA; MAE/RMSE/MAPE | 04 | reports/model_accuracy.md, data/forecast/, figures/ts_*.png |
| Ch10 | EDA visualisation, capstone report | 06, docs | figures/01..10_*.png, docs/project_report_outline.md |

## Notes
- Hold-out: the last 12 months (2018) are held out; the three methods are compared on it. The best one is refit on all 48 months to forecast 2019. Holt-Winters interval is approximate (+/-1.96 x residual std); ARIMA/SARIMA use the model interval.
- With only 48 monthly points, accuracy is modest; discuss this honestly.
