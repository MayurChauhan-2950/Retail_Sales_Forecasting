# Power BI

Open `pbip/retail_sales_forecast.pbip` in Power BI Desktop, then click Home > Refresh.
The data path is set to `C:\Users\devch\Downloads\DSC\Projects\IP_Retail_Sales_Analytics\data`; change it under Home > Transform data > Edit parameters (DataFolder) if the project is elsewhere. `pbip/OPEN_ME.md` has the details.

Two report pages are built:

- **Overview:** KPI cards (sales, profit, customers, orders), monthly sales, sales by category, Year and Region slicers.
- **Forecasting Arena:** model slicer, best model, 2019 forecast total and growth, 2018 hold-out actual vs forecast, 2019 forecast with 95% interval, accuracy table.

Screenshots: `screenshots/page1_overview.png`, `screenshots/page2_forecasting_arena.png`.
The 84 DAX measures are in `dax/measures.dax`.

Checked against the pandas results: total sales 2,297,200.86, profit 286,397.02, 793 customers, 5,009 orders, 2019 forecast about 910K (+24.1%), hold-out MAE 10,896.63 / RMSE 14,117.72 / MAPE 18.51. Only the measures used on the two pages were exercised. Pages 3 and 4 (customers/RFM, products and discounts) are not built.
