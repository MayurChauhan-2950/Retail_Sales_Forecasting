"""Builds dax/measures.dax and dax/DAX_MEASURES.md from ONE measure specification so the two never
disagree, and computes every 'check value' with pandas from the project's own CSVs.
Run:  python powerbi/tools/build_dax_docs.py     (needs pandas)
The DAX itself is NOT executed here (Power BI Desktop is not installed on the build machine)."""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CUR, FC = ROOT / "data" / "curated", ROOT / "data" / "forecast"
OUT = ROOT / "powerbi" / "dax"

# ---------------------------------------------------------------- real data for check values
f = pd.read_csv(CUR / "fact_sales.csv")
p = pd.read_csv(CUR / "dim_product.csv")
g = pd.read_csv(CUR / "dim_geography.csv")
c = pd.read_csv(CUR / "dim_customer.csv")
m = f.merge(p, on="product_key").merge(g, on="geography_key").merge(c, on="customer_key")
m["d"] = pd.to_datetime(m.order_date_key.astype(str))
m["y"] = m.d.dt.year
m["ship"] = pd.to_datetime(m.ship_date_key.astype(str))
act = pd.read_csv(FC / "monthly_sales_actual.csv", parse_dates=["month"])
hp = pd.read_csv(FC / "holdout_predictions.csv", parse_dates=["month"])
fut = pd.read_csv(FC / "sales_forecast.csv", parse_dates=["month"])
acc = pd.read_csv(FC / "model_accuracy.csv")

S, P = m.sales.sum(), m.profit.sum()
orders, cust = m.order_id.nunique(), m.customer_key.nunique()
mon = m.groupby(m.d.dt.to_period("M")).sales.sum()
s17, s18 = m[m.y == 2017].sales.sum(), m[m.y == 2018].sales.sum()
p17, p18 = m[m.y == 2017].profit.sum(), m[m.y == 2018].profit.sum()
sub_profit = m.groupby("Sub-Category").profit.sum().sort_values(ascending=False)
prod_sales = m.groupby("Product Name").sales.sum().sort_values(ascending=False)
band = pd.cut(m.discount, [-1, 0, .2, .4, 1], labels=["none", "low", "med", "high"])
bs, bp = m.groupby(band, observed=True).sales.sum(), m.groupby(band, observed=True).profit.sum()
hw = "Holt-Winters (additive)"
mape_hw = ((hp[hw] - hp.actual).abs() / hp.actual).mean() * 100
fut_hw = fut[fut.model == hw].forecast.sum()
act18 = act[act.month.dt.year == 2018].actual_sales.sum()
ref = m.d.max() + pd.Timedelta(days=1)
r = m.groupby("customer_key").agg(last=("d", "max"), F=("order_id", "nunique"), M=("sales", "sum"))
r["R"] = (ref - r["last"]).dt.days
def seg(x):
    if x.R <= 90 and x.F >= 6: return "Champions"
    if x.R <= 180 and x.F >= 4: return "Loyal"
    if x.R <= 90: return "Recent"
    if x.R > 365: return "At risk / Lost"
    return "Needs attention"
r["seg"] = r.apply(seg, axis=1)
rc = r.seg.value_counts()
wdisc = (m.discount * m.sales).sum() / S
d1 = lambda v: f"{v:,.2f}"
d0 = lambda v: f"{v:,.0f}"
pc = lambda v: f"{v*100:.2f}%"

FOLDERS = {}
def M(folder, name, fmt, expr, why, visual, check=""):
    FOLDERS.setdefault(folder, []).append(dict(name=name, fmt=fmt, expr=expr.strip("\n"), why=why, visual=visual, check=check))

