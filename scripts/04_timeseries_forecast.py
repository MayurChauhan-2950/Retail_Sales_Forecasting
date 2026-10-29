"""Step 4 - Time series analysis and forecasting (Ch9).
Monthly sales -> decomposition -> models on a train/test split (last 12 months held out)
-> accuracy table (MAE, RMSE, MAPE) -> best model refit on all data -> 12-month forecast with interval.
Outputs: reports/figures/ts_*.png, reports/model_accuracy.md, data/forecast/*.csv"""
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.holtwinters import SimpleExpSmoothing, Holt, ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
from common import CLEAN, FORECAST, FIGS, REPORTS, monthly_sales, md_table

warnings.filterwarnings("ignore")
df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date"])
y = monthly_sales(df)
H, SP = 12, 12                       # hold-out length and seasonal period
train, test = y.iloc[:-H], y.iloc[-H:]
print(f"[04] monthly points={len(y)} ({y.index[0]:%Y-%m} to {y.index[-1]:%Y-%m}); train={len(train)} test={len(test)}")

# ---- decomposition: trend + seasonality + residual
dec = seasonal_decompose(y, model="additive", period=SP)
fig = dec.plot(); fig.set_size_inches(10, 8); fig.suptitle("Additive decomposition of monthly sales", y=1.0)
fig.tight_layout(); fig.savefig(FIGS / "ts_decomposition.png", dpi=130); plt.close(fig)
season_idx = dec.seasonal.iloc[:12]
season_idx.index = season_idx.index.month_name()
adf_p = adfuller(y)[1]; adf_d = adfuller(y.diff().dropna())[1]


# ---- model definitions: each takes a training series and returns (forecast Series, fitted result)
def idx_future(s, h): return pd.date_range(s.index[-1] + pd.offsets.MonthBegin(1), periods=h, freq="MS")

def naive(s, h): return pd.Series(s.iloc[-1], index=idx_future(s, h)), None
def snaive(s, h): return pd.Series(s.iloc[-SP:].values[:h], index=idx_future(s, h)), None
def ses(s, h):
    r = SimpleExpSmoothing(s, initialization_method="estimated").fit(); return r.forecast(h), r
def holt(s, h):
    r = Holt(s, damped_trend=True, initialization_method="estimated").fit(); return r.forecast(h), r
def hw(s, h):
    r = ExponentialSmoothing(s, trend="add", seasonal="add", seasonal_periods=SP, damped_trend=True,
                             initialization_method="estimated").fit(); return r.forecast(h), r
def hw_mult(s, h):
    r = ExponentialSmoothing(s, trend=None, seasonal="mul", seasonal_periods=SP,
                             initialization_method="estimated").fit(); return r.forecast(h), r
def arima(s, h):
    r = ARIMA(s, order=(1, 1, 1)).fit(); return r.forecast(h), r
def sarima(s, h):
    r = SARIMAX(s, order=(1, 1, 1), seasonal_order=(0, 1, 1, SP)).fit(disp=False); return r.forecast(h), r

# the three methods compared in this project (same train/test split for all)
models = {"Holt-Winters (additive)": hw, "ARIMA(1,1,1)": arima, "SARIMA(1,1,1)(0,1,1,12)": sarima}

def metrics(actual, pred):
    e = actual.values - pred.values
    return {"MAE": np.mean(np.abs(e)), "RMSE": np.sqrt(np.mean(e ** 2)),
            "MAPE_%": np.mean(np.abs(e) / actual.values) * 100}

rows, preds = [], {"actual": test}
for name, fn in models.items():
    try:
        p, _ = fn(train, H)
        p.index = test.index
        preds[name] = p
        rows.append({"model": name, **metrics(test, p)})
    except Exception as ex:
        print(f"[04] model {name} failed: {ex}")
acc = pd.DataFrame(rows).sort_values("RMSE").reset_index(drop=True)
best = acc.loc[0, "model"]
print(acc.round(2).to_string(index=False))
print(f"[04] best model on hold-out (lowest RMSE): {best}")

# ---- plot hold-out predictions
fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(train.index, train, color="#888", label="train")
ax.plot(test.index, test, color="black", lw=2, label="actual (hold-out)")
for name in models:
    if name in preds:
        ax.plot(test.index, preds[name], lw=1.6, ls="--", label=name)
