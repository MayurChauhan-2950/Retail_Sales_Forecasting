# DAX measure reference

84 measures in 8 display folders. Copy-ready code is in `measures.dax` (same content). **All DAX was carefully reviewed for syntax and logic but has NOT been executed in Power BI Desktop** (it is not installed on the build machine). The `Check value` column holds numbers computed with pandas from `data/curated` and `data/forecast`; if your card shows the same number, the measure and the model are correct.

Setup: create a blank table `_Measures` (Home > Enter data, one dummy column, then delete the column after the first measure), create the two calculated tables from `measures.dax` (`Top N`, `RFM`), then add the measures. For each measure set **Format** (Measure tools) and **Display folder** (Model view > Properties). Date measures assume `dim_date` is marked as the date table (Table tools > Mark as date table > Date).

Colour measures return hex text; use them via *Conditional formatting > Format style: Field value*.

Check values assume NO filters unless a filter is stated (for example `Year 2018 selected` means a slicer or visual filter dim_date[Year] = 2018).

## 01 Core KPIs

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **Total Sales** | `$#,##0` | Sum of line sales. | KPI card, every page | 2,297,200.86 (all data) |
| **Total Profit** | `$#,##0` | Sum of line profit (negative lines included). | KPI card, profit charts | 286,397.02 (all data) |
| **Profit Margin %** | `0.0%` | Profit divided by sales; ratio of sums, not average of ratios. | KPI card, category/region bars, discount band chart | 12.47% (all data) |
| **Orders** | `#,##0` | Distinct orders (an order has several lines). | KPI card | 5,009 |
| **Customers** | `#,##0` | Distinct customers who bought. | KPI card, segment donut | 793 |
| **Avg Order Value** | `$#,##0.00` | Sales per order. | KPI card | 458.61 |
| **Quantity** | `#,##0` | Units sold. | KPI card, product table | 37,873 |
| **Order Lines** | `#,##0` | Rows of the fact table (one per product on an order). | Data-check card | 9,994 |
| **Avg Discount %** | `0.0%` | Simple average of the line discount rate. | KPI card (page 1, page 4) | 15.62% |
| **Sales per Customer** | `$#,##0.00` | Average revenue per customer. | Customers page card | 2,896.85 |
| **Avg Days to Ship** | `0.0` | Mean of ship date minus order date (column built in Power Query). | Optional card | 3.96 |

## 02 Time Intelligence

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **Sales LY** | `$#,##0` | Sales in the same period one year earlier (blank when there is no current sales, so 2019 forecast months stay clean). | Trend line (comparison series), KPI subtitle | Year 2018 selected: 609,205.60 (= 2017 sales) |
| **Profit LY** | `$#,##0` | Profit one year earlier. | KPI subtitle | Year 2018 selected: 81,795.17 |
| **Sales YoY Change** | `$#,##0;-$#,##0` | Absolute change versus last year. | Tooltip | Year 2018: 124,009.66 |
| **YoY %** | `+0.0%;-0.0%;0.0%` | Percentage growth versus the same period last year. | KPI card variance, trend tooltip | Year 2018 selected: +20.36% (2015 has no LY so shows blank) |
| **Profit YoY %** | `+0.0%;-0.0%;0.0%` | Profit growth versus last year. | KPI card variance | Year 2018 selected: +14.24% |
| **Sales PM** | `$#,##0` | Sales in the previous month. | Tooltip | Dec 2018 selected: 118,447.82 |
| **MoM %** | `+0.0%;-0.0%;0.0%` | Month-over-month growth. | Trend tooltip | Dec 2018 selected: -29.23% |
| **Sales YTD** | `$#,##0` | Year-to-date sales (resets each 1 January). | Trend (second line), KPI subtitle | Dec 2018 selected: 733,215.26 (= full 2018) |
| **Profit YTD** | `$#,##0` | Year-to-date profit. | Optional line | Dec 2018 selected: 93,439.27 |
| **Rolling 3M Sales** | `$#,##0` | Sum of the latest 3 months ending at the last date in context. | Trend line (smoothed series) | Dec 2018 selected: 280,054.07 (Oct+Nov+Dec 2018) |
| **Rolling 3M Avg Sales** | `$#,##0` | 3-month moving average (assumes 3 complete months). | Trend line | Dec 2018 selected: 93,351.36 |