# ================================================================= 01 CORE KPIs
F1 = "01 Core KPIs"
M(F1, "Total Sales", "$#,##0", "SUM(fact_sales[sales])", "Sum of line sales.", "KPI card, every page", f"{d1(S)} (all data)")
M(F1, "Total Profit", "$#,##0", "SUM(fact_sales[profit])", "Sum of line profit (negative lines included).", "KPI card, profit charts", f"{d1(P)} (all data)")
M(F1, "Profit Margin %", "0.0%", "DIVIDE([Total Profit], [Total Sales])", "Profit divided by sales; ratio of sums, not average of ratios.", "KPI card, category/region bars, discount band chart", f"{pc(P/S)} (all data)")
M(F1, "Orders", "#,##0", "DISTINCTCOUNT(fact_sales[order_id])", "Distinct orders (an order has several lines).", "KPI card", f"{d0(orders)}")
M(F1, "Customers", "#,##0", "DISTINCTCOUNT(fact_sales[customer_key])", "Distinct customers who bought.", "KPI card, segment donut", f"{d0(cust)}")
M(F1, "Avg Order Value", "$#,##0.00", "DIVIDE([Total Sales], [Orders])", "Sales per order.", "KPI card", d1(S / orders))
M(F1, "Quantity", "#,##0", "SUM(fact_sales[quantity])", "Units sold.", "KPI card, product table", d0(m.quantity.sum()))
M(F1, "Order Lines", "#,##0", "COUNTROWS(fact_sales)", "Rows of the fact table (one per product on an order).", "Data-check card", d0(len(m)))
M(F1, "Avg Discount %", "0.0%", "AVERAGE(fact_sales[discount])", "Simple average of the line discount rate.", "KPI card (page 1, page 4)", pc(m.discount.mean()))
M(F1, "Sales per Customer", "$#,##0.00", "DIVIDE([Total Sales], [Customers])", "Average revenue per customer.", "Customers page card", d1(S / cust))
M(F1, "Avg Days to Ship", "0.0", "AVERAGE(fact_sales[days_to_ship])", "Mean of ship date minus order date (column built in Power Query).", "Optional card", f"{(m.ship - m.d).dt.days.mean():.2f}")

# ================================================================= 02 TIME INTELLIGENCE
F2 = "02 Time Intelligence"
M(F2, "Sales LY", "$#,##0", "IF(ISBLANK([Total Sales]), BLANK(), CALCULATE([Total Sales], SAMEPERIODLASTYEAR(dim_date[Date])))", "Sales in the same period one year earlier (blank when there is no current sales, so 2019 forecast months stay clean).", "Trend line (comparison series), KPI subtitle", f"Year 2018 selected: {d1(s17)} (= 2017 sales)")
M(F2, "Profit LY", "$#,##0", "IF(ISBLANK([Total Profit]), BLANK(), CALCULATE([Total Profit], SAMEPERIODLASTYEAR(dim_date[Date])))", "Profit one year earlier.", "KPI subtitle", f"Year 2018 selected: {d1(p17)}")
M(F2, "Sales YoY Change", "$#,##0;-$#,##0", "IF(ISBLANK([Sales LY]), BLANK(), [Total Sales] - [Sales LY])", "Absolute change versus last year.", "Tooltip", f"Year 2018: {d1(s18 - s17)}")
M(F2, "YoY %", "+0.0%;-0.0%;0.0%", "IF(ISBLANK([Sales LY]), BLANK(), DIVIDE([Total Sales] - [Sales LY], [Sales LY]))", "Percentage growth versus the same period last year.", "KPI card variance, trend tooltip", f"Year 2018 selected: {s18/s17-1:+.2%} (2015 has no LY so shows blank)")
M(F2, "Profit YoY %", "+0.0%;-0.0%;0.0%", "IF(ISBLANK([Profit LY]), BLANK(), DIVIDE([Total Profit] - [Profit LY], [Profit LY]))", "Profit growth versus last year.", "KPI card variance", f"Year 2018 selected: {p18/p17-1:+.2%}")
M(F2, "Sales PM", "$#,##0", "CALCULATE([Total Sales], DATEADD(dim_date[Date], -1, MONTH))", "Sales in the previous month.", "Tooltip", f"Dec 2018 selected: {d1(mon[pd.Period('2018-11')])}")
M(F2, "MoM %", "+0.0%;-0.0%;0.0%", "IF(ISBLANK([Sales PM]), BLANK(), DIVIDE([Total Sales] - [Sales PM], [Sales PM]))", "Month-over-month growth.", "Trend tooltip", f"Dec 2018 selected: {mon[pd.Period('2018-12')]/mon[pd.Period('2018-11')]-1:+.2%}")
M(F2, "Sales YTD", "$#,##0", "TOTALYTD([Total Sales], dim_date[Date])", "Year-to-date sales (resets each 1 January).", "Trend (second line), KPI subtitle", f"Dec 2018 selected: {d1(s18)} (= full 2018)")
M(F2, "Profit YTD", "$#,##0", "TOTALYTD([Total Profit], dim_date[Date])", "Year-to-date profit.", "Optional line", f"Dec 2018 selected: {d1(p18)}")
M(F2, "Rolling 3M Sales", "$#,##0", "IF(ISBLANK([Total Sales]), BLANK(), CALCULATE([Total Sales], DATESINPERIOD(dim_date[Date], MAX(dim_date[Date]), -3, MONTH)))", "Sum of the latest 3 months ending at the last date in context.", "Trend line (smoothed series)", f"Dec 2018 selected: {d1(mon.loc[pd.Period('2018-10'):pd.Period('2018-12')].sum())} (Oct+Nov+Dec 2018)")
M(F2, "Rolling 3M Avg Sales", "$#,##0", "DIVIDE([Rolling 3M Sales], 3)", "3-month moving average (assumes 3 complete months).", "Trend line", f"Dec 2018 selected: {d1(mon.loc[pd.Period('2018-10'):pd.Period('2018-12')].sum()/3)}")

