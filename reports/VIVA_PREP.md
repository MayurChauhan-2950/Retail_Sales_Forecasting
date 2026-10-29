# Viva Preparation: Retail Sales Forecasting Project

Short, honest answers grounded in the project outputs. Numbers come from the reports and data files. Remember: the Power BI .pbix is NOT built yet; say so plainly if asked.

## A. Project and data

1. **What is your project about?** I cleaned the Superstore retail data, built a star schema, analysed sales and profit, and compared Holt-Winters, ARIMA and SARIMA for forecasting monthly sales. A Power BI dashboard is planned but not built yet.
2. **Is the data real?** It is the real public Sample Superstore dataset (9,994 order lines, 2015-2018), not a real company's records. The copy I used had 806 extra empty rows appended, which I removed.
3. **What did cleaning find?** 806 stray rows (10,800 to 9,994), 11 missing Postal Codes (Burlington, VT), 32 text values standardised, 32 Product IDs with several names, 0 duplicates, 0 invalid values. Many checks gave zero because the real data is already tidy; I report that honestly.
4. **Why keep the 1,167 sales outliers?** They are genuine large orders (above Q3 + 1.5 IQR), not errors. Removing them would distort totals; they are flagged only.
5. **Why is Postal Code stored as text?** ZIP codes are identifiers, not numbers; leading zeros must be kept.
6. **What are the headline totals?** Sales 2,297,201, profit 286,397, margin 12.5%. Yearly sales 484,247; 470,532; 609,206; 733,215.

## B. Chapter 6: transformation and integrity

7. **Min-max vs standardisation?** Min-max rescales to 0-1 using (x - min)/(max - min); z-score uses (x - mean)/std. Both matched scikit-learn in my check. Min-max is sensitive to outliers (Sales ranges from 0.444 to 22,638).
8. **Why a log transform on Sales?** Sales are heavily right-skewed: skewness 12.97 before, 0.28 after log1p.
9. **Which encodings did you use?** One-hot for nominal columns (14 dummies), label encoding for Sub-Category (17 classes; only appropriate where an arbitrary order is harmless, e.g. tree models), and smoothed target encoding for State, computed out-of-fold (5 folds) to avoid target leakage.
10. **How did you measure data quality?** A scorecard of 17 rules over six dimensions; mean 99.46%. The weakest are raw completeness (92.54%, the stray rows) and Product ID to name consistency (98.28%).

## C. Chapter 7: optimisation

11. **What is a cost function?** A number measuring model error; I used the mean squared error of a linear trend on the 48 monthly totals.
12. **Explain gradient descent.** Start with parameters at zero, compute the gradient of the MSE, step opposite to it scaled by a learning rate, repeat. I wrote it from scratch (200 epochs, rate 0.1, on standardised data).
13. **How do you know it worked?** It matched the closed-form normal equation and numpy polyfit exactly: slope 902.01 and intercept 26,661.17, same MSE. Loss was within 1e-6 of the optimum after about 28 epochs.
14. **What did the learning-rate experiment show?** 0.001 converged slowly (loss 0.862), 0.01 to 0.5 converged (0.7488), 1.05 diverged (loss about 7.5e15).
15. **Why standardise before gradient descent?** It puts both variables on similar scales so one learning rate works well and convergence is fast.
16. **The trend R-squared is only 0.251. Is the fit bad?** A straight line explains only a quarter of the variance because seasonality dominates. That is why seasonal models are needed.

## D. Chapter 8: data engineering

17. **What is the ETL flow?** Raw zone (untouched CSV), staging (as-is parquet with load timestamp), clean (9,994 rows), curated (star schema). Reconciled at each step.
18. **What is a star schema?** One fact table (fact_sales, grain = one order line) with surrogate-keyed dimensions: date (1,826), product (1,862), customer (793), geography (632). Simple joins, fast aggregation, good for Power BI.
19. **Why surrogate keys?** They are stable, small integers independent of source codes, and let dimensions change without breaking the fact table.
20. **What is a degenerate dimension?** order_id lives on the fact table because it has no attributes of its own.
21. **Additive vs non-additive?** Sales, quantity and profit can be summed; discount is a fraction and must be averaged.
22. **Star vs snowflake?** Snowflake normalises dimensions into sub-tables. I used a star for simplicity and speed; the dimensions are small.
23. **Which OLAP operations did you show?** Roll-up (month to quarter to year), drill-down (year to month), slice (fix one dimension, e.g. Region = West), dice (several), pivot, plus subtotals, year-over-year and running total, as SQL on SQLite.
24. **How do you prove the load is correct?** 9 of 9 reconciliation checks pass: row counts (10,800 - 806 = 9,994 = fact rows), sums of Sales, Profit and Quantity equal between clean and fact, distinct customers and products equal dimension rows, and no orphan foreign keys.

## E. Chapter 9: time series

