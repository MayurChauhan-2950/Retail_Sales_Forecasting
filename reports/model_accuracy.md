# Time Series Model Accuracy (Ch9)

- Series: monthly total sales, Jan 2015 to Dec 2018 (48 months)
- Split: train = first 36 months, hold-out test = last 12 months (Jan 2018 to Dec 2018)
- ADF stationarity test p-value: original series 0.000, first difference 0.000
- Metrics: MAE = mean |error|; RMSE = sqrt(mean error^2); MAPE = mean |error|/actual x 100

## Accuracy on the hold-out (sorted by RMSE)
| model | MAE | RMSE | MAPE_% |
|---|---|---|---|
| Holt-Winters (additive) | 10,896.6345 | 14,117.724 | 18.5068 |
| SARIMA(1,1,1)(0,1,1,12) | 15,104.5647 | 17,570.5088 | 33.9769 |
| ARIMA(1,1,1) | 23,450.6273 | 27,208.4475 | 54.1058 |

**Best model: Holt-Winters (additive)** - MAE 10,896.63, RMSE 14,117.72, MAPE 18.51%

## Seasonal index (additive decomposition, $ above/below trend)
| month | seasonal_effect |
|---|---|
| January | -19,009.77 |
| February | -28,141.54 |
| March | 2,645.88 |
| April | -11,364.64 |
| May | -5,256.48 |
| June | -10,426.9 |
| July | -9,505.79 |
| August | -12,154.78 |
| September | 28,868.55 |
| October | -3,702.3 |
| November | 33,052.89 |
| December | 34,994.88 |

## Final forecast (next 12 months, model refit on all data; interval = approx. +/-1.96*residual std)
| month | forecast | lower_95 | upper_95 | model |
|---|---|---|---|---|
| 2019-01 | 49,386.76 | 31,778.18 | 66,995.34 | Holt-Winters (additive) |
| 2019-02 | 41,475.74 | 23,867.16 | 59,084.31 | Holt-Winters (additive) |
| 2019-03 | 74,998.04 | 57,389.47 | 92,606.62 | Holt-Winters (additive) |
| 2019-04 | 61,269.33 | 43,660.76 | 78,877.91 | Holt-Winters (additive) |
| 2019-05 | 67,933.81 | 50,325.24 | 85,542.39 | Holt-Winters (additive) |
| 2019-06 | 65,178.3 | 47,569.72 | 82,786.88 | Holt-Winters (additive) |
| 2019-07 | 66,495.77 | 48,887.19 | 84,104.35 | Holt-Winters (additive) |
| 2019-08 | 66,534.51 | 48,925.93 | 84,143.09 | Holt-Winters (additive) |
| 2019-09 | 107,466.28 | 89,857.7 | 125,074.86 | Holt-Winters (additive) |
| 2019-10 | 77,578.54 | 59,969.97 | 95,187.12 | Holt-Winters (additive) |
| 2019-11 | 115,687.27 | 98,078.69 | 133,295.85 | Holt-Winters (additive) |
| 2019-12 | 116,030.81 | 98,422.23 | 133,639.39 | Holt-Winters (additive) |

Figures: `figures/ts_decomposition.png`, `figures/ts_holdout_forecast.png`, `figures/ts_final_forecast.png`

## Rolling-origin cross-validation (script 07)

