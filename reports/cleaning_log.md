# Cleaning and Transformation Log

- Rows before cleaning: **10,800**
- Rows after cleaning: **9,994**
- Rows removed: **806**

## Every fix with counts
| step | rule | rows_or_cells_affected | action | rows_after |
|---|---|---|---|---|
| 1 stray rows | all columns except Row ID/Order ID empty | 806 | dropped | 9994 |
| 2 duplicates | fully identical rows | 0 | kept first, dropped rest | 9994 |
| 2b duplicate Row ID | same Row ID twice | 0 | kept first | 9994 |
| 3 text consistency | strip/collapse spaces; Title Case for category-like columns | 32 | standardised | 9994 |
| 4 data types | Row ID/Sales/Quantity/Discount/Profit -> numeric; dates parsed from mixed formats | 0 | 0 values could not be parsed -> NaT (handled in step 5) | 9994 |
| 5a missing critical fields | any of 9 key fields missing | 0 | dropped | 9994 |
| 5b missing Discount | Discount empty | 0 | imputed with 0 (no discount) | 9994 |
| 5c missing Postal Code | Postal Code empty | 11 | filled with mode of same City+State; 11 still 'Unknown'; stored as 5-char text | 9994 |
| 5d other missing text | category-like columns empty | 0 | filled with 'Unknown' | 9994 |
| 6a invalid Quantity/Sales | Quantity <= 0 or Sales <= 0 | 0 | dropped | 9994 |
| 6b Discount range | Discount outside 0..1 | 0 | clipped to 0..1 | 9994 |
| 6c Ship before Order | Ship Date < Order Date | 0 | dropped | 9994 |
| 7a Customer ID -> name | one ID should have one name | 0 | checked (no change) | 9994 |
| 7b Product ID -> name | one ID should have one name | 32 | checked; star schema keeps first name per Product ID | 9994 |
| 7c Sales outliers | above Q3 + 1.5*IQR | 1167 | kept (genuine large orders); flagged only | 9994 |
| 8 derived columns | Order Year/Month/YearMonth, Ship Days, Profit Margin, Unit Price | 9994 | added | 9994 |

## Scaling demonstration (Ch6)
| column | min | max | mean | std |
|---|---|---|---|---|
| Sales | 0.444 | 22,638.48 | 229.858 | 623.2139 |
| Quantity | 1 | 14 | 3.7896 | 2.225 |
| Discount | 0 | 0.8 | 0.1562 | 0.2064 |
| Profit | -6,599.978 | 8,399.976 | 28.6569 | 234.2484 |
| Ship Days | 0 | 7 | 3.9585 | 1.7475 |

- Min-max formula (x-min)/(max-min) matches sklearn MinMaxScaler: **True**
- Z-score formula (x-mean)/std matches sklearn StandardScaler: **True**
- Skewness of Sales: 12.97 before, 0.28 after log1p transform

## Encoding demonstration (Ch6)
- One-hot (Segment, Ship Mode, Category, Region): 14 dummy columns
- Label encoding of Sub-Category: 17 classes -> 0..16
- Target encoding of State: smoothed mean Profit (smoothing m=20), computed with 5-fold out-of-fold to avoid leakage
- ML-ready demo file: `data/clean/superstore_ml_ready_demo.csv` (9,994 rows x 28 columns)