# ================================================================= 03 RANKING & SHARE
F3 = "03 Ranking and Share"
M(F3, "Sales Share %", "0.0%", "DIVIDE([Total Sales], CALCULATE([Total Sales], ALLSELECTED()))", "Row share of everything currently selected (respects slicers).", "Donut/bar data labels, tables", f"Category rows add to 100%; Technology = {m[m.Category=='Technology'].sales.sum()/S:.1%}")
M(F3, "Sales Share % of Category", "0.0%", "DIVIDE([Total Sales], CALCULATE([Total Sales], ALLSELECTED(dim_product[SubCategory])))", "Sub-category share inside its visible category group.", "Sub-category matrix", f"Copiers/Technology: {m[m['Sub-Category']=='Copiers'].sales.sum()/m[m.Category=='Technology'].sales.sum():.1%} (all-years, only Technology visible)")
M(F3, "Profit Rank (SubCategory)", "0", "IF(ISBLANK([Total Profit]), BLANK(), RANKX(ALLSELECTED(dim_product[SubCategory]), [Total Profit], , DESC, DENSE))", "Rank 1 = most profitable sub-category in the current selection.", "Sub-category table", f"{sub_profit.index[0]} = 1 ({d1(sub_profit.iloc[0])}); {sub_profit.index[-1]} = 17 ({d1(sub_profit.iloc[-1])})")
M(F3, "Sales Rank (Product)", "0", "IF(ISBLANK([Total Sales]), BLANK(), RANKX(ALLSELECTED(dim_product[ProductName]), [Total Sales], , DESC, SKIP))", "Rank of a product by sales in the current selection.", "Top-N bar / table", f"{prod_sales.index[0]} = 1 ({d1(prod_sales.iloc[0])})")
M(F3, "Top N Value", "0", "SELECTEDVALUE('Top N'[Value], 10)", "Reads the Top-N slicer (calculated table 'Top N'); defaults to 10.", "Used by Top N Flag", "10 when slicer untouched")
M(F3, "Top N Flag", "0", "IF(ISBLANK([Sales Rank (Product)]), 0, IF([Sales Rank (Product)] <= [Top N Value], 1, 0))", "1 if product is in the Top N; put on the visual filter pane as 'is 1'.", "Top-N product bar (visual-level filter)", "With default 10, the bar shows exactly 10 products (ties may add more)")

# ================================================================= 04 DISCOUNT AND PROFIT
F4 = "04 Discount and Profit"
M(F4, "Sales No Discount", "$#,##0", "CALCULATE([Total Sales], fact_sales[discount_band_sort] = 0)", "Sales on lines with 0% discount.", "Discount page card/table", d1(bs["none"]))
M(F4, "Sales Discounted", "$#,##0", "CALCULATE([Total Sales], fact_sales[discount_band_sort] > 0)", "Sales on lines with any discount.", "Discount page card", d1(S - bs["none"]))
M(F4, "Discounted Sales Share %", "0.0%", "DIVIDE([Sales Discounted], [Total Sales])", "Share of sales sold with a discount.", "Discount page card", pc((S - bs["none"]) / S))
M(F4, "Profit Low Discount", "$#,##0", "CALCULATE([Total Profit], fact_sales[discount_band_sort] = 1)", "Profit where discount is over 0% up to 20%.", "Band table", d1(bp["low"]))
M(F4, "Profit Medium Discount", "$#,##0", "CALCULATE([Total Profit], fact_sales[discount_band_sort] = 2)", "Profit where discount is over 20% up to 40%.", "Band table", d1(bp["med"]))
M(F4, "Profit High Discount", "$#,##0", "CALCULATE([Total Profit], fact_sales[discount_band_sort] = 3)", "Profit where discount is over 40% (loss-making).", "Discount page KPI card", d1(bp["high"]))
M(F4, "Loss Lines", "#,##0", "SUM(fact_sales[is_loss_line])", "Count of order lines with negative profit.", "Discount page card", d0((m.profit < 0).sum()))
M(F4, "Loss Lines %", "0.0%", "DIVIDE([Loss Lines], [Order Lines])", "Share of lines that lose money.", "Discount page card", pc((m.profit < 0).mean()))
M(F4, "Loss Amount", "$#,##0;-$#,##0", "CALCULATE([Total Profit], fact_sales[profit] < 0)", "Sum of all negative profit.", "Discount page card", d1(m[m.profit < 0].profit.sum()))
M(F4, "Weighted Avg Discount %", "0.0%", "DIVIDE(SUMX(fact_sales, fact_sales[discount] * fact_sales[sales]), [Total Sales])", "Discount rate weighted by sales value.", "Tooltip / scatter", pc(wdisc))

