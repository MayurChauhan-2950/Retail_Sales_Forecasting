"""Step 6 - Exploratory data analysis charts (Ch10). Saves 10 PNG files into reports/figures/."""
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common import CLEAN, FIGS, monthly_sales

df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date", "Ship Date"])
BLUE, RED, GREY = "#2a6fb0", "#c0392b", "#7f8c8d"
plt.rcParams.update({"axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
                     "grid.alpha": .25, "figure.dpi": 100, "font.size": 10})
saved = []


def save(fig, name):
    fig.tight_layout(); fig.savefig(FIGS / name, dpi=130); plt.close(fig); saved.append(name)


def bar_sales_profit(col, title, name, horizontal=False):
    """Sales and profit side by side for one categorical column."""
    g = df.groupby(col)[["Sales", "Profit"]].sum().sort_values("Sales", ascending=not horizontal)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    g.plot(kind="barh" if horizontal else "bar", ax=ax, color=[BLUE, "#e67e22"], width=.75)
    ax.set_title(title); ax.set_ylabel("" if horizontal else "USD"); ax.set_xlabel("USD" if horizontal else "")
    if not horizontal: plt.setp(ax.get_xticklabels(), rotation=0)
    save(fig, name)


# 1-3 category, region, segment
bar_sales_profit("Category", "Sales and profit by category", "01_sales_by_category.png")
bar_sales_profit("Region", "Sales and profit by region", "02_sales_by_region.png")
bar_sales_profit("Segment", "Sales and profit by customer segment", "03_sales_by_segment.png")

# 4 monthly trend + 12-month rolling mean
m = monthly_sales(df)
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(m.index, m, color=BLUE, marker="o", ms=3, label="monthly sales")
ax.plot(m.index, m.rolling(12).mean(), color=RED, lw=2, label="12-month rolling mean")
ax.set_title("Monthly sales trend"); ax.set_ylabel("USD"); ax.legend()
save(fig, "04_monthly_sales_trend.png")

# 5 top 10 products by sales
top = df.groupby("Product Name")["Sales"].sum().nlargest(10).sort_values()
fig, ax = plt.subplots(figsize=(9, 5))
ax.barh(top.index.str.slice(0, 45), top.values, color=BLUE); ax.set_title("Top 10 products by sales"); ax.set_xlabel("USD")
save(fig, "05_top10_products.png")

# 6 profit vs discount (scatter + average per discount level)
fig, ax = plt.subplots(1, 2, figsize=(12, 4.5))
ax[0].scatter(df["Discount"], df["Profit"], s=6, alpha=.3, color=GREY)
ax[0].set_ylim(-2000, 2000); ax[0].axhline(0, color="black", lw=.8)
ax[0].set_title("Profit vs discount (each dot = order line)"); ax[0].set_xlabel("Discount"); ax[0].set_ylabel("Profit")
avg = df.groupby("Discount")["Profit"].mean()
ax[1].bar(avg.index.astype(str), avg.values, color=[RED if v < 0 else BLUE for v in avg.values])
ax[1].set_title("Average profit by discount level"); ax[1].set_xlabel("Discount"); ax[1].axhline(0, color="black", lw=.8)
plt.setp(ax[1].get_xticklabels(), rotation=45)
save(fig, "06_profit_vs_discount.png")

# 7 heatmap month x year
pv = df.pivot_table(index="Order Month", columns="Order Year", values="Sales", aggfunc="sum")
fig, ax = plt.subplots(figsize=(7, 6))
im = ax.imshow(pv.values, cmap="Blues", aspect="auto"); ax.grid(False)
ax.set_xticks(range(len(pv.columns)), pv.columns); ax.set_yticks(range(12), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
for i in range(pv.shape[0]):
    for j in range(pv.shape[1]):
        ax.text(j, i, f"{pv.values[i, j] / 1000:.0f}k", ha="center", va="center", fontsize=8,
                color="white" if pv.values[i, j] > pv.values.max() * .6 else "black")
ax.set_title("Sales heatmap: month x year (USD thousands)"); fig.colorbar(im, ax=ax, shrink=.8)
save(fig, "07_heatmap_month_year.png")

# 8 sub-category profit (shows loss-makers)
sc = df.groupby("Sub-Category")["Profit"].sum().sort_values()
fig, ax = plt.subplots(figsize=(8, 6))
ax.barh(sc.index, sc.values, color=[RED if v < 0 else BLUE for v in sc.values]); ax.axvline(0, color="black", lw=.8)
ax.set_title("Profit by sub-category (red = loss-making)"); ax.set_xlabel("USD")
save(fig, "08_profit_by_subcategory.png")

# 9 top 10 states by sales
st = df.groupby("State")["Sales"].sum().nlargest(10).sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
ax.barh(st.index, st.values, color=BLUE); ax.set_title("Top 10 states by sales"); ax.set_xlabel("USD")
save(fig, "09_top10_states.png")

# 10 correlation heatmap of numeric columns
cols = ["Sales", "Quantity", "Discount", "Profit", "Ship Days", "Profit Margin"]
cm = df[cols].corr()
fig, ax = plt.subplots(figsize=(6.5, 5.5))
im = ax.imshow(cm, cmap="RdBu_r", vmin=-1, vmax=1); ax.grid(False)
ax.set_xticks(range(len(cols)), cols, rotation=45, ha="right"); ax.set_yticks(range(len(cols)), cols)
for i in range(len(cols)):
    for j in range(len(cols)):
        ax.text(j, i, f"{cm.values[i, j]:.2f}", ha="center", va="center", fontsize=8)
ax.set_title("Correlation of numeric columns"); fig.colorbar(im, ax=ax, shrink=.8)
save(fig, "10_correlation_heatmap.png")

print(f"[06] saved {len(saved)} charts to reports/figures/: " + ", ".join(saved))