ax.set_title("Hold-out forecast vs actual (last 12 months)"); ax.set_ylabel("Monthly sales ($)")
ax.legend(); ax.grid(alpha=.3); fig.tight_layout(); fig.savefig(FIGS / "ts_holdout_forecast.png", dpi=130); plt.close(fig)
pd.DataFrame(preds).rename_axis("month").round(2).to_csv(FORECAST / "holdout_predictions.csv")

# ---- final forecast: refit best model on ALL data, predict next 12 months with a 95% interval
fc, res = models[best](y, H)
if hasattr(res, "get_forecast"):                       # ARIMA / SARIMA give a proper interval
    ci = res.get_forecast(H).conf_int(alpha=0.05)
    lower, upper, how = ci.iloc[:, 0].values, ci.iloc[:, 1].values, "model confidence interval"
else:                                                  # exponential smoothing: +/- 1.96 * in-sample residual std
    sd = np.std(res.resid, ddof=1) if res is not None else np.std(y.diff().dropna())
    lower, upper, how = fc.values - 1.96 * sd, fc.values + 1.96 * sd, "approx. +/-1.96*residual std"
lower = np.maximum(lower, 0)
out = pd.DataFrame({"month": fc.index, "forecast": fc.values.round(2), "lower_95": np.round(lower, 2),
                    "upper_95": np.round(upper, 2), "model": best})
out.to_csv(FORECAST / "sales_forecast.csv", index=False)
hist = pd.DataFrame({"month": y.index, "actual_sales": y.values.round(2)})
hist.to_csv(FORECAST / "monthly_sales_actual.csv", index=False)
# one combined file (actual + forecast rows) convenient for a single Power BI line chart
comb = pd.concat([hist.rename(columns={"actual_sales": "value"}).assign(type="Actual", lower_95=np.nan, upper_95=np.nan),
                  out.rename(columns={"forecast": "value"}).assign(type="Forecast")[["month", "value", "type", "lower_95", "upper_95"]]])
comb.to_csv(FORECAST / "sales_actual_plus_forecast.csv", index=False)
acc.round(4).to_csv(FORECAST / "model_accuracy.csv", index=False)

fig, ax = plt.subplots(figsize=(11, 5))
ax.plot(y.index, y, color="#1f77b4", label="actual")
ax.plot(fc.index, fc, color="#d62728", label=f"forecast ({best})")
ax.fill_between(fc.index, lower, upper, color="#d62728", alpha=.2, label="95% interval")
ax.set_title("12-month sales forecast"); ax.set_ylabel("Monthly sales ($)"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(FIGS / "ts_final_forecast.png", dpi=130); plt.close(fig)

b = acc.iloc[0]
md = ["# Time Series Model Accuracy (Ch9)", "",
      f"- Series: monthly total sales, {y.index[0]:%b %Y} to {y.index[-1]:%b %Y} ({len(y)} months)",
      f"- Split: train = first {len(train)} months, hold-out test = last {H} months ({test.index[0]:%b %Y} to {test.index[-1]:%b %Y})",
      f"- ADF stationarity test p-value: original series {adf_p:.3f}, first difference {adf_d:.3f}",
      "- Metrics: MAE = mean |error|; RMSE = sqrt(mean error^2); MAPE = mean |error|/actual x 100", "",
      "## Accuracy on the hold-out (sorted by RMSE)", md_table(acc), "",
      f"**Best model: {best}** - MAE {b['MAE']:,.2f}, RMSE {b['RMSE']:,.2f}, MAPE {b['MAPE_%']:.2f}%", "",
      "## Seasonal index (additive decomposition, $ above/below trend)", md_table(season_idx.round(2).rename("seasonal_effect").rename_axis("month").to_frame(), index=True), "",
      f"## Final forecast (next {H} months, model refit on all data; interval = {how})", md_table(out.assign(month=out["month"].dt.strftime("%Y-%m"))), "",
      "Figures: `figures/ts_decomposition.png`, `figures/ts_holdout_forecast.png`, `figures/ts_final_forecast.png`", ""]
(REPORTS / "model_accuracy.md").write_text("\n".join(md), encoding="utf-8")
print(f"[04] best={best} MAE={b['MAE']:.2f} RMSE={b['RMSE']:.2f} MAPE={b['MAPE_%']:.2f}%")
print("[04] wrote data/forecast/*.csv and reports/model_accuracy.md")
