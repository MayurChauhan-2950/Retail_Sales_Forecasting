# Results Summary

All numbers below were produced by the scripts in `scripts/` (07-11) and read from the CSV/markdown outputs listed. Data: real Sample Superstore, 9,994 order lines, 2015-01-03 to 2018-12-30, total sales 2,297,201 and profit 286,397 (overall margin 12.5%). Yearly sales: 2015 484,247; 2016 470,532; 2017 609,206; 2018 733,215.

## 1. Forecast model comparison (script 07; `data/forecast/cv_summary.csv`, `reports/model_accuracy.md`)
Monthly total sales, 48 points. Rolling-origin (expanding window) CV: minimum train 24 months, horizon 6, step 3 = 7 folds.

| model | CV MAE | CV RMSE | CV MAPE % | 2018 hold-out MAE | hold-out MAPE % |
|---|---|---|---|---|---|
| Holt-Winters additive (damped) | 10,981 | 13,445 | 21.7 | 10,897 | 18.5 |
| Seasonal naive (baseline) | 13,739 | 16,542 | 25.0 | 15,468 | 24.5 |
| SARIMA(1,1,1)(0,1,1,12) | 14,513 | 16,199 | 36.6 | 15,105 | 34.0 |
| ARIMA(1,1,1) | 22,601 | 27,047 | 49.1 | 23,451 | 54.1 |

Chart: `figures/cv_mae_by_model.png` (also `cv_fold_mae.png`, `cv_mase_by_model.png`). Eleven models were tested; the full table is in `model_accuracy.md`.
- Damped additive Holt-Winters has the lowest mean CV MAE and the lowest 2018 hold-out MAE. It beat seasonal naive in 7 of 7 folds (Wilcoxon p = 0.016, the smallest value possible with 7 folds).
- SARIMA did not beat the seasonal-naive baseline on average (MAE 14,513 vs 13,739; mean fold gap 774, SARIMA better in 5 of 7 folds but much worse in the others). Its error varies a lot across folds (MAE SD 6,974 vs 3,265 for seasonal naive). Plain ARIMA, with no seasonal term, is far worse (MAPE 49%).
- Damped Holt-Winters vs SARIMA: mean fold MAE gap 3,532, Holt-Winters better in 4 of 7 folds, Wilcoxon p = 0.375, so the two are not statistically distinguishable here.

## 2. Residual diagnostics (script 08; `data/forecast/residual_tests.csv`, `figures/diag_residuals.png`, `figures/diag_acf_pacf.png`)
Best model, damped additive Holt-Winters, 48 one-step residuals: Ljung-Box p = 0.329 (lag 6) and 0.165 (lag 12), so no significant leftover autocorrelation; Jarque-Bera p = 0.577 and Shapiro p = 0.181, so no evidence against normality; residual mean 594, SD 8,984. For comparison, SARIMA residuals (35) have Ljung-Box lag 12 p = 0.010, i.e. leftover autocorrelation. STL seasonal strength 0.86, trend strength 0.53. ADF and KPSS disagree on the level series (ADF p = 0.0002, KPSS p = 0.019); one regular difference satisfies both.
The 2019 forecast (bootstrap 80/95% bands in `data/forecast/forecast_total.csv`, `figures/fan_chart_total.png`) runs from 41,476 (Feb) to 115,687 (Nov) and 116,031 (Dec); the December 95% band is 56,622 to 189,080.

## 3. Category, region and segment forecasts (script 09; `data/forecast/segment_best_models.csv`, `forecast_all_series.csv`)
Best model per series by CV MAE (it differs by series):

