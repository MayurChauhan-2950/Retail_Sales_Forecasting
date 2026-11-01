# Retail Sales Forecasting: ARIMA, SARIMA and Holt-Winters with a Power BI Dashboard

DSC individual project by Mayur Chauhan (Enrollment No. 23002171310018), L.J. Institute of Engineering and Technology.

This is the **clean branch**: only the files needed to read, present and re-run the project.

## Start here

| I want to... | Open this |
|---|---|
| Understand everything (theory, code, data, viva Q&A, speaking script) | `IP_COMPLETE_EXPLAINER.pdf` |
| Present the project (7 slides) | `presentation/Retail_Sales_Forecasting_Short.pptx` (PDF copy next to it) |
| See the dashboard | `powerbi/pbip/retail_sales_forecast.pbip` (open in Power BI Desktop, click Refresh) or the screenshots in `powerbi/screenshots/` |
| Read the code | `scripts/` (01 to 11, run in order with `python scripts/run_all.py`) |
| See the results | `reports/RESULTS_SUMMARY.md`, `reports/model_accuracy.md`, charts in `reports/figures/` |

## What is in each folder

```
IP_COMPLETE_EXPLAINER.pdf   one file that explains the whole project
presentation/               7-slide deck, PDF copy, and the 4 diagrams (images + PlantUML sources)
scripts/                    Python code: 01 quality check ... 11 extras, plus run_all.py
data/raw/                   original Sample Superstore CSV (unchanged)
data/curated/               star schema tables (fact_sales + 4 dimensions) used by Power BI
data/forecast/              forecast and cross-validation CSVs used by Power BI
reports/                    result summaries, data quality report, cleaning log, charts
powerbi/pbip/               Power BI project (2 pages: Overview, Forecasting Arena)
powerbi/dax/measures.dax    the DAX measures
powerbi/screenshots/        real screenshots of the two pages
requirements.txt            Python packages
```

## How the project works (one line each)

1. `01`, `02`: check data quality (99.46%) and clean it. 806 empty rows removed, 9,994 order lines remain.
2. `03`: build the star schema (one fact table, four dimensions) in `data/curated`.
3. `04`, `07`, `08`, `09`: forecast monthly sales with Holt-Winters, ARIMA and SARIMA, compare them with a 2018 hold-out and rolling-origin cross-validation, check residuals.
4. `05`, `06`, `10`, `11`: gradient descent, charts, RFM, Pareto, discount versus profit, extra checks.
5. Power BI reads `data/curated` and `data/forecast` and shows the results.

## Main result

Holt-Winters has the lowest forecast error (damped version: cross-validation MAE 10,981; 2018 hold-out MAPE 18.5%). SARIMA did not beat the seasonal-naive baseline on average, and its gap to Holt-Winters is not statistically significant (p = 0.375).

## Honest limits

- Only 48 monthly points, so SARIMA has little data to learn from.
- Cross-validation folds overlap, so p-values are indicative only.
- The dashboard has 2 pages. The 2019 forecast exists only for the best model; ARIMA and SARIMA have hold-out values only.
- Only the Power BI measures used on the two pages were checked against the pandas totals.

## Data source

Public "Sample - Superstore" dataset, copied from `https://raw.githubusercontent.com/leonism/sample-superstore/master/data/superstore.csv`. The raw copy has 806 empty rows appended, which cleaning removes.

## Run it

```
pip install -r requirements.txt
python scripts/run_all.py
```