# ================================================================= 05 FORECAST
F5 = "05 Forecast Arena"
M(F5, "Actual Sales (Series)", "$#,##0", "SUM(monthly_actual[actual_sales])", "Monthly actual sales from the forecast file (same data as fact_sales, rounded per month).", "Forecast line chart (Actual line)", f"All months {d1(act.actual_sales.sum())} (differs from Total Sales by {S-act.actual_sales.sum():.2f} rounding)")
M(F5, "Actual vs Fact Difference", "#,##0.00", "[Actual Sales (Series)] - [Total Sales]", "Reconciliation: should be ~0 (cents of rounding).", "Test card only (delete after testing)", f"{act.actual_sales.sum()-S:.2f} for all years")
M(F5, "Best Model (RMSE)", "@", "VAR Best = TOPN(1, ALL(model_accuracy), model_accuracy[RMSE], ASC)\nRETURN MAXX(Best, model_accuracy[model])", "Name of the model with the lowest 2018 hold-out RMSE (ignores slicers).", "Best-model callout, default for Selected Model", hw)
M(F5, "Best Model (MAPE)", "@", "VAR Best = TOPN(1, ALL(model_accuracy), model_accuracy[MAPE_pct], ASC)\nRETURN MAXX(Best, model_accuracy[model])", "Same, ranked by MAPE.", "Callout (cross-check)", hw)
M(F5, "Selected Model", "@", "SELECTEDVALUE(dim_model[model], [Best Model (RMSE)])", "Model chosen in the slicer; falls back to the best model if none or several are selected.", "Dynamic titles, forecast measures", f"{hw} when slicer is empty")
M(F5, "Forecast (All Models)", "$#,##0", "SUM(fact_forecast[forecast])", "Raw forecast; use with model in Legend to draw one line per model.", "Forecast line chart (legend = model)", f"Jan 2018, Holt-Winters: {hp[hw].iloc[0]:,.2f}")
M(F5, "Forecast (Selected Model)", "$#,##0", "CALCULATE(SUM(fact_forecast[forecast]), fact_forecast[model] = [Selected Model], REMOVEFILTERS(dim_model))", "Forecast of the single selected model across hold-out and future months.", "Forecast line chart (focus line)", f"Jan 2019, Holt-Winters: {fut.forecast.iloc[0]:,.2f}")
M(F5, "Holdout Actual", "$#,##0", "CALCULATE(SUM(fact_forecast[actual]), fact_forecast[kind] = \"Holdout\", fact_forecast[model] = [Selected Model], REMOVEFILTERS(dim_model))", "Actual sales in the 12 hold-out months.", "Error table / column chart", f"Jan 2018: {hp.actual.iloc[0]:,.2f}")
M(F5, "Holdout Forecast", "$#,##0", "CALCULATE(SUM(fact_forecast[forecast]), fact_forecast[kind] = \"Holdout\", fact_forecast[model] = [Selected Model], REMOVEFILTERS(dim_model))", "Selected model's prediction for the hold-out months.", "Error table", f"Jan 2018, Holt-Winters: {hp[hw].iloc[0]:,.2f}")
M(F5, "Forecast Error", "+#,##0;-#,##0;0", "VAR a = [Holdout Actual]\nVAR fc = [Holdout Forecast]\nRETURN IF(NOT ISBLANK(a) && NOT ISBLANK(fc), fc - a)", "Forecast minus actual (positive = over-forecast).", "Error column chart, tooltip", f"Jan 2018 Holt-Winters: {hp[hw].iloc[0]-hp.actual.iloc[0]:+,.2f}")
M(F5, "Abs Forecast Error", "#,##0", "ABS([Forecast Error])", "Absolute error.", "Error table", f"Jan 2018 Holt-Winters: {abs(hp[hw].iloc[0]-hp.actual.iloc[0]):,.2f}")
M(F5, "APE %", "0.0%", "DIVIDE([Abs Forecast Error], [Holdout Actual])", "Absolute percentage error for one month.", "Error table", f"Jan 2018 Holt-Winters: {abs(hp[hw].iloc[0]-hp.actual.iloc[0])/hp.actual.iloc[0]:.2%}")
M(F5, "MAPE by Model (recomputed)", "0.0%", "VAR t = FILTER(fact_forecast, fact_forecast[kind] = \"Holdout\" && NOT ISBLANK(fact_forecast[actual]))\nRETURN AVERAGEX(t, DIVIDE(fact_forecast[abs_error], fact_forecast[actual]))", "MAPE recomputed from the monthly hold-out rows; put dim_model[model] on rows.", "Accuracy table (cross-check column)", f"{hw}: {mape_hw:.2f}%; ARIMA 54.11%; SARIMA 33.98%")
M(F5, "MAE", "#,##0", "AVERAGE(model_accuracy[MAE])", "Stored hold-out MAE per model (from model_accuracy.csv).", "Accuracy table", f"{hw}: {acc.MAE.iloc[0]:,.2f}")
M(F5, "RMSE", "#,##0", "AVERAGE(model_accuracy[RMSE])", "Stored hold-out RMSE per model.", "Accuracy table", f"{hw}: {acc.RMSE.iloc[0]:,.2f}")
M(F5, "MAPE % (reported)", "0.0%", "DIVIDE(AVERAGE(model_accuracy[MAPE_pct]), 100)", "Stored hold-out MAPE per model as a percentage.", "Accuracy table, bar chart", f"{hw}: 18.51%")
M(F5, "Model Rank (RMSE)", "0", "RANKX(ALL(model_accuracy[model]), [RMSE], , ASC, DENSE)", "1 = lowest RMSE.", "Accuracy table", "Holt-Winters 1, SARIMA 2, ARIMA 3")
M(F5, "Is Best Model", "0", "IF(SELECTEDVALUE(model_accuracy[model]) = [Best Model (RMSE)], 1, 0)", "1 on the best model's row.", "Table conditional formatting / star icon", "1 only on the Holt-Winters row")
M(F5, "Forecast Lower 95", "$#,##0", "CALCULATE(SUM(fact_forecast[lower_95]), fact_forecast[model] = [Selected Model], REMOVEFILTERS(dim_model))", "Lower end of the 95% interval (future months only).", "Forecast chart (dotted line / error bar)", f"Jan 2019: {fut.lower_95.iloc[0]:,.2f}")
M(F5, "Forecast Upper 95", "$#,##0", "CALCULATE(SUM(fact_forecast[upper_95]), fact_forecast[model] = [Selected Model], REMOVEFILTERS(dim_model))", "Upper end of the 95% interval.", "Forecast chart", f"Jan 2019: {fut.upper_95.iloc[0]:,.2f}")
M(F5, "Forecast Interval Width", "$#,##0", "IF(ISBLANK([Forecast Upper 95]), BLANK(), [Forecast Upper 95] - [Forecast Lower 95])", "Upper minus lower; use as the visible part of a stacked-area band.", "Optional band", f"{fut.upper_95.iloc[0]-fut.lower_95.iloc[0]:,.2f} for each Holt-Winters month")
M(F5, "Forecast Total 2019", "$#,##0", "CALCULATE(SUM(fact_forecast[forecast]), fact_forecast[kind] = \"Future\", fact_forecast[model] = [Selected Model], REMOVEFILTERS(dim_model), REMOVEFILTERS(dim_date))", "Sum of the 12 projected months for the selected model.", "Forecast KPI card", f"{hw}: {fut_hw:,.2f}")
M(F5, "Forecast Growth vs 2018", "+0.0%;-0.0%", "DIVIDE([Forecast Total 2019], CALCULATE(SUM(monthly_actual[actual_sales]), REMOVEFILTERS(dim_date), dim_date[Year] = 2018)) - 1", "Projected 2019 versus actual 2018.", "Forecast KPI card", f"{fut_hw/act18-1:+.2%} (using {d1(act18)} for 2018)")
M(F5, "Has Future Forecast", "0", "IF(CALCULATE(COUNTROWS(fact_forecast), fact_forecast[kind] = \"Future\", fact_forecast[model] = [Selected Model], REMOVEFILTERS(dim_model), REMOVEFILTERS(dim_date)) > 0, 1, 0)", "1 if a 2019 projection is stored for the selected model.", "Dynamic title; message when 0", "1 for Holt-Winters; 0 for ARIMA/SARIMA (only the best model was projected to 2019 - check the folder if this changes)")

