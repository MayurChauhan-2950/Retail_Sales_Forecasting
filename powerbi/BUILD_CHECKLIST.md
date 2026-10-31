# BUILD_CHECKLIST (status: sections A to D done and checked; section E partly done: pages 1 and 2 built, pages 3 and 4 not built)

Tick a box only after you did it and the check passes. Expected values come from
`dax/DAX_MEASURES.md` (computed from the CSVs, not from Power BI).

## A. Setup
- [x] Install Power BI Desktop; open a blank report; save as `retail_sales_forecast.pbix` in `powerbi/`.
- [x] Run the Python pipeline first if `data/curated` or `data/forecast` is missing: `python scripts/run_all.py`.
- [x] Home > Transform data > New Source > Blank Query > Advanced Editor: paste `power_query/00_DataFolder_parameter.pq`, rename the query `DataFolder`, fix the path.

## B. Load tables (Power Query: one blank query each, named as in the file header)
- [x] 01_fact_sales.pq -> `fact_sales` (check 9,994 rows)
- [x] 02_dim_date.pq -> `dim_date` (1,826 rows). If it errors, use 02b_dim_date_generated.pq instead
- [x] 03_dim_product.pq -> `dim_product` (1,862)
- [x] 04_dim_customer.pq -> `dim_customer` (793)
- [x] 05_dim_geography.pq -> `dim_geography` (632)
- [x] 06_monthly_actual.pq -> `monthly_actual` (48)
- [x] 07_fact_forecast.pq -> `fact_forecast` (48 rows: 36 hold-out + 12 future)
- [x] 08_model_accuracy.pq -> `model_accuracy` (3), then 09_dim_model.pq -> `dim_model` (3)
- [x] No "Error" cells in any query; Close & Apply.

## C. Model (see `model/DATA_MODEL.md`)
- [x] Mark `dim_date` as date table on `Date`.
- [x] Create the relationships; make the `ship_date_key` one inactive.
- [x] Sort `MonthName` by `MonthNumber`, `YearMonth` by `YearMonthSort`, `discount_band` by `discount_band_sort`.
- [x] Set data categories on dim_geography (State, City, Country, Postal Code).
- [x] Hide key columns in report view.

## D. DAX
- [x] Create `_Measures` (Enter data), then the calculated tables `Top N` and `RFM` from `dax/measures.dax`.
- [x] Add the RFM one-to-one relationship (customer_key).
- [x] Add measures folder by folder; set Format and Display folder.
- [x] (cards checked: sales, profit, orders, customers) Verify against check values: Total Sales 2,297,200.86; Total Profit 286,397.02; Margin 12.47%; Orders 5,009; Customers 793.
- [ ] With Year 2018 selected: YoY % = +20.36%; Sales LY = 609,205.60.
- [x] Forecast page: Best Model (RMSE) = Holt-Winters (additive); Forecast Total 2019 = 910,035.16.
- [x] If any value differs, fix the measure or model before building visuals. Record the difference.

## E. Theme and pages
- [x] View > Themes > Browse for themes > `theme/retail_forecast_theme.json`.
- [ ] Build pages 1-4 following `layouts/WIREFRAMES.md`; rename the pages.
- [ ] Add conditional formatting (Format style: Field value) with the colour measures.
- [ ] Sync slicers; edit interactions; add navigation buttons; add alt text to visuals.

## F. Test and deliver
- [ ] Click every slicer; confirm cards, totals and the forecast chart respond sensibly.
- [ ] Check Performance analyzer shows no very slow visual.
- [ ] Take screenshots only from the real report; export PDF (File > Export > PDF).
- [ ] Update `README.md` here: change the status line only after the .pbix truly exists and passed section D.
- [ ] Update section 9 of `Individual_Project_Retail_Sales_Analytics.md` and the presentation with the real screenshots.


Notes: the project was opened from `pbip/` (not built by hand), the RFM relationship was left out of the project file and must be added in Model view if the RFM page is built, and the theme is applied manually. Pages 3 and 4 and the full set of measure checks are still open.
