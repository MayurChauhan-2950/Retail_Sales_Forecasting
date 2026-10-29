# Power BI build pack

## STATUS: the .pbix dashboard is NOT built yet

Power BI Desktop was not installed on the machine where this project was prepared.
There is no `.pbix`, no PDF export and no dashboard screenshot in this repository.
This folder is a **build pack**: everything needed to build the dashboard later in
about 2 to 3 hours. None of the DAX or Power Query code here has been executed in
Power BI Desktop; it was only reviewed by reading. Treat the first run as a test.

Every number quoted in these files was computed from the project's CSV files
(`data/curated`, `data/forecast`) by `tools/build_dax_docs.py`, or copied from
`reports/model_accuracy.md`. Those numbers are "expected check values" to compare
against once you build the report, not results of a dashboard.

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
1. Install Power BI Desktop (Windows).
2. Edit the path in `power_query/00_DataFolder_parameter.pq` if the project is not at
   `C:\Users\devch\Downloads\DSC\Projects\IP_Retail_Sales_Analytics\data`.
3. Follow `BUILD_CHECKLIST.md`. Tick items only after you have really done and checked them.

## Honest limits
- Dataset: public "Sample - Superstore" (9,994 order lines, 2015-2018), not a company's private data.
- Forecast: only 48 monthly points; accuracy is modest (best hold-out MAPE 18.5%).
- Only the best model (Holt-Winters additive) has 2019 values; ARIMA and SARIMA have hold-out values only.