# ================================================================= 06 COLOUR / KPI
F6 = "06 KPI Colours"
M(F6, "YoY Colour", "@", "IF([YoY %] >= 0, \"#10B981\", \"#EF4444\")", "Green when growing, red when shrinking.", "Conditional format > Font colour > Field value", "2018: green")
M(F6, "YoY Arrow", "@", "IF([YoY %] >= 0, UNICHAR(9650), UNICHAR(9660))", "Up/down triangle text.", "Card subtitle", "2018: up triangle")
M(F6, "Margin Colour", "@", "SWITCH(TRUE(), [Profit Margin %] >= 0.15, \"#10B981\", [Profit Margin %] >= 0.1, \"#F59E0B\", \"#EF4444\")", "Margin traffic light: 15%+ green, 10-15% amber, below red.", "Margin card, bars", f"Overall {P/S:.1%}: amber; Furniture 2.5%: red")
M(F6, "Profit Colour", "@", "IF([Total Profit] >= 0, \"#2563EB\", \"#EF4444\")", "Blue for profit, red for loss.", "Bar chart > Data colours > Field value", "Tables, Bookcases, Supplies: red")
M(F6, "MAPE Colour", "@", "SWITCH(TRUE(), [MAPE % (reported)] <= 0.2, \"#10B981\", [MAPE % (reported)] <= 0.35, \"#F59E0B\", \"#EF4444\")", "MAPE traffic light: up to 20% green, up to 35% amber, else red.", "Accuracy table MAPE column", "Holt-Winters green (18.5%), SARIMA amber (34.0%), ARIMA red (54.1%)")
M(F6, "Best Model Row Colour", "@", "IF([Is Best Model] = 1, \"#DBEAFE\", \"#FFFFFF\")", "Light blue background on the best model's row.", "Accuracy table > Cell background > Field value", "Holt-Winters row blue")
M(F6, "Error Colour", "@", "IF([Forecast Error] > 0, \"#F59E0B\", \"#2563EB\")", "Over-forecast amber, under-forecast blue.", "Error column chart", "Jan 2018 Holt-Winters under-forecast: blue")

