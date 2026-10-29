"""Step 9 - Forecasts by Category, Region and Segment (Ch9, Power BI ready).
For each monthly series: rolling-origin CV (same design as script 07: min train 24, horizon 6, step 3)
over 4 candidate models; the model with the lowest mean CV MAE is refit on all 48 months and forecasts 2019 with
80%/95% intervals (bootstrap for exponential smoothing, model-based for SARIMA, empirical for seasonal naive).
Outputs: data/forecast/forecast_{category,region,segment}.csv, forecast_all_series.csv (adds Total from script 08),
segment_accuracy.csv, segment_best_models.csv, figures seg_forecast_*.png"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from common import CLEAN, FORECAST, REPORTS
import tsmodels as tm
import style

df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date"])
CAND = {"Seasonal naive": tm.snaive, "Holt-Winters additive (damped)": tm.hw_add_damped,
        "Holt-Winters multiplicative": tm.hw_mul, "SARIMA(1,1,1)(0,1,1,12)": tm.sarima_fixed}
MIN_TRAIN, H, STEP, FH = 24, 6, 3, 12
COLS = ["level", "series", "month", "actual", "forecast", "lower_80", "upper_80", "lower_95", "upper_95", "model"]
acc_rows, best_rows, frames = [], [], []
levels = {"Category": "Category", "Region": "Region", "Segment": "Segment"}

for level, col in levels.items():
    wide = (df.pivot_table(index=pd.Grouper(key="Order Date", freq="MS"), columns=col, values="Sales", aggfunc="sum")
            .fillna(0))
    wide.index.freq = "MS"
    lvl_frames = []
    for ser in wide.columns:
        y = wide[ser]
        folds = {m: [] for m in CAND}
        for o in range(MIN_TRAIN, len(y) - H + 1, STEP):
            tr, te = y.iloc[:o], y.iloc[o:o + H]
            for m, fn in CAND.items():
                try:
                    folds[m].append(tm.metrics(te, fn(tr, H), tr))
                except Exception as ex:
                    print(f"[09] {ser} {m} fold failed: {ex}")
        for m, lst in folds.items():
            if lst:
                d = pd.DataFrame(lst).mean()
                acc_rows.append({"level": level, "series": ser, "model": m, "folds": len(lst), **{f"CV_{k}": v for k, v in d.items()}})
        sub = pd.DataFrame([r for r in acc_rows if r["level"] == level and r["series"] == ser])
        best = sub.loc[sub["CV_MAE"].idxmin(), "model"]
        # 2018 hold-out of the chosen model (train 36 / test 12)
        tr, te = y.iloc[:-12], y.iloc[-12:]
        hm = tm.metrics(te, CAND[best](tr, 12), tr)
        fc, how = tm.intervals(CAND[best], y, FH)
        best_rows.append({"level": level, "series": ser, "best_model": best, "interval_method": how,
                          "CV_MAE": sub["CV_MAE"].min(), "CV_MASE": sub.loc[sub["CV_MAE"].idxmin(), "CV_MASE"],
                          "CV_MAPE": sub.loc[sub["CV_MAE"].idxmin(), "CV_MAPE"],
                          **{f"holdout2018_{k}": v for k, v in hm.items()},
                          "mean_monthly_sales": y.mean(), "forecast_2019_total": fc["forecast"].sum(),
                          "actual_2018_total": te.sum()})
        hist = pd.DataFrame({"level": level, "series": ser, "month": y.index, "actual": y.values})
        f = fc.rename_axis("month").reset_index().assign(level=level, series=ser, actual=np.nan, model=best)
        lvl_frames.append(pd.concat([hist, f], ignore_index=True)[COLS])
        print(f"[09] {level}/{ser}: best={best} CV_MAE={sub['CV_MAE'].min():,.0f}")
    lf = pd.concat(lvl_frames, ignore_index=True)
    lf.round(2).to_csv(FORECAST / f"forecast_{level.lower()}.csv", index=False)
    frames.append(lf)

tot = pd.read_csv(FORECAST / "forecast_total.csv", parse_dates=["month"])
allf = pd.concat([tot[COLS]] + frames, ignore_index=True)
allf.round(2).to_csv(FORECAST / "forecast_all_series.csv", index=False)
acc = pd.DataFrame(acc_rows); best_df = pd.DataFrame(best_rows)
acc.round(4).to_csv(FORECAST / "segment_accuracy.csv", index=False)
best_df.round(4).to_csv(FORECAST / "segment_best_models.csv", index=False)

# figures: one small-multiple panel per level
for level in levels:
    d = allf[allf.level == level]; names = list(d.series.unique())
    fig, axs = plt.subplots(1, len(names), figsize=(5 * len(names), 4.2), sharey=False)
    for ax, n in zip(np.atleast_1d(axs), names):
        s = d[d.series == n]; a = s[s.actual.notna()]; f = s[s.forecast.notna()]
        ax.plot(a.month, a.actual, color=style.BLUE, lw=1.4)
        ax.fill_between(f.month, f.lower_95, f.upper_95, color=style.ORANGE, alpha=.2)
        ax.fill_between(f.month, f.lower_80, f.upper_80, color=style.ORANGE, alpha=.4)
        ax.plot(f.month, f.forecast, color=style.RED, lw=1.8)
        ax.set_title(f"{n} ({f.model.iloc[0].split(' (')[0]})", fontsize=10); ax.set_xlabel("Month"); ax.tick_params(axis="x", rotation=30)
    np.atleast_1d(axs)[0].set_ylabel("Monthly sales (USD)")
    fig.suptitle(f"2019 forecast by {level} (blue actual, red forecast, bands 80%/95%)", fontweight="bold")
    style.save(fig, f"seg_forecast_{level.lower()}.png")
print("[09] wrote forecast CSVs for Power BI: forecast_all_series.csv (" + str(len(allf)) + " rows)")
