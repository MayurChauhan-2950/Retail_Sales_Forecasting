# Report Outline - Retail Sales Forecasting: A Comparison of ARIMA, SARIMA and Holt-Winters Using an Interactive Power BI Dashboard

(All numbers come from `reports/`; re-run `python scripts/run_all.py` if data changes.)

## Abstract
Analysis of 9,994 order lines (Superstore, 2015-2018, sales $2,297,200.86, profit $286,397.02). Data cleaned, loaded to a star schema, explored, and monthly sales forecast with Holt-Winters, ARIMA and SARIMA compared on a 12-month hold-out. Best: Holt-Winters additive (MAE 10,896.63; RMSE 14,117.72; MAPE 18.51%). (Polish to ~150 words.)

## 1. Introduction
TODO write: retail context, why forecasting matters, why Power BI.

## 2. Objectives
1. Profile and clean the data (Ch6). 2. Fit a trend with gradient descent (Ch7). 3. Build a star schema (Ch8). 4. Compare Holt-Winters, ARIMA, SARIMA (Ch9). 5. Present in Power BI (Ch10).

## 3. Dataset
Public Sample - Superstore, REAL data, 21 columns (see README for source and the 806 stray rows). Orders 2015-01-03 to 2018-12-30; 5,009 orders, 793 customers, 1,862 products, 49 states, 4 regions, 3 categories, 17 sub-categories.

## 4. Methodology by DSC chapter
### 4.1 Transformation and integrity (Ch6) - `reports/data_quality_report.md`, `reports/cleaning_log.md`
- 10,800 raw rows -> 9,994 clean rows (806 stray empty rows removed; the 504 raw "duplicates" were these stray rows; 0 true duplicates).
- 11 missing Postal Codes (Burlington, VT) set to 'Unknown'; Postal Code stored as text; dates parsed; 32 Product IDs have multiple names.
- 1,167 Sales outliers kept (genuine large orders). Sales skewness 12.97 -> 0.28 after log1p.
- Scaling checked against sklearn; encoding: one-hot (14 columns), label (17 sub-categories), out-of-fold target encoding (State).
### 4.2 Optimisation (Ch7) - `reports/gradient_descent_report.md`
MSE cost; gradient descent equals closed form (slope $902.01 per month, MSE 465,460,447.08, R^2 0.251), converged in about 28 epochs at lr 0.1; lr 1.05 diverges, 0.001 is slow.
### 4.3 Data engineering (Ch8) - `reports/olap_examples.md`
raw -> staging -> clean -> curated. fact_sales 9,994 rows; dim_customer 793; dim_product 1,862; dim_geography 632; dim_date 1,826; all integrity checks PASS. OLAP: roll-up, drill-down, slice, dice, pivot in SQL.
### 4.4 Time series (Ch9) - `reports/model_accuracy.md`
48 months; train 36 / test 12. Decomposition: rising trend, strong Sep/Nov/Dec seasonality. Three methods compared on the same hold-out.
### 4.5 Visualisation (Ch10) - `reports/figures/`
10 EDA charts.

## 5. Results
| Model (hold-out Jan-Dec 2018) | MAE | RMSE | MAPE % |
|---|---|---|---|
| Holt-Winters (additive) | 10,896.63 | 14,117.72 | 18.51 |
| SARIMA(1,1,1)(0,1,1,12) | 15,104.56 | 17,570.51 | 33.98 |
| ARIMA(1,1,1) | 23,450.63 | 27,208.45 | 54.11 |

| Item | Result |
|---|---|
| Sales by year 2015/16/17/18 | $484,247.50 / $470,532.51 / $609,205.60 / $733,215.26 |
| Profit by category | Furniture $18,451, Office Supplies $122,491, Technology $145,455 |
| Sales by region | West $725,458, East $678,781, Central $501,240, South $391,722 |
| Discount effect | average profit positive up to 20% discount, negative from 30% |
Figures: `ts_decomposition.png`, `ts_holdout_forecast.png`, `ts_final_forecast.png`, `gd_loss_curve.png`, EDA charts. Discuss: non-seasonal ARIMA cannot capture the strong seasonality; only 3 training seasonal cycles limit SARIMA.

## 6. Dashboard (Power BI)
**TODO - to be completed by the student.** See `powerbi/README_TODO.md`.

## 7. Conclusion
TODO write: clean star schema, discounts above 20% erode profit, strong Q4 seasonality, Holt-Winters best on this hold-out.

## 8. Limitations and future work
Short history; no external drivers (promotions, holidays); try Prophet or gradient boosting with calendar features; forecast per category/region; automate ETL.

## 9. References
- Sample - Superstore dataset (GitHub copy: leonism/sample-superstore).
- Hyndman and Athanasopoulos, Forecasting: Principles and Practice (3rd ed.).
- Kimball and Ross, The Data Warehouse Toolkit.
- Seabold and Perktold, statsmodels (2010); Pedregosa et al., scikit-learn (2011).
- DSC course notes, Chapters 6-10.