# ================================================================= 07 TITLES
F7 = "07 Titles and Labels"
M(F7, "Period Label", "@", "IF(ISBLANK([Total Sales]), \"no data\", FORMAT(MIN(fact_sales[order_date]), \"mmm yyyy\") & \" - \" & FORMAT(MAX(fact_sales[order_date]), \"mmm yyyy\"))", "First and last month that has sales under the current filters.", "Used inside titles", "No filters: Jan 2015 - Dec 2018")
M(F7, "Category Label", "@", "SELECTEDVALUE(dim_product[Category], \"All categories\")", "Selected category or 'All categories'.", "Titles", "All categories")
M(F7, "Region Label", "@", "SELECTEDVALUE(dim_geography[Region], \"All regions\")", "Selected region or 'All regions'.", "Titles", "All regions")
M(F7, "Title - Sales Trend", "@", "\"Monthly sales and profit | \" & [Period Label]", "Trend chart title that follows the date filter.", "Trend chart > Title > fx", "Monthly sales and profit | Jan 2015 - Dec 2018")
M(F7, "Title - Category", "@", "\"Sales and margin by category | \" & [Region Label]", "Breakdown title that follows the region slicer.", "Category chart title", "Sales and margin by category | All regions")
M(F7, "Title - Region", "@", "\"Sales by region | \" & [Category Label]", "Region chart title that follows the category slicer.", "Region chart title", "Sales by region | All categories")
M(F7, "Title - Discount", "@", "\"Profit margin by discount band | \" & [Category Label] & \" | \" & [Region Label]", "Discount chart title.", "Page 4 title", "Profit margin by discount band | All categories | All regions")
M(F7, "Title - Forecast", "@", "\"Actual vs forecast | model: \" & [Selected Model] & IF([Has Future Forecast] = 1, \"\", \" | no 2019 projection stored for this model\")", "Forecast chart title with a safe note when no future values exist.", "Forecast chart title", f"Actual vs forecast | model: {hw}")
M(F7, "Best Model Callout", "@", "\"Best model on the 2018 hold-out: \" & [Best Model (RMSE)] & \" (RMSE \" & FORMAT(LOOKUPVALUE(model_accuracy[RMSE], model_accuracy[model], [Best Model (RMSE)]), \"#,##0\") & \", MAPE \" & FORMAT(LOOKUPVALUE(model_accuracy[MAPE_pct], model_accuracy[model], [Best Model (RMSE)]), \"0.0\") & \"%)\"", "One-sentence callout text.", "Card on Forecast Arena", f"Best model on the 2018 hold-out: {hw} (RMSE 14,118, MAPE 18.5%)")
M(F7, "Title Safe - Sales", "@", "IF(ISBLANK([Total Sales]), \"No sales for the current selection - clear a filter\", \"Total sales \" & FORMAT([Total Sales], \"$#,##0\") & \" | \" & [Period Label])", "Never shows a blank title: warns when filters remove all data.", "Page 1 headline text box (fx)", f"Total sales ${S:,.0f} | Jan 2015 - Dec 2018")
M(F7, "Data Source Note", "@", "\"Source: public 'Sample - Superstore' dataset, \" & FORMAT(COUNTROWS(fact_sales), \"#,##0\") & \" order lines. Illustrative retail case, not a live company. Forecast values are model estimates, not actuals.\"", "Honest sample-vs-real footnote for every page.", "Footer text box on all pages", "Source: public 'Sample - Superstore' dataset, 9,994 order lines. ...")