- Design: expanding window, minimum training length 24 months, horizon 6 months, origin step 3 months -> 7 folds (first fold tests 2017-01, windows overlap, so folds are not independent).
- Models: seasonal naive, naive, SES, Holt-Winters (additive damped = the project's 'Holt-Winters (additive)', additive undamped, multiplicative, multiplicative-seasonal with damped trend), ETS chosen by AICc among 4 configurations, ARIMA(1,1,1), SARIMA(1,1,1)(0,1,1,12), SARIMA with a 16-candidate AIC search (p,q,P,Q in {0,1}, d=D=1) re-run inside each fold.
- MASE scales MAE by the in-sample seasonal-naive MAE of the training window (below 1 = better than seasonal naive). MAPE and sMAPE are in %.
- **Best by mean CV MAE: Holt-Winters additive (damped).  Best on the single 2018 hold-out by MAE: Holt-Winters additive (damped).**

### Mean and SD across folds, with the original 2018 hold-out (train 36 / test 12)
| model | MAE_mean | MAE_sd | RMSE_mean | MAPE_mean | sMAPE_mean | MASE_mean | MASE_sd | holdout_MAE | holdout_RMSE | holdout_MAPE |
|---|---|---|---|---|---|---|---|---|---|---|
| Holt-Winters additive (damped) | 10,981.37 | 2,729.1 | 13,444.72 | 21.67 | 24.27 | 1.24 | 0.36 | 10,896.63 | 14,117.72 | 18.51 |
| ETS (AICc-selected) | 11,722.87 | 3,916.95 | 14,017.5 | 22.53 | 24.75 | 1.32 | 0.46 | 11,820.37 | 15,607.36 | 19.2 |
| Holt-Winters multiplicative | 11,808.94 | 2,792.99 | 14,684.34 | 23.01 | 27.34 | 1.32 | 0.32 | 13,738.53 | 17,692.74 | 23.32 |
| Holt-Winters additive (undamped) | 11,976.36 | 2,853.8 | 14,455.35 | 24.01 | 25.16 | 1.34 | 0.34 | 11,453.69 | 12,541.79 | 22.59 |
| Holt-Winters mult. seasonal + damped trend | 13,694.76 | 5,089.75 | 16,671.75 | 26.15 | 30.2 | 1.54 | 0.6 | 13,459.24 | 17,370.44 | 22.98 |
| Seasonal naive | 13,738.74 | 3,264.84 | 16,541.86 | 25 | 29.84 | 1.53 | 0.3 | 15,467.89 | 18,985.7 | 24.52 |
| SARIMA(1,1,1)(0,1,1,12) | 14,513.02 | 6,974.07 | 16,199.16 | 36.6 | 28.28 | 1.67 | 1 | 15,104.56 | 17,570.51 | 33.98 |
| SARIMA (AIC search) | 14,578.92 | 7,155.76 | 16,665.81 | 35.38 | 28.44 | 1.66 | 1.01 | 15,093.21 | 17,934.62 | 33.64 |
| SES | 20,844.17 | 9,611.48 | 25,714.65 | 39.15 | 38.6 | 2.27 | 0.92 | 21,836.42 | 26,045.08 | 48.36 |
| ARIMA(1,1,1) | 22,601.02 | 7,685.79 | 27,046.61 | 49.09 | 40.75 | 2.52 | 0.87 | 23,450.63 | 27,208.45 | 54.11 |
| Naive | 28,381.78 | 13,840.59 | 31,749.71 | 69.34 | 47.22 | 3.15 | 1.48 | 39,472.57 | 44,191.89 | 97.32 |

### Paired comparison of fold MAE against Holt-Winters additive (damped)
Positive difference = the listed model has larger error. Wilcoxon and paired-t p-values use the 7 overlapping folds, so treat them as indicative only; with this few folds the smallest possible two-sided Wilcoxon p is 0.0156.

| reference | model | mean_MAE_diff(model-ref) | folds_ref_better | folds | wilcoxon_p | paired_t_p |
|---|---|---|---|---|---|---|
| Holt-Winters additive (damped) | ARIMA(1,1,1) | 11,619.657 | 7 | 7 | 0.016 | 0.004 |
| Holt-Winters additive (damped) | ETS (AICc-selected) | 741.506 | 4 | 7 | 0.578 | 0.433 |
| Holt-Winters additive (damped) | Holt-Winters additive (undamped) | 994.989 | 5 | 7 | 0.109 | 0.085 |
| Holt-Winters additive (damped) | Holt-Winters mult. seasonal + damped trend | 2,713.397 | 6 | 7 | 0.031 | 0.097 |
| Holt-Winters additive (damped) | Holt-Winters multiplicative | 827.573 | 6 | 7 | 0.078 | 0.101 |
| Holt-Winters additive (damped) | Naive | 17,400.416 | 7 | 7 | 0.016 | 0.019 |
| Holt-Winters additive (damped) | SARIMA (AIC search) | 3,597.549 | 4 | 7 | 0.375 | 0.243 |
| Holt-Winters additive (damped) | SARIMA(1,1,1)(0,1,1,12) | 3,531.657 | 4 | 7 | 0.375 | 0.252 |
| Holt-Winters additive (damped) | SES | 9,862.804 | 6 | 7 | 0.031 | 0.02 |
| Holt-Winters additive (damped) | Seasonal naive | 2,757.377 | 7 | 7 | 0.016 | 0.043 |

### Why 48 months limits SARIMA
- A seasonal period of 12 with D=1 consumes 12 observations for differencing; a 24-month training window leaves only 12 usable points to estimate up to 5 parameters, and at the 36-month origin 24 points.
- Seasonal parameters are identified from only 2-3 repeats of each calendar month; the estimates are unstable and the AIC search order changes between folds (see `data/forecast/cv_sarima_orders.csv`).
- Exponential smoothing and seasonal naive need fewer parameters or none, so they are less exposed to this estimation noise.
- The series itself is also irregular (large Sep/Nov/Dec peaks and a few outlying months), so a conclusion about the best model is tentative: differences between close models are within fold-to-fold variation.

Figures: `figures/cv_mae_by_model.png`, `figures/cv_fold_mae.png`, `figures/cv_mase_by_model.png`

## Diagnostics and interval forecast (script 08)

### Stationarity tests (ADF null = unit root; KPSS null = stationary; 5% level)
| series | n | ADF_stat | ADF_p | KPSS_stat | KPSS_p(>=0.1 means 0.1) | ADF_says | KPSS_says |
|---|---|---|---|---|---|---|---|
| level | 48 | -4.4938 | 0.0002 | 0.643 | 0.0187 | stationary | non-stationary |
| first difference (d=1) | 47 | -9.0577 | 0 | 0.2726 | 0.1 | stationary | stationary |
| seasonal difference (D=1, lag 12) | 36 | -1.4818 | 0.5425 | 0.4672 | 0.0491 | unit root | non-stationary |
| d=1 and D=1 | 35 | -4.4813 | 0.0002 | 0.4785 | 0.0465 | stationary | non-stationary |

**Test verdicts:** level: ADF p=0.000 (stationary), KPSS p=0.019 (non-stationary); first difference (d=1): ADF p=0.000 (stationary), KPSS p=0.100 (stationary); seasonal difference (D=1, lag 12): ADF p=0.543 (unit root), KPSS p=0.049 (non-stationary); d=1 and D=1: ADF p=0.000 (stationary), KPSS p=0.047 (non-stationary). The tests disagree on the level series (ADF rejects a unit root, KPSS rejects stationarity), the typical sign of a trend or seasonal pattern rather than a unit root; one regular difference (d=1) satisfies both tests. The seasonal difference alone is not enough for ADF, and adding it to d=1 leaves KPSS borderline, so over-differencing risk is real on 35 points.

**Differencing decision.** Because the series has a rising trend and strong yearly seasonality (STL seasonal strength 0.86, trend strength 0.53), the SARIMA specification uses d=1 and D=1 (lag 12), and the table shows whether the doubly-differenced series passes both tests. With only 48 points these tests have low power: ADF can reject a unit root on a seasonal series that is still not trend-stationary, so the decision also rests on the ACF/PACF plots and on the AIC search in script 07, not on a single test.

### Residual tests (one-step in-sample residuals, full data)
| model | n_resid | mean | sd | LjungBox_lag6_p | LjungBox_lag12_p | JarqueBera_p | Shapiro_p | skew | excess_kurtosis |
|---|---|---|---|---|---|---|---|---|---|
| Holt-Winters additive (damped) | 48 | 594.2591 | 8,983.9681 | 0.3286 | 0.1652 | 0.5768 | 0.1811 | 0.28 | -0.4864 |
| SARIMA(1,1,1)(0,1,1,12) | 35 | -3,135.6755 | 13,480.3074 | 0.0908 | 0.0102 | 0.7933 | 0.2873 | -0.015 | -0.5627 |

Read: Ljung-Box p > 0.05 means no significant leftover autocorrelation; Jarque-Bera / Shapiro p > 0.05 means no evidence against normality. With 36-48 residuals these tests are weak, so a pass is not proof.

### Forecast for Jan 2019 to Dec 2019
Model: **Holt-Winters additive (damped)** (best CV mean MAE among models with an interval method). Interval method: **residual-bootstrap simulation (2,000 paths)**. Lower bounds are clipped at 0.

| month | forecast | lower_80 | upper_80 | lower_95 | upper_95 |
|---|---|---|---|---|---|
| 2019-01 | 49,386.76 | 41,201.82 | 62,582.76 | 36,337.53 | 67,151 |
| 2019-02 | 41,475.74 | 31,746.29 | 55,547.51 | 25,491.98 | 59,915.84 |
| 2019-03 | 74,998.04 | 63,732.67 | 89,886.31 | 57,559.2 | 95,657.88 |
| 2019-04 | 61,269.33 | 48,539.21 | 77,002.77 | 41,166.37 | 84,965.2 |
| 2019-05 | 67,933.81 | 53,148.28 | 86,102.83 | 44,802.17 | 94,742.9 |
| 2019-06 | 65,178.3 | 47,281.39 | 86,857.2 | 38,448.47 | 97,336.76 |
| 2019-07 | 66,495.77 | 45,449.58 | 91,407.23 | 35,133.07 | 104,583.27 |
| 2019-08 | 66,534.51 | 43,085.22 | 95,788.45 | 30,445.2 | 109,388.07 |
| 2019-09 | 107,466.28 | 80,702.2 | 141,591.97 | 65,541.34 | 158,153.44 |
| 2019-10 | 77,578.54 | 46,859.82 | 116,714.54 | 30,832.88 | 133,992.43 |
| 2019-11 | 115,687.27 | 81,166.88 | 161,128.63 | 62,640 | 178,961.04 |
| 2019-12 | 116,030.81 | 77,777.91 | 165,381.11 | 56,622.02 | 189,079.95 |

Figures: `figures/diag_stl_decomposition.png`, `figures/diag_residuals.png`, `figures/diag_acf_pacf.png`, `figures/fan_chart_total.png`