## 03 Ranking and Share

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **Sales Share %** | `0.0%` | Row share of everything currently selected (respects slicers). | Donut/bar data labels, tables | Category rows add to 100%; Technology = 36.4% |
| **Sales Share % of Category** | `0.0%` | Sub-category share inside its visible category group. | Sub-category matrix | Copiers/Technology: 17.9% (all-years, only Technology visible) |
| **Profit Rank (SubCategory)** | `0` | Rank 1 = most profitable sub-category in the current selection. | Sub-category table | Copiers = 1 (55,617.82); Tables = 17 (-17,725.48) |
| **Sales Rank (Product)** | `0` | Rank of a product by sales in the current selection. | Top-N bar / table | Canon imageCLASS 2200 Advanced Copier = 1 (61,599.82) |
| **Top N Value** | `0` | Reads the Top-N slicer (calculated table 'Top N'); defaults to 10. | Used by Top N Flag | 10 when slicer untouched |
| **Top N Flag** | `0` | 1 if product is in the Top N; put on the visual filter pane as 'is 1'. | Top-N product bar (visual-level filter) | With default 10, the bar shows exactly 10 products (ties may add more) |

## 04 Discount and Profit

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **Sales No Discount** | `$#,##0` | Sales on lines with 0% discount. | Discount page card/table | 1,087,908.47 |
| **Sales Discounted** | `$#,##0` | Sales on lines with any discount. | Discount page card | 1,209,292.39 |
| **Discounted Sales Share %** | `0.0%` | Share of sales sold with a discount. | Discount page card | 52.64% |
| **Profit Low Discount** | `$#,##0` | Profit where discount is over 0% up to 20%. | Band table | 100,785.47 |
| **Profit Medium Discount** | `$#,##0` | Profit where discount is over 20% up to 40%. | Band table | -35,817.47 |
| **Profit High Discount** | `$#,##0` | Profit where discount is over 40% (loss-making). | Discount page KPI card | -99,558.59 |
| **Loss Lines** | `#,##0` | Count of order lines with negative profit. | Discount page card | 1,871 |
| **Loss Lines %** | `0.0%` | Share of lines that lose money. | Discount page card | 18.72% |
| **Loss Amount** | `$#,##0;-$#,##0` | Sum of all negative profit. | Discount page card | -156,131.29 |
| **Weighted Avg Discount %** | `0.0%` | Discount rate weighted by sales value. | Tooltip / scatter | 14.04% |

