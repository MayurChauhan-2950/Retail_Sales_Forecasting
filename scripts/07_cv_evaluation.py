"""Step 7 - Rigorous forecast evaluation (Ch9).
Rolling-origin (expanding window) cross-validation: min train 24 months, horizon 6, origin step 3 months
-> 7 folds (origins after month 24,27,...,42; windows overlap because of the step). Plus the original
single 2018 hold-out (train 36 / test 12) for every model. Metrics: MAE, RMSE, MAPE, sMAPE, MASE.
Outputs: data/forecast/cv_fold_results.csv, cv_summary.csv, holdout_all_models.csv, cv_paired_tests.csv,
reports/figures/cv_*.png, appends a section to reports/model_accuracy.md"""
import numpy as np
import pandas as pd
from scipy import stats
from common import CLEAN, FORECAST, FIGS, REPORTS, monthly_sales, md_table
import tsmodels as tm
import style
import matplotlib.pyplot as plt

df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date"])
y = monthly_sales(df)
MIN_TRAIN, H, STEP = 24, 6, 3
origins = list(range(MIN_TRAIN, len(y) - H + 1, STEP))
print(f"[07] {len(y)} months, {len(origins)} folds, horizon {H}, origins (train length) {origins}")

rows, orders = [], []
for k, o in enumerate(origins, 1):
    tr, te = y.iloc[:o], y.iloc[o:o + H]
    for name, fn in tm.MODELS.items():
        try:
            if fn is tm.sarima_search:
                p, ordr = tm.sarima_search(tr, H, True)
                orders.append({"fold": k, "train_end": tr.index[-1].strftime("%Y-%m"), "order": str(ordr)})
            else:
                p = fn(tr, H)
            rows.append({"fold": k, "train_end": tr.index[-1].strftime("%Y-%m"), "test_start": te.index[0].strftime("%Y-%m"),
                         "model": name, **tm.metrics(te, p, tr)})
        except Exception as ex:
            print(f"[07] fold {k} {name} failed: {ex}")
    print(f"[07] fold {k} done")
cv = pd.DataFrame(rows)
cv.round(4).to_csv(FORECAST / "cv_fold_results.csv", index=False)
pd.DataFrame(orders).to_csv(FORECAST / "cv_sarima_orders.csv", index=False)

MET = ["MAE", "RMSE", "MAPE", "sMAPE", "MASE"]
g = cv.groupby("model")[MET]
summ = g.mean().add_suffix("_mean").join(g.std().add_suffix("_sd")).join(cv.groupby("model")["fold"].count().rename("n_folds"))

# single 2018 hold-out for every model
tr, te = y.iloc[:-12], y.iloc[-12:]
hrows = []
for name, fn in tm.MODELS.items():
    try:
        p = fn(tr, 12)
        hrows.append({"model": name, **{f"holdout_{k}": v for k, v in tm.metrics(te, p, tr).items()}})
    except Exception as ex:
        print(f"[07] holdout {name} failed: {ex}")
hold = pd.DataFrame(hrows).set_index("model")
hold.round(4).reset_index().to_csv(FORECAST / "holdout_all_models.csv", index=False)
summ = summ.join(hold).sort_values("MAE_mean")
summ.round(4).reset_index().to_csv(FORECAST / "cv_summary.csv", index=False)
best_cv = summ.index[0]
best_hold = hold["holdout_MAE"].idxmin()
print(summ[["MAE_mean", "MAE_sd", "RMSE_mean", "MASE_mean", "holdout_MAE"]].round(1).to_string())
print(f"[07] best by CV mean MAE: {best_cv}; best on 2018 hold-out MAE: {best_hold}")

# paired comparison of fold MAEs against the CV-best model (Wilcoxon signed-rank + paired t), and vs seasonal naive
piv = cv.pivot(index="fold", columns="model", values="MAE")
prow = []
for ref in dict.fromkeys([best_cv, "Seasonal naive"]):
    for m in piv.columns:
        if m == ref:
            continue
        d = (piv[m] - piv[ref]).dropna()
        try:
            w = stats.wilcoxon(d).pvalue if (d != 0).any() else np.nan
        except ValueError:
            w = np.nan
        t = stats.ttest_1samp(d, 0).pvalue if len(d) > 2 else np.nan
        prow.append({"reference": ref, "model": m, "mean_MAE_diff(model-ref)": d.mean(),
                     "folds_ref_better": int((d > 0).sum()), "folds": len(d), "wilcoxon_p": w, "paired_t_p": t})
pair = pd.DataFrame(prow)
pair.round(4).to_csv(FORECAST / "cv_paired_tests.csv", index=False)

