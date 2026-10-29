# Additional OLAP Query Examples (script 11)

Executed as SQL on SQLite over the curated tables; results are real output.

## Roll-up with subtotals: year x category (UNION of levels)
Detail rows plus year subtotals, emulating ROLLUP (SQLite has no ROLLUP).

```sql
SELECT d.year, p.[Category], ROUND(SUM(f.sales),2) AS sales FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key GROUP BY d.year, p.[Category] UNION ALL SELECT d.year, 'ALL CATEGORIES', ROUND(SUM(f.sales),2) FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key GROUP BY d.year ORDER BY 1, 2
```

| year | Category | sales |
|---|---|---|
| 2015 | ALL CATEGORIES | 484,247.5 |
| 2015 | Furniture | 157,192.85 |
| 2015 | Office Supplies | 151,776.41 |
| 2015 | Technology | 175,278.23 |
| 2016 | ALL CATEGORIES | 470,532.51 |
| 2016 | Furniture | 170,518.24 |
| 2016 | Office Supplies | 137,233.46 |
| 2016 | Technology | 162,780.81 |
| 2017 | ALL CATEGORIES | 609,205.6 |
| 2017 | Furniture | 198,901.44 |
| 2017 | Office Supplies | 183,939.98 |
| 2017 | Technology | 226,364.18 |
| 2018 | ALL CATEGORIES | 733,215.26 |
| 2018 | Furniture | 215,387.27 |
| 2018 | Office Supplies | 246,097.18 |
| 2018 | Technology | 271,730.81 |

## Roll-up: region -> state (top 8 states in the West)
Drill from region to the states inside it.

```sql
SELECT g.[Region], g.[State], ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key WHERE g.[Region]='West' GROUP BY g.[Region], g.[State] ORDER BY sales DESC LIMIT 8
```

| Region | State | sales | profit |
|---|---|---|---|
| West | California | 457,687.63 | 76,381.39 |
| West | Washington | 138,641.27 | 33,402.65 |
| West | Arizona | 35,282 | -3,427.92 |
| West | Colorado | 32,108.12 | -6,527.86 |
| West | Oregon | 17,431.15 | -1,190.47 |
| West | Nevada | 16,729.1 | 3,316.77 |
| West | Utah | 11,220.06 | 2,546.53 |
| West | Montana | 5,589.35 | 1,833.33 |

## Drill-down: category -> sub-category (Technology)
From a category to its sub-categories.

```sql
SELECT p.[Category], p.[Sub-Category], ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key WHERE p.[Category]='Technology' GROUP BY p.[Category], p.[Sub-Category] ORDER BY sales DESC
```

| Category | Sub-Category | sales | profit |
|---|---|---|---|
| Technology | Phones | 330,007.05 | 44,515.73 |
| Technology | Machines | 189,238.63 | 3,384.76 |
| Technology | Accessories | 167,380.32 | 41,936.64 |
| Technology | Copiers | 149,528.03 | 55,617.82 |

## Drill-down: Q4 2018 by month and category
Year -> quarter -> month detail for one quarter.

```sql
SELECT d.year_month, p.[Category], ROUND(SUM(f.sales),2) AS sales FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key WHERE d.year=2018 AND d.quarter=4 GROUP BY d.year_month, p.[Category] ORDER BY d.year_month, p.[Category]
```

| year_month | Category | sales |
|---|---|---|
| 2018-10 | Furniture | 21,884.07 |
| 2018-10 | Office Supplies | 23,037.19 |
| 2018-10 | Technology | 32,855.66 |
| 2018-11 | Furniture | 37,056.72 |
| 2018-11 | Office Supplies | 31,472.34 |
| 2018-11 | Technology | 49,918.77 |
| 2018-12 | Furniture | 31,407.47 |
| 2018-12 | Office Supplies | 30,436.94 |
| 2018-12 | Technology | 21,984.91 |

## Slice: Consumer segment, all years
Fix Segment = Consumer; sales and profit by year.

```sql
SELECT d.year, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key WHERE c.[Segment]='Consumer' GROUP BY d.year ORDER BY d.year
```

| year | sales | profit |
|---|---|---|
| 2015 | 266,096.81 | 24,319.85 |
| 2016 | 266,535.93 | 28,460.17 |
| 2017 | 296,863.9 | 35,770.95 |
| 2018 | 331,904.7 | 45,568.24 |

## Slice: discount above 30%
Loss-making rows by sub-category when heavily discounted.

```sql
SELECT p.[Sub-Category], COUNT(*) AS lines, ROUND(SUM(f.profit),2) AS profit FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key WHERE f.discount > 0.3 GROUP BY p.[Sub-Category] ORDER BY profit LIMIT 6
```

| Sub-Category | lines | profit |
|---|---|---|
| Binders | 613 | -38,510.5 |
| Machines | 48 | -29,881.39 |
| Tables | 122 | -27,295.9 |
| Bookcases | 60 | -10,541.89 |
| Appliances | 67 | -8,629.64 |
| Phones | 109 | -6,385.79 |

