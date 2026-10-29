# Viva Q&A: the dashboard

The dashboard is not built yet. Answers describe the design and the Python/data results. Numbers come from the
project CSVs and reports. Before the viva, build the report and confirm these numbers appear on screen.

**Q1. Why Power BI for this project?**
It connects to CSV files, has Power Query for ETL, a DAX engine for measures, and interactive slicers and drill-down, which is what the aim (interactive dashboard) needs.

**Q2. Describe your data model.**
Star schema: fact_sales (9,994 order lines) with dim_date, dim_customer, dim_product and dim_geography, all many-to-one with single-direction filters. The forecast tables (monthly_actual, fact_forecast, model_accuracy, dim_model) join to dim_date and dim_model. See `model/DATA_MODEL.md`.

**Q3. Why a star schema?**
Dimensions filter the fact table, queries are simple and fast, and it is what Chapter 8 teaches (the Python ETL builds the same tables).

**Q4. What is the grain of the fact table?**
One row per order line. There are 5,009 orders and 9,994 lines.

**Q5. Why is ship_date_key an inactive relationship?**
Only one active relationship can exist between two tables. Order date is the active one; ship date is a role-playing relationship that can be used with USERELATIONSHIP.

**Q6. Which headline KPIs and what values?**
Total Sales 2,297,200.86, Total Profit 286,397.02, Margin 12.47%, Orders 5,009, Customers 793 (computed from the CSVs; confirm on the cards).

**Q7. Explain the YoY measure.**
YoY % = (Sales - Sales LY) / Sales LY, where Sales LY shifts the date filter back one year on dim_date. It needs a marked date table. From the data, 2018 sales were 20.36% above 2017.

**Q8. What does discount do to profit in your data?**
Lines with no discount have a 29.5% margin; 10-20% discount 11.6%; above 20% the margins are negative (20-30%: -10.1%; above 50%: -119.2%). Source: `data/analytics/discount_bands.csv`. This is an association in this dataset, not proof of cause.

**Q9. Which models did you compare and which won?**
Holt-Winters (additive), ARIMA(1,1,1) and SARIMA(1,1,1)(0,1,1,12) on a 12-month hold-out (2018). Holt-Winters is best: MAE 10,896.63, RMSE 14,117.72, MAPE 18.51%. SARIMA MAPE is 33.98% and ARIMA 54.11%.

**Q10. Why is ARIMA the worst here?**
Non-seasonal ARIMA cannot represent the yearly pattern (peaks in September, November, December). SARIMA adds seasonality but 36 training months is little to estimate it. These are plausible reasons; the data show the ranking, not the cause.

**Q11. Define MAE, RMSE and MAPE.**
MAE is the mean absolute error; RMSE is the square root of the mean squared error (penalises large misses); MAPE is the mean of absolute error divided by actual, in percent. The DAX versions are checked against the reported values.

**Q12. How reliable is the forecast?**
Modest. Only 48 months exist, the hold-out is one year, and the Holt-Winters 95% interval is approximate (+/-1.96 x residual standard deviation). Rolling-origin cross-validation (7 folds) gave a mean MAPE of 21.67% for Holt-Winters additive (damped). The 2019 total forecast is 910,035.16, which is +24.12% against 2018.

**Q13. Why do ARIMA and SARIMA show nothing for 2019?**
Only the best model was refit on all 48 months and projected, so only it has future rows. The forecast page title states this.

**Q14. What is RFM and how did you do it?**
Recency, Frequency, Monetary value per customer. The data has no RFM column, so a DAX calculated table derives it with a reference date of 31 Dec 2018 and rule-based segments (the thresholds are my choice, not a standard). Counts: Champions 298, Loyal 250, Needs attention 113, At risk / Lost 100, Recent 32.

**Q15. Why measures and not calculated columns?**
Measures are evaluated in filter context, respond to slicers and do not bloat the model. Columns are used only for row-level attributes such as discount_band.

**Q16. What data issues did you handle?**
806 stray empty rows in the raw file were removed and 11 missing postal codes (Burlington, Vermont) were noted. See `reports/cleaning_log.md`.

**Q17. What are the limits?**
One public sample dataset, no live refresh, a short series, and discount/profit findings are correlations. State honestly whether the DAX was verified in Power BI Desktop at the time of the viva.

**Q18. How would you refresh it?**
Rerun the Python pipeline, which rewrites the CSVs, then Refresh in Power BI; the DataFolder parameter points to them.

**Q19. How does the Model slicer work?**
dim_model is the one-side for fact_forecast and model_accuracy. The measure Selected Model uses SELECTEDVALUE and falls back to the best model when none or several are selected.

**Q20. Why four pages and these colours?**
Each page answers one question: overview, products/regions/discounts, customers, forecast. A single theme file keeps colours consistent; green/amber/red are used only for status.