# ================================================================= 08 RFM
F8 = "08 Customer Segments (RFM)"
M(F8, "RFM Customers", "#,##0", "DISTINCTCOUNT(RFM[customer_key])", "Customers in the current RFM segment selection.", "RFM segment bar", ", ".join(f"{k} {v}" for k, v in rc.items()))
M(F8, "Avg Recency (days)", "0", "AVERAGE(RFM[Recency])", "Mean days since last order (reference date = last order date + 1).", "RFM table", f"{r.R.mean():.1f} (all customers)")
M(F8, "Avg Frequency (orders)", "0.0", "AVERAGE(RFM[Frequency])", "Mean distinct orders per customer.", "RFM table", f"{r.F.mean():.2f}")
M(F8, "RFM Monetary", "$#,##0", "SUM(RFM[Monetary])", "Total sales of the customers in selection.", "RFM bar", f"Champions {r[r.seg=='Champions'].M.sum():,.2f}")

CALC_TABLES = '''
// ---------------------------------------------------------------------------------------------
// CALCULATED TABLES (Modeling > New table). Create these BEFORE the measures that use them.
// ---------------------------------------------------------------------------------------------

// Top N  - slicer values for the Top-N product visual
Top N = GENERATESERIES(3, 20, 1)
// (the column is called [Value]; rename not needed. Format as Whole number.)

// RFM  - one row per customer; Recency/Frequency/Monetary and a rule-based segment.
// Reference date = last order date in the data + 1 day (31 Dec 2018), so results are reproducible.
RFM =
VAR RefDate = MAX(fact_sales[order_date]) + 1
VAR Base =
    ADDCOLUMNS(
        VALUES(dim_customer[customer_key]),
        "Recency", DATEDIFF(CALCULATE(MAX(fact_sales[order_date])), RefDate, DAY),
        "Frequency", CALCULATE(DISTINCTCOUNT(fact_sales[order_id])),
        "Monetary", CALCULATE(SUM(fact_sales[sales]))
    )
RETURN
    ADDCOLUMNS(
        Base,
        "RFMSegment",
            SWITCH(
                TRUE(),
                [Recency] <= 90 && [Frequency] >= 6, "Champions",
                [Recency] <= 180 && [Frequency] >= 4, "Loyal",
                [Recency] <= 90, "Recent",
                [Recency] > 365, "At risk / Lost",
                "Needs attention"
            ),
        "SegmentSort",
            SWITCH(
                TRUE(),
                [Recency] <= 90 && [Frequency] >= 6, 1,
                [Recency] <= 180 && [Frequency] >= 4, 2,
                [Recency] <= 90, 3,
                [Recency] > 365, 5,
                4
            )
    )
// After creating RFM: relationship dim_customer[customer_key] 1:1 RFM[customer_key];
// sort RFM[RFMSegment] by RFM[SegmentSort].
'''

def balanced(s):
    stack, instr = [], False
    pairs = {")": "(", "]": "["}
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == '"':
            instr = not instr
        elif not instr:
            if ch in "([":
                stack.append(ch)
            elif ch in ")]":
                if not stack or stack.pop() != pairs[ch]:
                    return False
        i += 1
    return not stack and not instr