## Dice: 2017-2018, Central/South, Furniture/Technology, Corporate
Restrict four dimensions at once.

```sql
SELECT d.year, g.[Region], p.[Category], ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key WHERE d.year IN (2017,2018) AND g.[Region] IN ('Central','South') AND p.[Category] IN ('Furniture','Technology') AND c.[Segment]='Corporate' GROUP BY d.year, g.[Region], p.[Category] ORDER BY 1,2,3
```

| year | Region | Category | sales | profit |
|---|---|---|---|---|
| 2017 | Central | Furniture | 26,246.12 | 2,184.41 |
| 2017 | Central | Technology | 24,642.29 | 9,624.48 |
| 2017 | South | Furniture | 7,679.21 | -131.11 |
| 2017 | South | Technology | 10,198.66 | 2,982.34 |
| 2018 | Central | Furniture | 13,940.12 | 518.2 |
| 2018 | Central | Technology | 12,788.37 | 2,168.51 |
| 2018 | South | Furniture | 7,771.23 | -914.08 |
| 2018 | South | Technology | 20,369.45 | -847.02 |

## Year-over-year growth by category
Window function LAG over yearly totals.

```sql
SELECT [Category] AS category, year, sales, ROUND((sales - LAG(sales) OVER (PARTITION BY [Category] ORDER BY year)) / LAG(sales) OVER (PARTITION BY [Category] ORDER BY year) * 100, 2) AS yoy_pct FROM (SELECT p.[Category], d.year, SUM(f.sales) AS sales FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key GROUP BY p.[Category], d.year) ORDER BY [Category], year
```

| category | year | sales | yoy_pct |
|---|---|---|---|
| Furniture | 2015 | 157,192.8531 | nan |
| Furniture | 2016 | 170,518.237 | 8.48 |
| Furniture | 2017 | 198,901.436 | 16.65 |
| Furniture | 2018 | 215,387.2692 | 8.29 |
| Office Supplies | 2015 | 151,776.412 | nan |
| Office Supplies | 2016 | 137,233.463 | -9.58 |
| Office Supplies | 2017 | 183,939.982 | 34.03 |
| Office Supplies | 2018 | 246,097.175 | 33.79 |
| Technology | 2015 | 175,278.233 | nan |
| Technology | 2016 | 162,780.809 | -7.13 |
| Technology | 2017 | 226,364.18 | 39.06 |
| Technology | 2018 | 271,730.811 | 20.04 |

## Running total of monthly sales 2018
Window function SUM OVER ordered months.

```sql
SELECT year_month, ROUND(sales,2) AS sales, ROUND(SUM(sales) OVER (ORDER BY year_month),2) AS running_sales FROM (SELECT d.year_month, SUM(f.sales) AS sales FROM fact_sales f JOIN dim_date d ON f.order_date_key = d.date_key JOIN dim_product p ON f.product_key = p.product_key JOIN dim_geography g ON f.geography_key = g.geography_key JOIN dim_customer c ON f.customer_key = c.customer_key WHERE d.year=2018 GROUP BY d.year_month) ORDER BY year_month
```

| year_month | sales | running_sales |
|---|---|---|
| 2018-01 | 43,971.37 | 43,971.37 |
| 2018-02 | 20,301.13 | 64,272.51 |
| 2018-03 | 58,872.35 | 123,144.86 |
| 2018-04 | 36,521.54 | 159,666.4 |
| 2018-05 | 44,261.11 | 203,927.51 |
| 2018-06 | 52,981.73 | 256,909.23 |
| 2018-07 | 45,264.42 | 302,173.65 |
| 2018-08 | 63,120.89 | 365,294.54 |
| 2018-09 | 87,866.65 | 453,161.19 |
| 2018-10 | 77,776.92 | 530,938.11 |
| 2018-11 | 118,447.83 | 649,385.94 |
| 2018-12 | 83,829.32 | 733,215.26 |

## Aggregate table query (what Power BI reads)
Same answer as the fact join, from the pre-aggregated table.

```sql
SELECT year, Category, ROUND(SUM(sales),2) AS sales, ROUND(SUM(profit),2) AS profit FROM agg_monthly_category_region GROUP BY year, Category ORDER BY year, Category
```

| year | Category | sales | profit |
|---|---|---|---|
| 2015 | Furniture | 157,192.85 | 5,457.73 |
| 2015 | Office Supplies | 151,776.41 | 22,593.42 |
| 2015 | Technology | 175,278.23 | 21,492.83 |
| 2016 | Furniture | 170,518.24 | 3,015.2 |
| 2016 | Office Supplies | 137,233.46 | 25,099.53 |
| 2016 | Technology | 162,780.81 | 33,503.87 |
| 2017 | Furniture | 198,901.44 | 6,959.95 |
| 2017 | Office Supplies | 183,939.98 | 35,061.23 |
| 2017 | Technology | 226,364.18 | 39,773.99 |
| 2018 | Furniture | 215,387.27 | 3,018.39 |
| 2018 | Office Supplies | 246,097.18 | 39,736.62 |
| 2018 | Technology | 271,730.81 | 50,684.26 |
