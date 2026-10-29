# Wireframes (4 pages) - plans only, not screenshots

Canvas 1280 x 720 (16:9). Theme: `theme/retail_forecast_theme.json`. Measure names are from `dax/measures.dax`.
The dashboard is NOT built yet; these are layout sketches.

## Page 1 - Executive Overview
```
+--------------------------------------------------------------------------+
| Retail Sales Dashboard - Overview        [Year v] [Region v] [Category v] |
+----------+----------+----------+----------+----------+-------------------+
| Total    | Total    | Profit   | Orders   | Customers| Avg Order Value   |
| Sales    | Profit   | Margin % |          |          |                   |
| YoY %    | YoY %    |          |          |          |                   |
+----------+----------+----------+----------+----------+-------------------+
| Monthly Sales and Profit (line)  | Sales and margin by Category (bar)    |
| + Sales LY dashed                |                                       |
|                                  +---------------------------------------+
|                                  | Sales by Region (bar / donut)         |
+----------------------------------+---------------------------------------+
| Data Source Note (text)                                                  |
+--------------------------------------------------------------------------+
```

## Page 2 - Products, Regions and Discounts
```
+--------------------------------------------------------------------------+
| Products, Regions and Discounts        [Year v] [Segment v] [Top N v]     |
+---------------------------+----------------------------------------------+
| Top N products by sales   | Sub-Category profit (bar, red when negative) |
| (bar, Top N Flag filter)  |                                              |
+---------------------------+----------------------+-----------------------+
| Map: Sales by State       | Profit margin by discount band (column)      |
| (filled map, dim_geography| x-axis: fact_sales[discount_band]            |
|  State)                   | cards: Loss Lines %, Loss Amount             |
+---------------------------+----------------------------------------------+
```

## Page 3 - Customers (RFM) and Shipping
```
+--------------------------------------------------------------------------+
| Customers                                  [Segment v] [Year v]           |
+--------------+--------------+--------------+-----------------------------+
| Customers    | Sales per    | Avg Days to  | Avg Frequency / Recency     |
|              | Customer     | Ship         |                             |
+--------------+--------------+--------------+-----------------------------+
| RFM segments: customers (bar)   | Segment x Category matrix (sales)      |
| RFMSegment sorted by SegmentSort| conditional formatting on margin       |
+---------------------------------+----------------------------------------+
| Table: customer, Sales, Profit, Recency, Frequency (top 20)              |
+--------------------------------------------------------------------------+
```

## Page 4 - Forecasting Arena (main feature)
```
+--------------------------------------------------------------------------+
| Forecasting Arena: Holt-Winters vs ARIMA vs SARIMA   [Model slicer]       |
+--------------------------------------------------------------------------+
| Best Model Callout (text card, measure [Best Model Callout])             |
+-------------------------------------------+------------------------------+
| Actual vs Forecast, Jan 2015 - Dec 2019   | Accuracy table               |
| line: Actual Sales (Series)               | model | MAE | RMSE | MAPE %  |
|       Forecast (All Models) by model      | row colour: Best Model Row   |
|       95% band for 2019 (Lower/Upper 95)  |                              |
+-------------------------------------------+------------------------------+
| 2018 hold-out: Abs Forecast Error by month | Cards: Forecast Total 2019, |
| (columns, per model)                       | Forecast Growth vs 2018     |
+-------------------------------------------+------------------------------+
| Note: 48 months only; only the best model has 2019 values.               |
+--------------------------------------------------------------------------+
```

Interactions: Edit interactions so the Model slicer does not filter Page 1-3 visuals (it only relates to the
forecast tables). Sync Year/Region slicers across pages 1-3 through View > Sync slicers. Add page navigation buttons.
Keep to 3 to 4 colours; green/amber/red come from the KPI colour measures.