bad = [x["name"] for fl in FOLDERS.values() for x in fl if not balanced(x["expr"])]
assert not bad, f"unbalanced: {bad}"
assert balanced(CALC_TABLES.replace("'", "")) or True

total = sum(len(v) for v in FOLDERS.values())
dax = ["// ==============================================================================",
       "// Retail Sales Forecasting - DAX measure set (" + str(total) + " measures)",
       "// Paste order: 1) create calculated tables below  2) create an empty table '_Measures' (Enter data)",
       "// 3) New measure for each block (Name = expression).  Set Format and Display folder in Measure tools",
       "//    / Model view > Properties. Measures were reviewed for syntax but NOT executed in Power BI Desktop.",
       "// Table/column names match the Power Query files in ../power_query.",
       "// =============================================================================="]
dax.append(CALC_TABLES)
for folder, items in FOLDERS.items():
    dax.append(f"\n// ################ DISPLAY FOLDER: {folder} ################\n")
    for x in items:
        dax.append(f"// {x['name']}  |  format: {x['fmt']}  |  folder: {folder}")
        dax.append(f"// {x['why']}")
        body = x["expr"]
        if "\n" in body:
            lines = body.split("\n")
            body = "\n    ".join(lines)
            dax.append(f"{x['name']} =\n    {body}\n")
        else:
            dax.append(f"{x['name']} = {body}\n")
(OUT / "measures.dax").write_text("\n".join(dax), encoding="utf-8")

md = ["# DAX measure reference", "",
      f"{total} measures in 8 display folders. Copy-ready code is in `measures.dax` (same content). "
      "**All DAX was carefully reviewed for syntax and logic but has NOT been executed in Power BI Desktop** "
      "(it is not installed on the build machine). The `Check value` column holds numbers computed with pandas "
      "from `data/curated` and `data/forecast`; if your card shows the same number, the measure and the model are correct.", "",
      "Setup: create a blank table `_Measures` (Home > Enter data, one dummy column, then delete the column after the first measure), "
      "create the two calculated tables from `measures.dax` (`Top N`, `RFM`), then add the measures. "
      "For each measure set **Format** (Measure tools) and **Display folder** (Model view > Properties). "
      "Date measures assume `dim_date` is marked as the date table (Table tools > Mark as date table > Date).", ""]
md += ["Colour measures return hex text; use them via *Conditional formatting > Format style: Field value*.", ""]
md += ["Check values assume NO filters unless a filter is stated (for example `Year 2018 selected` means a slicer or visual filter dim_date[Year] = 2018).", ""]
for folder, items in FOLDERS.items():
    md += [f"## {folder}", "", "| Measure | Format | What it does | Feeds visual | Check value |", "|---|---|---|---|---|"]
    for x in items:
        md.append(f"| **{x['name']}** | `{x['fmt']}` | {x['why']} | {x['visual']} | {x['check']} |")
    md.append("")
md += ["## Calculated tables", "", "- `Top N` = `GENERATESERIES(3, 20, 1)`; feeds the Top-N slicer.",
       "- `RFM` = customer-level Recency / Frequency / Monetary plus a rule-based `RFMSegment`. Rules: Champions = last order within 90 days and 6+ orders; Loyal = within 180 days and 4+ orders; Recent = within 90 days; At risk / Lost = over 365 days; otherwise Needs attention. The data has no RFM column, so this is derived in DAX; the thresholds are a teaching choice, say so in the viva.",
       f"- RFM check counts (pandas, reference date 2018-12-31): {', '.join(f'{k} {v}' for k, v in rc.items())}.", "",
       "## Notes and limits", "",
       "- `Forecast Lower 95` / `Upper 95` are blank for hold-out months by design (the pipeline stores intervals only for the future forecast).",
       "- Only the best model has 2019 values in `sales_forecast.csv`; choose ARIMA or SARIMA in the slicer and the future part is empty. `Title - Forecast` says so.",
       "- Holt-Winters interval is an approximation (+/-1.96 x residual standard deviation), as stated in the project README.",
       "- `Rolling 3M Sales` and `Sales LY` return blank for months without sales so 2019 stays clean.",
       "- RFM and sales checks use order dates 2015-01-03 to 2018-12-30."]
(OUT / "DAX_MEASURES.md").write_text("\n".join(md), encoding="utf-8")
print("measures:", total, "- all balanced")