# ---- figures
fig, ax = plt.subplots(figsize=(9, 5.5))
s2 = summ.sort_values("MAE_mean", ascending=False)
ax.barh(s2.index, s2["MAE_mean"], xerr=s2["MAE_sd"], color=style.BLUE, ecolor=style.GREY, capsize=3)
ax.set_xlabel("Mean MAE across CV folds (USD, bars = +/-1 SD)"); ax.set_title("Rolling-origin CV: mean MAE by model")
style.save(fig, "cv_mae_by_model.png")

top = list(summ.index[:4]) + (["Seasonal naive"] if "Seasonal naive" not in summ.index[:4] else [])
fig, ax = plt.subplots(figsize=(9, 5))
for m in top:
    ax.plot(piv.index, piv[m], marker="o", label=m)
ax.set_xlabel("Fold (expanding window, later = more training data)"); ax.set_ylabel("MAE (USD)")
ax.set_title("Fold-by-fold MAE of the leading models"); ax.legend(fontsize=9)
style.save(fig, "cv_fold_mae.png")

fig, ax = plt.subplots(figsize=(9, 5))
sh = summ.sort_values("MASE_mean", ascending=False)
ax.barh(sh.index, sh["MASE_mean"], color=style.ORANGE)
ax.axvline(1, color="black", ls="--", lw=1); ax.text(1.01, 0, "MASE = 1 (seasonal naive)", fontsize=9)
ax.set_xlabel("Mean MASE across folds (below 1 beats seasonal naive)"); ax.set_title("MASE by model")
style.save(fig, "cv_mase_by_model.png")

# ---- report section
show = summ.reset_index()[["model", "MAE_mean", "MAE_sd", "RMSE_mean", "MAPE_mean", "sMAPE_mean", "MASE_mean", "MASE_sd", "holdout_MAE", "holdout_RMSE", "holdout_MAPE"]].round(2)
ps = pair[pair.reference == best_cv].round(3)
md = ["", "## Rolling-origin cross-validation (script 07)", "",
      f"- Design: expanding window, minimum training length {MIN_TRAIN} months, horizon {H} months, origin step {STEP} months -> {len(origins)} folds "
      f"(first fold tests {cv.test_start.iloc[0]}, windows overlap, so folds are not independent).",
      "- Models: seasonal naive, naive, SES, Holt-Winters (additive damped = the project's 'Holt-Winters (additive)', additive undamped, multiplicative, "
      "multiplicative-seasonal with damped trend), ETS chosen by AICc among 4 configurations, ARIMA(1,1,1), SARIMA(1,1,1)(0,1,1,12), "
      "SARIMA with a 16-candidate AIC search (p,q,P,Q in {0,1}, d=D=1) re-run inside each fold.",
      "- MASE scales MAE by the in-sample seasonal-naive MAE of the training window (below 1 = better than seasonal naive). MAPE and sMAPE are in %.",
      f"- **Best by mean CV MAE: {best_cv}.  Best on the single 2018 hold-out by MAE: {best_hold}.**", "",
      "### Mean and SD across folds, with the original 2018 hold-out (train 36 / test 12)", md_table(show), "",
      f"### Paired comparison of fold MAE against {best_cv}",
      "Positive difference = the listed model has larger error. Wilcoxon and paired-t p-values use the 7 overlapping folds, so treat them as indicative only; with this few folds the smallest possible two-sided Wilcoxon p is 0.0156.", "",
      md_table(ps), "",
      "### Why 48 months limits SARIMA",
      "- A seasonal period of 12 with D=1 consumes 12 observations for differencing; a 24-month training window leaves only 12 usable points to estimate up to 5 parameters, and at the 36-month origin 24 points.",
      "- Seasonal parameters are identified from only 2-3 repeats of each calendar month; the estimates are unstable and the AIC search order changes between folds (see `data/forecast/cv_sarima_orders.csv`).",
      "- Exponential smoothing and seasonal naive need fewer parameters or none, so they are less exposed to this estimation noise.",
      "- The series itself is also irregular (large Sep/Nov/Dec peaks and a few outlying months), so a conclusion about the best model is tentative: differences between close models are within fold-to-fold variation.", "",
      "Figures: `figures/cv_mae_by_model.png`, `figures/cv_fold_mae.png`, `figures/cv_mase_by_model.png`", ""]
p = REPORTS / "model_accuracy.md"
txt = p.read_text(encoding="utf-8") if p.exists() else ""
txt = txt.split("\n## Rolling-origin cross-validation (script 07)")[0].rstrip("\n") + "\n" + "\n".join(md)
p.write_text(txt, encoding="utf-8")
print("[07] wrote CV outputs and appended to reports/model_accuracy.md")
