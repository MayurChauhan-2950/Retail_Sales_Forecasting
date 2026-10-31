# Power BI build pack

## STATUS: the dashboard is built (2 pages); pages 3 and 4 are not

The Power BI project is in `pbip/` (open `pbip/retail_sales_forecast.pbip` in Power BI Desktop, then click Refresh).
It has 9 data tables, relationships, 84 DAX measures and two report pages:

- **Overview:** KPI cards (sales, profit, customers, orders), monthly sales line, sales by category, Year and Region slicers.
- **Forecasting Arena:** model slicer, best model, 2019 forecast total and growth, 2018 hold-out actual vs forecast, 2019 forecast with 95% interval, accuracy table.

Real screenshots: `screenshots/page1_overview.png` and `screenshots/page2_forecasting_arena.png`.

What was checked in Power BI Desktop: the project loads, the data refreshes, and the visible numbers match the pandas results
(total sales 2,297,200.86, profit 286,397.02, 793 customers, 5,009 orders, Holt-Winters 2019 forecast about 910K, +24.1% vs 2018,
hold-out MAE 10,896.63, RMSE 14,117.72, MAPE 18.51). Only the measures used on the two pages were exercised; the other measures
in `dax/measures.dax` have not been run. The planned pages 3 and 4 (customers/RFM, products and discounts) are not built.

Every expected value in these files was computed from the project's CSV files (`data/curated`, `data/forecast`) by
`tools/build_dax_docs.py`, or copied from `reports/model_accuracy.md`.

## Contents

| Path | What it is |
|---|---|
| `BUILD_CHECKLIST.md` | Step-by-step build and test list (start here) |
| `theme/retail_forecast_theme.json` | Power BI theme (valid JSON; import via View > Themes > Browse for themes) |
| `power_query/00..09_*.pq` | One M script per table: DataFolder parameter, fact_sales, dim_date (+ generated fallback), dim_product, dim_customer, dim_geography, monthly_actual, fact_forecast, model_accuracy, dim_model |
| `dax/measures.dax` | 84 measures + 2 calculated tables (Top N, RFM), copy-ready |
| `dax/DAX_MEASURES.md` | Reference table: format, purpose, visual, expected check value |
| `model/DATA_MODEL.md` | Tables, keys, relationships, Mermaid diagram |
| `layouts/WIREFRAMES.md` | ASCII wireframes of the 4 pages |
| `VIVA_QA.md` | Viva questions and answers about the dashboard |
| `tools/build_dax_docs.py` | Regenerates the DAX files and check values from the CSVs (needs pandas) |

## Before you start
1. Power BI Desktop (Windows) is needed. Open `pbip/retail_sales_forecast.pbip`; see `pbip/OPEN_ME.md`.
2. Edit the path in `power_query/00_DataFolder_parameter.pq` if the project is not at
   `C:\Users\devch\Downloads\DSC\Projects\IP_Retail_Sales_Analytics\data`.
3. Follow `BUILD_CHECKLIST.md`. Tick items only after you have really done and checked them.

## Honest limits
- Dataset: public "Sample - Superstore" (9,994 order lines, 2015-2018), not a company's private data.
- Forecast: only 48 monthly points; accuracy is modest (best hold-out MAPE 18.5%).
- Only the best model (Holt-Winters additive) has 2019 values; ARIMA and SARIMA have hold-out values only.
