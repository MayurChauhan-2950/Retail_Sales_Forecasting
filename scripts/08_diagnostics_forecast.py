"""Step 8 - Diagnostics and interval forecast (Ch9).
Stationarity (ADF + KPSS) and differencing decision, STL decomposition, residual analysis
(Ljung-Box, Jarque-Bera, Shapiro-Wilk, ACF/PACF, QQ) for Holt-Winters and SARIMA, 12-month forecast
with 80% and 95% intervals (fan chart) from the model chosen by CV (script 07).
Outputs: data/forecast/stationarity_tests.csv, residual_tests.csv, forecast_total.csv, figures diag_*.png / fan_chart_total.png,
appends a section to reports/model_accuracy.md"""
import warnings
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.tsa.seasonal import STL
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.statespace.sarimax import SARIMAX
from common import CLEAN, FORECAST, REPORTS, monthly_sales, md_table
import tsmodels as tm
import style

warnings.filterwarnings("ignore")
df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date"])
y = monthly_sales(df)
H = 12

# ---- 1. stationarity
variants = {"level": y, "first difference (d=1)": y.diff().dropna(), "seasonal difference (D=1, lag 12)": y.diff(12).dropna(),
            "d=1 and D=1": y.diff().diff(12).dropna()}
srows = []
for name, s in variants.items():
    a = adfuller(s, autolag="AIC")
    k = kpss(s, regression="c", nlags="auto")
    srows.append({"series": name, "n": len(s), "ADF_stat": a[0], "ADF_p": a[1], "KPSS_stat": k[0], "KPSS_p(>=0.1 means 0.1)": k[1],
                  "ADF_says": "stationary" if a[1] < .05 else "unit root", "KPSS_says": "non-stationary" if k[1] < .05 else "stationary"})
st = pd.DataFrame(srows)
st.round(4).to_csv(FORECAST / "stationarity_tests.csv", index=False)
print(st.round(3).to_string(index=False))

# ---- 2. STL
stl = STL(y, period=12, robust=True).fit()
fig, axs = plt.subplots(4, 1, figsize=(10, 8), sharex=True)
for ax, (t, s_, c) in zip(axs, [("Observed", y, style.BLUE), ("Trend", stl.trend, style.ORANGE),
                                ("Seasonal", stl.seasonal, style.GREEN), ("Remainder", stl.resid, style.GREY)]):
    ax.plot(s_.index, s_, color=c, lw=1.6); ax.set_ylabel(t)
axs[0].set_title("STL decomposition of monthly sales (robust, period 12)")
axs[-1].set_xlabel("Month")
style.save(fig, "diag_stl_decomposition.png")
seas_strength = max(0, 1 - np.var(stl.resid) / np.var(stl.resid + stl.seasonal))
trend_strength = max(0, 1 - np.var(stl.resid) / np.var(stl.resid + stl.trend))

# ---- 3. residual diagnostics on in-sample one-step residuals (full data)
hw = ExponentialSmoothing(y, trend="add", damped_trend=True, seasonal="add", seasonal_periods=12,
                          initialization_method="estimated").fit()
sar = SARIMAX(y, order=(1, 1, 1), seasonal_order=(0, 1, 1, 12)).fit(disp=False)
resids = {"Holt-Winters additive (damped)": hw.resid, "SARIMA(1,1,1)(0,1,1,12)": sar.resid.iloc[13:]}   # drop diffuse start
rrows = []
for name, r in resids.items():
    r = pd.Series(np.asarray(r), dtype=float).dropna()
    lb = acorr_ljungbox(r, lags=[6, 12], model_df=0)
    jb = stats.jarque_bera(r); sw = stats.shapiro(r)
    rrows.append({"model": name, "n_resid": len(r), "mean": r.mean(), "sd": r.std(ddof=1),
                  "LjungBox_lag6_p": lb["lb_pvalue"].iloc[0], "LjungBox_lag12_p": lb["lb_pvalue"].iloc[1],
                  "JarqueBera_p": jb.pvalue, "Shapiro_p": sw.pvalue, "skew": stats.skew(r), "excess_kurtosis": stats.kurtosis(r)})
rt = pd.DataFrame(rrows)
rt.round(4).to_csv(FORECAST / "residual_tests.csv", index=False)
print(rt.round(3).to_string(index=False))

fig, axs = plt.subplots(2, 3, figsize=(13, 7))
for i, (name, r) in enumerate(resids.items()):
    r = pd.Series(np.asarray(r), dtype=float).dropna()
    plot_acf(r, lags=18, ax=axs[i, 0], color=style.BLUE, title=f"{name}: residual ACF")
    axs[i, 1].hist(r, bins=12, color=style.BLUE, alpha=.8); axs[i, 1].set_title("Residual histogram")
    axs[i, 1].set_xlabel("Residual (USD)")
    stats.probplot(r, dist="norm", plot=axs[i, 2]); axs[i, 2].set_title("Normal QQ plot")
    axs[i, 0].set_xlabel("Lag (months)"); axs[i, 0].set_ylabel("Autocorrelation")
style.save(fig, "diag_residuals.png")