| series | best model | CV MAE | 2018 hold-out MAPE % |
|---|---|---|---|
| Category: Furniture | Seasonal naive | 3,344 | 24.0 |
| Category: Office Supplies | HW additive damped | 5,182 | 24.1 |
| Category: Technology | SARIMA(1,1,1)(0,1,1,12) | 7,595 | 46.8 |
| Region: Central | Seasonal naive | 4,836 | 41.4 |
| Region: East | HW additive damped | 6,055 | 39.7 |
| Region: South | HW additive damped | 4,462 | 59.7 |
| Region: West | HW additive damped | 4,130 | 15.4 |
| Segment: Consumer | HW multiplicative | 6,770 | 32.6 |
| Segment: Corporate | HW additive damped | 5,558 | 49.7 |
| Segment: Home Office | Seasonal naive | 4,667 | 41.4 |

Where seasonal naive wins, the 2019 forecast is a repeat of 2018 (forecast total equals the 2018 total in the CSV). Hold-out errors of 15-60% MAPE mean these are directional, not precise.

## 4. Business analytics (script 10; `data/analytics/`, `figures/ba_*.png`)
- **Pareto 80/20 (products):** 414 of 1,862 products (22.2%) give 80.0% of sales and 70.6% of profit (class A); 959 products (51.5%) are class C with 5.0% of sales. Customers are less concentrated: 396 of 793 (49.9%) give 80.1% of sales.
- **Discount vs profit:** margin is 29.5% with no discount (4,798 lines), 11.6% at 10-20%, then negative from 20%: -10.1% (20-30%), -19.4% (30-40%), -35.7% (40-50%), -119.2% above 50% (856 lines, all loss-making). Lines with discount above 20% lose 135,376 in total (1,393 lines). Spearman correlation of discount and profit per line is -0.54. This is an association: heavily discounted lines cluster in certain sub-categories, so product mix is a confounder.
- **Sub-categories:** Copiers, Phones and Accessories earn the most profit (55,618; 44,516; 41,937). Tables (-17,725), Bookcases (-3,473) and Supplies (-1,189) lose money. Machines have a 1.8% margin on 189,239 of sales (average discount 31%).
- **RFM (k-means, k=4):** Cooling high-value 244 customers (30.8%, 51.5% of sales, average recency 98 days); Active mid-value 198 (23.4% of sales, 20 days); Lapsed mid-value 260 (23.2%, 229 days); Lapsed low-value 91 (1.9%, 328 days). The segment names are labels assigned from recency and spend thresholds in the script, not output by k-means.
- **Seasonality index (100 = average month):** November 185, December 173, September 164; February 30, January 48.

## 5. Data engineering (script 11)
`reports/data_dictionary.md` and `data/data_dictionary.csv` (every column: type, meaning, nullable, distinct count, example), `reports/data_quality_scorecard.md` (overall 99.46%), `reports/lineage_and_reconciliation.md` (9 of 9 reconciliation checks pass), `reports/olap_extra_examples.md`.

## Caveats (read before quoting any number)
1. **Small sample.** 48 monthly points. With D=1 and a 24-month minimum window, SARIMA has about 12 usable points for up to 5 parameters. Its weak result reflects this and does not show SARIMA is a bad method in general.
2. **Folds overlap** (6-month horizon, 3-month step), so the 7 folds are not independent; p-values are indicative only.
3. **Model choice is tentative.** Damped Holt-Winters leads ETS (AICc), undamped Holt-Winters and SARIMA by amounts within fold-to-fold variation (SARIMA gap p = 0.375). It is clearly better than naive, SES and ARIMA(1,1,1).
4. **Growth assumption.** Sales were flat in 2015-2016 and grew in 2017-2018; any forecast assumes the recent growth and seasonal pattern continue.
5. **Prediction intervals** are bootstrap or model-based approximations and will be too narrow if the model is wrong. The 2019 values are forecasts, not expected actuals.
6. **Sub-series** (category, region, segment) are noisier, with some hold-out MAPE of 40-60%.
7. **Association, not cause.** The discount-profit relationship is observational. RFM results depend on the snapshot date and on k (silhouette is highest at k=2, 0.350, vs 0.254 at k=4; k=4 was chosen for interpretability).
8. **Public sample data**, not real company records; 806 stray rows were removed in cleaning.
