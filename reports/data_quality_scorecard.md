# Data Quality Scorecard (script 11)

Each rule is a pass/fail test per row (or per key). Score = share passing. Computed on the cleaned data unless marked RAW.

| dimension | rule | passing | checked | score_% | note |
|---|---|---|---|---|---|
| Completeness | no nulls in 11 key business columns (clean) | 9994 | 9994 | 100 |  |
| Completeness | Postal Code present (clean, 'Unknown' counts as filled) | 9994 | 9994 | 100 | 11 Burlington VT rows set to 'Unknown' |
| Completeness | RAW: non-empty business rows | 9994 | 10800 | 92.54 | 806 stray rows in the raw copy |
| Uniqueness | Row ID unique | 9994 | 9994 | 100 |  |
| Uniqueness | no fully duplicated rows | 9994 | 9994 | 100 |  |
| Validity | Sales > 0 | 9994 | 9994 | 100 |  |
| Validity | Quantity >= 1 | 9994 | 9994 | 100 |  |
| Validity | Discount within [0, 1] | 9994 | 9994 | 100 |  |
| Validity | Ship Date >= Order Date | 9994 | 9994 | 100 |  |
| Validity | Ship Days <= 14 | 9994 | 9994 | 100 |  |
| Consistency | Profit margin = Profit/Sales within 1e-3 | 9994 | 9994 | 100 |  |
| Consistency | Product ID maps to exactly one Product Name | 1830 | 1862 | 98.28 | 32 Product IDs carry several names (dim_product keeps first) |
| Consistency | Customer ID maps to exactly one name | 793 | 793 | 100 |  |
| Consistency | Customer ID maps to exactly one Segment | 793 | 793 | 100 |  |
| Consistency | State maps to exactly one Region | 49 | 49 | 100 |  |
| Timeliness | Order Date within 2015-01-01..2018-12-31 | 9994 | 9994 | 100 | historic sample data, not a live feed |
| Referential integrity | fact FKs all present in dimensions | 49970 | 49970 | 100 |  |

## Score per dimension
| dimension | mean_score_% |
|---|---|
| Completeness | 97.51 |
| Consistency | 99.66 |
| Referential integrity | 100 |
| Timeliness | 100 |
| Uniqueness | 100 |
| Validity | 100 |

**Unweighted mean of all rule scores: 99.46%.** The RAW completeness rule shows what cleaning fixed.