fig, axs = plt.subplots(1, 3, figsize=(14, 4))
plot_acf(y, lags=24, ax=axs[0], title="ACF of sales (level)")
plot_acf(y.diff().diff(12).dropna(), lags=18, ax=axs[1], title="ACF after d=1, D=1")
plot_pacf(y.diff().diff(12).dropna(), lags=12, ax=axs[2], title="PACF after d=1, D=1", method="ywm")
for a in axs: a.set_xlabel("Lag (months)")
style.save(fig, "diag_acf_pacf.png")

# ---- 4. final forecast: model chosen by CV mean MAE among models that have an interval method
cvs = pd.read_csv(FORECAST / "cv_summary.csv")
interval_models = {"Holt-Winters additive (damped)": tm.hw_add_damped, "Holt-Winters additive (undamped)": tm.hw_add,
                   "Holt-Winters multiplicative": tm.hw_mul, "Holt-Winters mult. seasonal + damped trend": tm.hw_mul_damped,
                   "SARIMA(1,1,1)(0,1,1,12)": tm.sarima_fixed, "SARIMA (AIC search)": tm.sarima_search, "Seasonal naive": tm.snaive}
cand = cvs[cvs.model.isin(interval_models)].iloc[0]
best_name = cand["model"]
fc, how = tm.intervals(interval_models[best_name], y, H)
print(f"[08] forecast model {best_name}; intervals: {how}")
out = fc.rename_axis("month").reset_index()
out.insert(0, "level", "Total"); out.insert(1, "series", "All sales"); out["actual"] = np.nan; out["model"] = best_name
hist = pd.DataFrame({"level": "Total", "series": "All sales", "month": y.index, "actual": y.values})
full = pd.concat([hist, out], ignore_index=True)[["level", "series", "month", "actual", "forecast", "lower_80", "upper_80", "lower_95", "upper_95", "model"]]
full.round(2).to_csv(FORECAST / "forecast_total.csv", index=False)

fig, ax = plt.subplots(figsize=(11, 5.5))
ax.plot(y.index, y, color=style.BLUE, lw=1.8, label="Actual")
ax.fill_between(fc.index, fc.lower_95, fc.upper_95, color=style.ORANGE, alpha=.2, label="95% interval")
ax.fill_between(fc.index, fc.lower_80, fc.upper_80, color=style.ORANGE, alpha=.4, label="80% interval")
ax.plot(fc.index, fc.forecast, color=style.RED, lw=2, label=f"Forecast: {best_name}")
ax.set_title("12-month sales forecast with 80% and 95% fan chart"); ax.set_ylabel("Monthly sales (USD)"); ax.set_xlabel("Month")
ax.legend(loc="upper left", fontsize=9)
style.save(fig, "fan_chart_total.png")

md = ["", "## Diagnostics and interval forecast (script 08)", "",
      "### Stationarity tests (ADF null = unit root; KPSS null = stationary; 5% level)", md_table(st.round(4)), "",
      "**Test verdicts:** " + "; ".join(f"{r.series}: ADF p={r.ADF_p:.3f} ({r.ADF_says}), KPSS p={r['KPSS_p(>=0.1 means 0.1)']:.3f} ({r.KPSS_says})" for _, r in st.iterrows()) + ". "
      "The tests disagree on the level series (ADF rejects a unit root, KPSS rejects stationarity), the typical sign of a trend or seasonal pattern rather than a unit root; one regular difference (d=1) satisfies both tests. "
      "The seasonal difference alone is not enough for ADF, and adding it to d=1 leaves KPSS borderline, so over-differencing risk is real on 35 points.", "",
      "**Differencing decision.** Because the series has a rising trend and strong yearly seasonality "
      "(STL seasonal strength {:.2f}, trend strength {:.2f}), the SARIMA specification uses d=1 and D=1 (lag 12), and the table shows whether the doubly-differenced series passes both tests. "
      "With only 48 points these tests have low power: ADF can reject a unit root on a seasonal series that is still not trend-stationary, so the decision also rests on the ACF/PACF plots and on the AIC search in script 07, not on a single test.".format(seas_strength, trend_strength), "",
      "### Residual tests (one-step in-sample residuals, full data)", md_table(rt.round(4)), "",
      "Read: Ljung-Box p > 0.05 means no significant leftover autocorrelation; Jarque-Bera / Shapiro p > 0.05 means no evidence against normality. "
      "With 36-48 residuals these tests are weak, so a pass is not proof.", "",
      f"### Forecast for {fc.index[0]:%b %Y} to {fc.index[-1]:%b %Y}",
      f"Model: **{best_name}** (best CV mean MAE among models with an interval method). Interval method: **{how}**. Lower bounds are clipped at 0.", "",
      md_table(fc.round(2).rename_axis("month").reset_index().assign(month=lambda d: d["month"].dt.strftime("%Y-%m"))), "",
      "Figures: `figures/diag_stl_decomposition.png`, `figures/diag_residuals.png`, `figures/diag_acf_pacf.png`, `figures/fan_chart_total.png`", ""]
p = REPORTS / "model_accuracy.md"
txt = p.read_text(encoding="utf-8")
txt = txt.split("\n## Diagnostics and interval forecast (script 08)")[0].rstrip("\n") + "\n" + "\n".join(md)
p.write_text(txt, encoding="utf-8")
(FORECAST / "diag_strengths.csv").write_text(f"metric,value\nseasonal_strength,{seas_strength:.4f}\ntrend_strength,{trend_strength:.4f}\n")
print("[08] done")