25. **What is stationarity and why does it matter?** A stationary series has stable mean and variance and a stable autocorrelation structure. ARIMA-type models assume it, so non-stationary series are differenced.
26. **What did ADF and KPSS say?** On the level series they disagree: ADF p = 0.0002 (stationary), KPSS p = 0.019 (non-stationary). After one difference both agree (ADF p about 0, KPSS p = 0.1). Disagreement usually points to trend or seasonality rather than a unit root.
27. **What are the null hypotheses?** ADF: unit root (non-stationary). KPSS: stationary. So a low p-value means opposite things for the two tests.
28. **Why d = 1 and D = 1?** The series has trend and strong seasonality (STL strengths 0.53 and 0.86). Caveat: with D = 1 only 35 points remain, ADF on the seasonal difference alone gave p = 0.54, KPSS stayed borderline (0.047), and over-differencing is a risk. I also used ACF/PACF and an AIC search.
29. **Explain Holt-Winters.** Exponential smoothing of level, trend and seasonality with weights that decay with age. I used additive seasonality with a damped trend, which stops the trend extrapolating forever.
30. **Why did Holt-Winters beat SARIMA?** Holt-Winters has fewer parameters to estimate and is robust on short data. SARIMA with d = 1 and D = 1 loses 13 observations to differencing and needs seasonal parameters from only 3 to 4 years. Hold-out MAE 10,897 (MAPE 18.5%) vs 15,105 (34.0%); CV mean MAE 10,981 vs 14,513, with fold SD 2,729 vs 6,974.
31. **Is that a significant difference?** Not formally. Holt-Winters was better in only 4 of 7 folds, Wilcoxon p = 0.375, so the ranking against SARIMA is tentative. It is clearly better than seasonal naive and ARIMA(1,1,1) (7 of 7 folds, p = 0.016).
32. **Why does 48 months limit SARIMA?** With D = 1 at lag 12, a 24-month training window leaves 12 usable points for up to 5 parameters. Each calendar month appears only 2 to 3 times in training, so seasonal terms are unstable; the AIC-chosen order changed across folds.
33. **Does that mean SARIMA is a bad method?** No. It means that with this short series it does not beat simpler methods. With a much longer series it could be competitive; I have not tested that.
34. **Why was plain ARIMA so poor?** It has no seasonal term but the series is highly seasonal (STL seasonal strength 0.86): MAPE 54.1% on the hold-out, 49.1% in CV.
35. **Why not just use one hold-out?** One 12-month split is a single noisy experiment. I added rolling-origin CV (7 folds, horizon 6, step 3) and a seasonal-naive baseline. Caveat: the folds overlap, so they are not independent.
36. **Why is seasonal naive an important baseline?** If a complex model cannot beat "same month last year", it adds no value. SARIMA (CV MAE 14,513) did not beat it (13,739) on average; Holt-Winters did (10,981), in 7 of 7 folds.
37. **What are MAE, RMSE, MAPE, MASE?** MAE: mean absolute error. RMSE: root of mean squared error, penalises large misses. MAPE: mean percentage error, unstable when actuals are small. MASE: MAE divided by the in-sample seasonal-naive MAE; below 1 means better than that scale. Holt-Winters CV MASE was 1.24 (seasonal naive 1.53, SARIMA 1.67), so even the best model is above 1 on this scale.
38. **What do the residual diagnostics show?** Holt-Winters residuals: Ljung-Box p = 0.329 (lag 6) and 0.165 (lag 12), Jarque-Bera p = 0.577: no evidence of leftover autocorrelation or non-normality. SARIMA residuals had Ljung-Box lag 12 p = 0.010. With 35 to 48 residuals these tests are weak.
39. **How reliable is the 2019 forecast?** Moderate at best. CV MAPE is about 22%. It assumes the 2017-2018 growth and seasonal pattern continue. Intervals are bootstrap-based and may be too narrow; December 2019: 116,031 (95% band 56,622 to 189,080).
40. **Is Holt-Winters best for every series?** No. By CV MAE, seasonal naive wins for Furniture, Central and Home Office, SARIMA for Technology, and Holt-Winters variants for the others. Hold-out MAPE for sub-series is 15 to 60%.

## F. Chapter 10 and business results

41. **Key business insights?** Strong Q4 seasonality (index: Nov 185, Dec 173, Sep 164; Feb 30). 22.2% of products produce 80% of sales. Discounts above 20% lose money (-10.1% margin at 20-30%, -119.2% above 50%). Tables, Bookcases and Supplies lose money.
42. **Does discounting cause losses?** I can only say they are associated (Spearman -0.54 per line). Product mix is a confounder, so it is not proven causal.
43. **Why k = 4 in RFM when silhouette is highest at k = 2?** Silhouette was 0.350 at k = 2 vs 0.254 at k = 4. I chose 4 for business interpretability and say so. The segment names are my labels from recency and spend rules, not k-means output.
44. **What is the status of Power BI?** The .pbix is NOT built yet. Curated tables, forecast CSVs, Power Query scripts, DAX, model, theme and wireframes are ready; the checklist is unticked. I do not claim screenshots I do not have.
45. **What would you do next?** Build the dashboard and check KPIs against the report, try longer data, add price or promotion regressors, review the literature, and evaluate with a business cost metric.