## 05 Forecast Arena

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **Actual Sales (Series)** | `$#,##0` | Monthly actual sales from the forecast file (same data as fact_sales, rounded per month). | Forecast line chart (Actual line) | All months 2,297,200.84 (differs from Total Sales by 0.02 rounding) |
| **Actual vs Fact Difference** | `#,##0.00` | Reconciliation: should be ~0 (cents of rounding). | Test card only (delete after testing) | -0.02 for all years |
| **Best Model (RMSE)** | `@` | Name of the model with the lowest 2018 hold-out RMSE (ignores slicers). | Best-model callout, default for Selected Model | Holt-Winters (additive) |
| **Best Model (MAPE)** | `@` | Same, ranked by MAPE. | Callout (cross-check) | Holt-Winters (additive) |
| **Selected Model** | `@` | Model chosen in the slicer; falls back to the best model if none or several are selected. | Dynamic titles, forecast measures | Holt-Winters (additive) when slicer is empty |
| **Forecast (All Models)** | `$#,##0` | Raw forecast; use with model in Legend to draw one line per model. | Forecast line chart (legend = model) | Jan 2018, Holt-Winters: 29,667.48 |
| **Forecast (Selected Model)** | `$#,##0` | Forecast of the single selected model across hold-out and future months. | Forecast line chart (focus line) | Jan 2019, Holt-Winters: 49,386.76 |
| **Holdout Actual** | `$#,##0` | Actual sales in the 12 hold-out months. | Error table / column chart | Jan 2018: 43,971.37 |
| **Holdout Forecast** | `$#,##0` | Selected model's prediction for the hold-out months. | Error table | Jan 2018, Holt-Winters: 29,667.48 |
| **Forecast Error** | `+#,##0;-#,##0;0` | Forecast minus actual (positive = over-forecast). | Error column chart, tooltip | Jan 2018 Holt-Winters: -14,303.89 |
| **Abs Forecast Error** | `#,##0` | Absolute error. | Error table | Jan 2018 Holt-Winters: 14,303.89 |
| **APE %** | `0.0%` | Absolute percentage error for one month. | Error table | Jan 2018 Holt-Winters: 32.53% |
| **MAPE by Model (recomputed)** | `0.0%` | MAPE recomputed from the monthly hold-out rows; put dim_model[model] on rows. | Accuracy table (cross-check column) | Holt-Winters (additive): 18.51%; ARIMA 54.11%; SARIMA 33.98% |
| **MAE** | `#,##0` | Stored hold-out MAE per model (from model_accuracy.csv). | Accuracy table | Holt-Winters (additive): 10,896.63 |
| **RMSE** | `#,##0` | Stored hold-out RMSE per model. | Accuracy table | Holt-Winters (additive): 14,117.72 |
| **MAPE % (reported)** | `0.0%` | Stored hold-out MAPE per model as a percentage. | Accuracy table, bar chart | Holt-Winters (additive): 18.51% |
| **Model Rank (RMSE)** | `0` | 1 = lowest RMSE. | Accuracy table | Holt-Winters 1, SARIMA 2, ARIMA 3 |
| **Is Best Model** | `0` | 1 on the best model's row. | Table conditional formatting / star icon | 1 only on the Holt-Winters row |
| **Forecast Lower 95** | `$#,##0` | Lower end of the 95% interval (future months only). | Forecast chart (dotted line / error bar) | Jan 2019: 31,778.18 |
| **Forecast Upper 95** | `$#,##0` | Upper end of the 95% interval. | Forecast chart | Jan 2019: 66,995.34 |
| **Forecast Interval Width** | `$#,##0` | Upper minus lower; use as the visible part of a stacked-area band. | Optional band | 35,217.16 for each Holt-Winters month |
| **Forecast Total 2019** | `$#,##0` | Sum of the 12 projected months for the selected model. | Forecast KPI card | Holt-Winters (additive): 910,035.16 |
| **Forecast Growth vs 2018** | `+0.0%;-0.0%` | Projected 2019 versus actual 2018. | Forecast KPI card | +24.12% (using 733,215.25 for 2018) |
| **Has Future Forecast** | `0` | 1 if a 2019 projection is stored for the selected model. | Dynamic title; message when 0 | 1 for Holt-Winters; 0 for ARIMA/SARIMA (only the best model was projected to 2019 - check the folder if this changes) |

## 06 KPI Colours

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **YoY Colour** | `@` | Green when growing, red when shrinking. | Conditional format > Font colour > Field value | 2018: green |
| **YoY Arrow** | `@` | Up/down triangle text. | Card subtitle | 2018: up triangle |
| **Margin Colour** | `@` | Margin traffic light: 15%+ green, 10-15% amber, below red. | Margin card, bars | Overall 12.5%: amber; Furniture 2.5%: red |
| **Profit Colour** | `@` | Blue for profit, red for loss. | Bar chart > Data colours > Field value | Tables, Bookcases, Supplies: red |
| **MAPE Colour** | `@` | MAPE traffic light: up to 20% green, up to 35% amber, else red. | Accuracy table MAPE column | Holt-Winters green (18.5%), SARIMA amber (34.0%), ARIMA red (54.1%) |
| **Best Model Row Colour** | `@` | Light blue background on the best model's row. | Accuracy table > Cell background > Field value | Holt-Winters row blue |
| **Error Colour** | `@` | Over-forecast amber, under-forecast blue. | Error column chart | Jan 2018 Holt-Winters under-forecast: blue |

