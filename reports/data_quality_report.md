# Data Quality Report (raw data)

Source file: `data/raw/superstore.csv` - 10,800 rows x 21 columns

## 1. Data types and missing values
| column | dtype | missing | missing_% | unique |
|---|---|---|---|---|
| Row ID | str | 0 | 0 | 10001 |
| Order ID | str | 0 | 0 | 5015 |
| Order Date | str | 806 | 7.46 | 1236 |
| Ship Date | str | 806 | 7.46 | 1334 |
| Ship Mode | str | 806 | 7.46 | 4 |
| Customer ID | str | 806 | 7.46 | 793 |
| Customer Name | str | 806 | 7.46 | 793 |
| Segment | str | 806 | 7.46 | 3 |
| Country | str | 806 | 7.46 | 1 |
| City | str | 806 | 7.46 | 531 |
| State | str | 806 | 7.46 | 49 |
| Postal Code | float64 | 817 | 7.56 | 630 |
| Region | str | 806 | 7.46 | 4 |
| Product ID | str | 806 | 7.46 | 1862 |
| Category | str | 806 | 7.46 | 3 |
| Sub-Category | str | 806 | 7.46 | 17 |
| Product Name | str | 806 | 7.46 | 1850 |
| Sales | float64 | 806 | 7.46 | 5825 |
| Quantity | float64 | 806 | 7.46 | 14 |
| Discount | float64 | 806 | 7.46 | 12 |
| Profit | float64 | 806 | 7.46 | 7287 |

## 2. Duplicates and stray rows
- Completely empty business rows (stray rows, no Order Date/Sales/...): **806**
- Non-numeric `Row ID` values: **806**
- Fully duplicated rows (all columns identical): **504**  (among non-empty rows: **0**)
- Duplicated `Row ID` values: **799**

## 3. Text consistency (spaces / casing)
| column | values_with_extra_spaces | distinct_raw | distinct_normalised | casing_variants |
|---|---|---|---|---|
| Ship Mode | 0 | 4 | 4 | 0 |
| Segment | 0 | 3 | 3 | 0 |
| Country | 0 | 1 | 1 | 0 |
| City | 0 | 531 | 531 | 0 |
| State | 0 | 49 | 49 | 0 |
| Region | 0 | 4 | 4 | 0 |
| Category | 0 | 3 | 3 | 0 |
| Sub-Category | 0 | 17 | 17 | 0 |

## 4. Dates
- Order Date range: 2015-01-03 to 2018-12-30
- Unparseable Order Dates (after trying several formats): **0**
- Ship Date before Order Date: **0**
- Date string patterns seen (9 = a digit):

  - `9/99/9999`: 4,421
  - `99/99/9999`: 2,535
  - `9/9/9999`: 1,875
  - `99/9/9999`: 1,163

## 5. Invalid values (business rules)
- Quantity <= 0: **0**
- Sales <= 0: **0**
- Discount outside 0..1: **0**
- Negative Profit rows (valid, loss-making orders): 1,871

## 6. Outliers (IQR rule, flagged not removed)
| column | Q1 | Q3 | lower_fence | upper_fence | outliers | skew |
|---|---|---|---|---|---|---|
| Sales | 17.28 | 209.94 | -271.71 | 498.93 | 1167 | 12.9728 |
| Quantity | 2 | 5 | -2.5 | 9.5 | 170 | 1.2785 |
| Discount | 0 | 0.2 | -0.3 | 0.5 | 856 | 1.6843 |
| Profit | 1.7288 | 29.364 | -39.7241 | 70.8169 | 1881 | 7.5614 |

## 7. Key consistency
- Customer IDs with more than one name: **0**
- Product IDs with more than one product name: **32** (handled in the star schema)
- Postal Code stored as `float64` (should be text; leading zeros are lost)
