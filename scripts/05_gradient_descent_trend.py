"""Step 5 - Optimisation (Ch7): fit a linear trend  y_hat = w*x + b  to monthly sales
with gradient descent written from scratch, and compare with the closed-form (normal equation) solution.
Loss function: Mean Squared Error  J(w,b) = (1/n) * sum (y_hat - y)^2
Gradients:     dJ/dw = (2/n) * sum (y_hat - y) * x      dJ/db = (2/n) * sum (y_hat - y)
Update rule:   w <- w - lr * dJ/dw ;  b <- b - lr * dJ/db
Outputs: reports/figures/gd_loss_curve.png, gd_trend_fit.png, reports/gradient_descent_report.md"""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import CLEAN, FIGS, REPORTS, monthly_sales, md_table

df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date"])
y_raw = monthly_sales(df).values.astype(float)
x_raw = np.arange(len(y_raw), dtype=float)             # month index 0..n-1
n = len(y_raw)

# Ch6 link: standardise x and y so gradient descent converges quickly with one learning rate
xm, xs, ym, ys = x_raw.mean(), x_raw.std(), y_raw.mean(), y_raw.std()
x, y = (x_raw - xm) / xs, (y_raw - ym) / ys


def gradient_descent(x, y, lr, epochs):
    """Batch gradient descent for simple linear regression; returns w, b and the loss history."""
    w = b = 0.0
    hist = []
    for _ in range(epochs):
        err = (w * x + b) - y
        hist.append(np.mean(err ** 2))                  # cost J(w,b)
        w -= lr * (2 / len(x)) * np.sum(err * x)        # step against the gradient
        b -= lr * (2 / len(x)) * np.sum(err)
    return w, b, np.array(hist)


# main run
LR, EPOCHS = 0.1, 200
w, b, hist = gradient_descent(x, y, LR, EPOCHS)

# closed form (normal equation): theta = (X^T X)^-1 X^T y, solved with np.linalg.solve
X = np.column_stack([x, np.ones(n)])
w_cf, b_cf = np.linalg.solve(X.T @ X, X.T @ y)
slope_np, icpt_np = np.polyfit(x, y, 1)                 # independent check

# convert back to original units: y_raw = ys*(w*(x_raw-xm)/xs + b) + ym
def to_orig(w_, b_):
    slope = ys * w_ / xs
    return slope, ym + ys * b_ - slope * xm
sl_gd, ic_gd = to_orig(w, b)
sl_cf, ic_cf = to_orig(w_cf, b_cf)
mse_gd = np.mean((sl_gd * x_raw + ic_gd - y_raw) ** 2)
mse_cf = np.mean((sl_cf * x_raw + ic_cf - y_raw) ** 2)
mse_gd_scaled, mse_cf_scaled = hist[-1], np.mean((w_cf * x + b_cf - y) ** 2)
r2 = 1 - np.sum((sl_cf * x_raw + ic_cf - y_raw) ** 2) / np.sum((y_raw - y_raw.mean()) ** 2)
conv_epoch = int(np.argmax(hist - mse_cf_scaled < 1e-6))

# learning rate experiment
lrs = [0.001, 0.01, 0.1, 0.5, 1.05]
runs = {lr: gradient_descent(x, y, lr, EPOCHS)[2] for lr in lrs}

# --- plots
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ax[0].plot(hist, color="#1f77b4"); ax[0].axhline(mse_cf_scaled, color="#d62728", ls="--", label="closed-form MSE")
ax[0].set_title(f"Loss curve (lr={LR})"); ax[0].set_xlabel("epoch"); ax[0].set_ylabel("MSE (scaled units)"); ax[0].legend()
for lr, h in runs.items():
    ax[1].plot(np.clip(h, 0, 3), label=f"lr={lr}")
ax[1].set_title("Effect of learning rate (clipped at 3)"); ax[1].set_xlabel("epoch"); ax[1].legend()
for a in ax: a.grid(alpha=.3)
fig.tight_layout(); fig.savefig(FIGS / "gd_loss_curve.png", dpi=130); plt.close(fig)

fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(x_raw, y_raw, "o-", color="#888", label="monthly sales")
ax.plot(x_raw, sl_gd * x_raw + ic_gd, color="#d62728", lw=2, label="gradient descent line")
ax.plot(x_raw, sl_cf * x_raw + ic_cf, color="black", ls=":", lw=2, label="closed-form line")
ax.set_xlabel("month index"); ax.set_ylabel("sales ($)"); ax.set_title("Linear trend fitted two ways"); ax.legend(); ax.grid(alpha=.3)
fig.tight_layout(); fig.savefig(FIGS / "gd_trend_fit.png", dpi=130); plt.close(fig)

# --- report
cmp = pd.DataFrame({
    "method": ["Gradient descent", "Closed form (normal equation)", "np.polyfit (check)"],
    "slope_$_per_month": [sl_gd, sl_cf, ys * slope_np / xs],
    "intercept_$": [ic_gd, ic_cf, ym + ys * icpt_np - ys * slope_np / xs * xm],
    "MSE_original_units": [mse_gd, mse_cf, mse_cf],
})
lr_tab = pd.DataFrame({"learning_rate": lrs, "final_loss": [runs[l][-1] for l in lrs],
                       "outcome": ["converging slowly" if runs[l][-1] > mse_cf_scaled + 1e-3 and runs[l][-1] < 1
                                   else "converged" if runs[l][-1] <= mse_cf_scaled + 1e-3 else "DIVERGED" for l in lrs]})
md = ["# Optimisation: Gradient Descent vs Closed Form (Ch7)", "",
      f"Data: {n} monthly sales totals; model `sales = slope * month_index + intercept`.",
      f"Both variables standardised first (z-score), learning rate {LR}, {EPOCHS} epochs, starting from w=0, b=0.", "",
      "## Parameters and MSE", md_table(cmp), "",
      f"- Scaled-space MSE: gradient descent {mse_gd_scaled:.6f} vs closed form {mse_cf_scaled:.6f} "
      f"(difference {abs(mse_gd_scaled - mse_cf_scaled):.2e})",
      f"- Loss within 1e-6 of the optimum after about {conv_epoch} epochs",
      f"- Trend line R^2 = {r2:.3f}; RMSE = {np.sqrt(mse_cf):,.2f} $ (the linear trend alone ignores seasonality)",
      f"- Interpretation: sales grow by about ${sl_cf:,.2f} per month on average.", "",
      "## Learning-rate experiment (final loss after 200 epochs, scaled data)", md_table(lr_tab), "",
      "A tiny rate converges slowly; a suitable rate converges quickly; too large a rate overshoots and diverges.", "",
      "Figures: `figures/gd_loss_curve.png`, `figures/gd_trend_fit.png`", ""]
(REPORTS / "gradient_descent_report.md").write_text("\n".join(md), encoding="utf-8")
print(f"[05] GD slope={sl_gd:.4f} closed-form slope={sl_cf:.4f}; MSE GD={mse_gd:,.2f} closed={mse_cf:,.2f}; converged ~epoch {conv_epoch}")