## 07 Titles and Labels

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **Period Label** | `@` | First and last month that has sales under the current filters. | Used inside titles | No filters: Jan 2015 - Dec 2018 |
| **Category Label** | `@` | Selected category or 'All categories'. | Titles | All categories |
| **Region Label** | `@` | Selected region or 'All regions'. | Titles | All regions |
| **Title - Sales Trend** | `@` | Trend chart title that follows the date filter. | Trend chart > Title > fx | Monthly sales and profit | Jan 2015 - Dec 2018 |
| **Title - Category** | `@` | Breakdown title that follows the region slicer. | Category chart title | Sales and margin by category | All regions |
| **Title - Region** | `@` | Region chart title that follows the category slicer. | Region chart title | Sales by region | All categories |
| **Title - Discount** | `@` | Discount chart title. | Page 4 title | Profit margin by discount band | All categories | All regions |
| **Title - Forecast** | `@` | Forecast chart title with a safe note when no future values exist. | Forecast chart title | Actual vs forecast | model: Holt-Winters (additive) |
| **Best Model Callout** | `@` | One-sentence callout text. | Card on Forecast Arena | Best model on the 2018 hold-out: Holt-Winters (additive) (RMSE 14,118, MAPE 18.5%) |
| **Title Safe - Sales** | `@` | Never shows a blank title: warns when filters remove all data. | Page 1 headline text box (fx) | Total sales $2,297,201 | Jan 2015 - Dec 2018 |
| **Data Source Note** | `@` | Honest sample-vs-real footnote for every page. | Footer text box on all pages | Source: public 'Sample - Superstore' dataset, 9,994 order lines. ... |

## 08 Customer Segments (RFM)

| Measure | Format | What it does | Feeds visual | Check value |
|---|---|---|---|---|
| **RFM Customers** | `#,##0` | Customers in the current RFM segment selection. | RFM segment bar | Champions 298, Loyal 250, Needs attention 113, At risk / Lost 100, Recent 32 |
| **Avg Recency (days)** | `0` | Mean days since last order (reference date = last order date + 1). | RFM table | 147.8 (all customers) |
| **Avg Frequency (orders)** | `0.0` | Mean distinct orders per customer. | RFM table | 6.32 |
| **RFM Monetary** | `$#,##0` | Total sales of the customers in selection. | RFM bar | Champions 1,094,660.80 |

## Calculated tables

- `Top N` = `GENERATESERIES(3, 20, 1)`; feeds the Top-N slicer.
- `RFM` = customer-level Recency / Frequency / Monetary plus a rule-based `RFMSegment`. Rules: Champions = last order within 90 days and 6+ orders; Loyal = within 180 days and 4+ orders; Recent = within 90 days; At risk / Lost = over 365 days; otherwise Needs attention. The data has no RFM column, so this is derived in DAX; the thresholds are a teaching choice, say so in the viva.
- RFM check counts (pandas, reference date 2018-12-31): Champions 298, Loyal 250, Needs attention 113, At risk / Lost 100, Recent 32.

## Notes and limits

- `Forecast Lower 95` / `Upper 95` are blank for hold-out months by design (the pipeline stores intervals only for the future forecast).
- Only the best model has 2019 values in `sales_forecast.csv`; choose ARIMA or SARIMA in the slicer and the future part is empty. `Title - Forecast` says so.
- Holt-Winters interval is an approximation (+/-1.96 x residual standard deviation), as stated in the project README.
- `Rolling 3M Sales` and `Sales LY` return blank for months without sales so 2019 stays clean.
- RFM and sales checks use order dates 2015-01-03 to 2018-12-30.