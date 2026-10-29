# OLAP-style Examples on the Star Schema

Star schema: `fact_sales` (grain = one order line) with `dim_date`, `dim_product`, `dim_customer`, `dim_geography`.
Each query below was executed with SQL on the curated tables (SQLite); results are the real output.

## Integrity checks
| check | result |
|---|---|
| fact rows == clean rows | PASS |
| fact_sales.row_id unique | PASS |
| customer_key unique in dim | PASS |
| no orphan customer_key | PASS |
| product_key unique in dim | PASS |
| no orphan product_key | PASS |
| geography_key unique in dim | PASS |
| no orphan geography_key | PASS |
| date_key unique in dim | PASS |
| no orphan order_date_key | PASS |
| date_key unique in dim | PASS |
| no orphan ship_date_key | PASS |
| total sales preserved | PASS |

## Roll-up: sales by year (highest level)
Aggregate months up to years.

```sql
SELECT d.year, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY d.year
ORDER BY d.year
```

| year | sales | profit |
|---|---|---|
| 2015 | 484,247.5 | 49,543.97 |
| 2016 | 470,532.51 | 61,618.6 |
| 2017 | 609,205.6 | 81,795.17 |
| 2018 | 733,215.26 | 93,439.27 |

## Roll-up: year -> quarter
One level below year; summing the quarters gives the year totals above.

```sql
SELECT d.year, d.quarter, ROUND(SUM(f.sales),2) AS sales
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY d.year, d.quarter
ORDER BY d.year, d.quarter
```

| year | quarter | sales |
|---|---|---|
| 2015 | 1 | 74,447.8 |
| 2015 | 2 | 86,538.76 |
| 2015 | 3 | 143,633.21 |
| 2015 | 4 | 179,627.73 |
| 2016 | 1 | 68,851.74 |
| 2016 | 2 | 89,124.19 |
| 2016 | 3 | 130,259.58 |
| 2016 | 4 | 182,297.01 |
| 2017 | 1 | 93,237.18 |
| 2017 | 2 | 136,082.3 |
| 2017 | 3 | 143,787.36 |
| 2017 | 4 | 236,098.75 |
| 2018 | 1 | 123,144.86 |
| 2018 | 2 | 133,764.37 |
| 2018 | 3 | 196,251.96 |
| 2018 | 4 | 280,054.07 |

## Drill-down: 2017 sales by month
Go from year to month detail.

```sql
SELECT d.month, d.month_name, ROUND(SUM(f.sales),2) AS sales
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE d.year = 2017
GROUP BY d.month, d.month_name
ORDER BY d.month
```

| month | month_name | sales |
|---|---|---|
| 1 | January | 18,542.49 |
| 2 | February | 22,978.82 |
| 3 | March | 51,715.88 |
| 4 | April | 38,750.04 |
| 5 | May | 56,987.73 |
| 6 | June | 40,344.53 |
| 7 | July | 39,261.96 |
| 8 | August | 31,115.37 |
| 9 | September | 73,410.02 |
| 10 | October | 59,687.75 |
| 11 | November | 79,411.97 |
| 12 | December | 96,999.04 |

## Slice: Region = 'West' (one dimension fixed)
Category totals for the West region only.

```sql
SELECT p.category, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE g.region = 'West'
GROUP BY p.category
ORDER BY sales DESC
```

| Category | sales | profit |
|---|---|---|
| Furniture | 252,612.74 | 11,504.95 |
| Technology | 251,991.83 | 44,303.65 |
| Office Supplies | 220,853.25 | 52,609.85 |

## Dice: 2016-2017, Technology/Furniture, East/West
Several dimensions restricted at once.

```sql
SELECT d.year, g.region, p.category, ROUND(SUM(f.sales),2) AS sales, SUM(f.quantity) AS units
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key
JOIN dim_customer c ON f.customer_key = c.customer_key
WHERE d.year IN (2016,2017) AND p.category IN ('Technology','Furniture') AND g.region IN ('East','West')
GROUP BY d.year, g.region, p.category
ORDER BY d.year, g.region, p.category
```

| year | Region | Category | sales | units |
|---|---|---|---|---|
| 2016 | East | Furniture | 53,817.43 | 475 |
| 2016 | East | Technology | 59,859.38 | 455 |
| 2016 | West | Furniture | 57,004.94 | 597 |
| 2016 | West | Technology | 45,097.77 | 429 |
| 2017 | East | Furniture | 46,387.17 | 592 |
| 2017 | East | Technology | 72,497.44 | 458 |
| 2017 | West | Furniture | 73,819.64 | 696 |
| 2017 | West | Technology | 65,981.18 | 505 |

## Cross-tab (pivot): Segment x Category sales
Two dimensions against a measure.

```sql
SELECT c.segment, ROUND(SUM(CASE WHEN p.category='Furniture' THEN f.sales END),2) AS furniture, ROUND(SUM(CASE WHEN p.category='Office Supplies' THEN f.sales END),2) AS office_supplies, ROUND(SUM(CASE WHEN p.category='Technology' THEN f.sales END),2) AS technology
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY c.segment
ORDER BY c.segment
```

| Segment | furniture | office_supplies | technology |
|---|---|---|---|
| Consumer | 391,049.31 | 363,952.14 | 406,399.9 |
| Corporate | 229,019.79 | 230,676.46 | 246,450.12 |
| Home Office | 121,930.7 | 124,418.43 | 183,304.02 |

## Top 5 states by profit
Ranking over the geography dimension.

```sql
SELECT g.state, ROUND(SUM(f.sales),2) AS sales, ROUND(SUM(f.profit),2) AS profit
FROM fact_sales f
JOIN dim_date d ON f.order_date_key = d.date_key
JOIN dim_product p ON f.product_key = p.product_key
JOIN dim_geography g ON f.geography_key = g.geography_key
JOIN dim_customer c ON f.customer_key = c.customer_key
GROUP BY g.state
ORDER BY profit DESC LIMIT 5
```

| State | sales | profit |
|---|---|---|
| California | 457,687.63 | 76,381.39 |
| New York | 310,876.27 | 74,038.55 |
| Washington | 138,641.27 | 33,402.65 |
| Michigan | 76,269.61 | 24,463.19 |
| Virginia | 70,636.72 | 18,597.95 |
