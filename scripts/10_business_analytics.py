"""Step 10 - Business analytics layer (Ch10).
Discount vs profit bands, sub-category and product profit rankings, Pareto/ABC of products and customers,
RFM + K-means customer segmentation, seasonality index, state/city profit tables.
Tables -> data/analytics/*.csv ; charts -> reports/figures/ba_*.png"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from common import CLEAN, ROOT, FIGS
import style

OUT = ROOT / "data" / "analytics"
OUT.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(CLEAN / "superstore_clean.csv", parse_dates=["Order Date"])
money = lambda ax, axis="y": (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(
    plt.FuncFormatter(lambda v, _: f"${v/1000:,.0f}k" if abs(v) >= 1000 else f"${v:,.0f}"))


def margin(g): return g["profit"] / g["sales"] * 100


# ---------- a) discount bands
bins = [-0.001, 0, 0.1, 0.2, 0.3, 0.4, 0.5, 1.0]
labels = ["0% (none)", "0-10%", "10-20%", "20-30%", "30-40%", "40-50%", "above 50%"]
df["discount_band"] = pd.cut(df["Discount"], bins=bins, labels=labels)
db = df.groupby("discount_band", observed=True).agg(order_lines=("Sales", "size"), sales=("Sales", "sum"), profit=("Profit", "sum"),
                                                    avg_profit_per_line=("Profit", "mean"), loss_making_lines=("Profit", lambda s: (s < 0).sum())).reset_index()
db["margin_pct"] = margin(db); db["pct_lines_loss_making"] = db.loss_making_lines / db.order_lines * 100
db.round(2).to_csv(OUT / "discount_bands.csv", index=False)
fig, ax = plt.subplots(figsize=(9, 5))
cols = [style.GREEN if v >= 0 else style.RED for v in db.margin_pct]
b = ax.bar(db.discount_band.astype(str), db.margin_pct, color=cols)
for r, n in zip(b, db.order_lines):
    ax.annotate(f"n={n:,}", (r.get_x() + r.get_width() / 2, r.get_height()), ha="center",
                va="bottom" if r.get_height() >= 0 else "top", fontsize=9)
ax.axhline(0, color="black", lw=.8); ax.set_xlabel("Discount band"); ax.set_ylabel("Profit margin (% of sales)")
ax.set_title("Profit margin falls below zero once discounts exceed 20%")
style.save(fig, "ba_discount_bands.png")

# ---------- b) sub-category and product ranking
sc = df.groupby(["Category", "Sub-Category"]).agg(order_lines=("Sales", "size"), sales=("Sales", "sum"), profit=("Profit", "sum"),
                                                 avg_discount=("Discount", "mean")).reset_index()
sc["margin_pct"] = margin(sc); sc = sc.sort_values("profit", ascending=False)
sc.round(2).to_csv(OUT / "subcategory_profit.csv", index=False)
fig, ax = plt.subplots(figsize=(9, 6))
s2 = sc.sort_values("profit")
ax.barh(s2["Sub-Category"], s2.profit, color=[style.GREEN if v >= 0 else style.RED for v in s2.profit])
ax.set_xlabel("Total profit (USD)"); ax.set_title("Profit by sub-category"); money(ax, "x")
style.save(fig, "ba_subcategory_profit.png")

pr = df.groupby(["Product ID"]).agg(product=("Product Name", "first"), category=("Category", "first"), sub_category=("Sub-Category", "first"),
                                    order_lines=("Sales", "size"), units=("Quantity", "sum"), sales=("Sales", "sum"), profit=("Profit", "sum"),
                                    avg_discount=("Discount", "mean")).reset_index()
pr["margin_pct"] = margin(pr); pr = pr.sort_values("profit", ascending=False)
pr.round(2).to_csv(OUT / "product_profit_all.csv", index=False)
tb = pd.concat([pr.head(10).assign(rank_group="Top 10"), pr.tail(10).assign(rank_group="Bottom 10")])
tb.round(2).to_csv(OUT / "top_bottom_products.csv", index=False)
fig, ax = plt.subplots(figsize=(10, 6.5))
t = tb.iloc[::-1]
ax.barh([p[:42] + ("..." if len(p) > 42 else "") for p in t["product"]], t.profit, color=[style.GREEN if v >= 0 else style.RED for v in t.profit])
ax.set_xlabel("Total profit (USD)"); ax.set_title("Top 10 and bottom 10 products by profit"); money(ax, "x")
style.save(fig, "ba_top_bottom_products.png")

# ---------- c) Pareto / ABC
def pareto(g, key, name):
    g = g.sort_values("sales", ascending=False).reset_index(drop=True)
    g["cum_sales_pct"] = g.sales.cumsum() / g.sales.sum() * 100
    g["rank_pct"] = (g.index + 1) / len(g) * 100
    g["abc_class"] = np.where(g.cum_sales_pct.shift(fill_value=0) < 80, "A", np.where(g.cum_sales_pct.shift(fill_value=0) < 95, "B", "C"))
    return g
pp = pareto(pr[["Product ID", "product", "sales", "profit"]], "Product ID", "product")
cu = df.groupby(["Customer ID", "Customer Name"]).agg(sales=("Sales", "sum"), profit=("Profit", "sum"), orders=("Order ID", "nunique")).reset_index()
pc = pareto(cu, "Customer ID", "customer")
pp.round(2).to_csv(OUT / "pareto_products.csv", index=False); pc.round(2).to_csv(OUT / "pareto_customers.csv", index=False)
abc = []
for nm, g in [("Products", pp), ("Customers", pc)]:
    for c, gg in g.groupby("abc_class"):
        abc.append({"entity": nm, "class": c, "count": len(gg), "pct_of_entities": len(gg) / len(g) * 100,
                    "sales": gg.sales.sum(), "pct_of_sales": gg.sales.sum() / g.sales.sum() * 100,
                    "profit": gg.profit.sum(), "pct_of_profit": gg.profit.sum() / g.profit.sum() * 100})
abc = pd.DataFrame(abc); abc.round(2).to_csv(OUT / "abc_summary.csv", index=False)
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
for ax, g, nm in zip(axs, [pp, pc], ["Products", "Customers"]):
    ax.plot(g.rank_pct, g.cum_sales_pct, color=style.BLUE, lw=2)
    ax.axhline(80, color=style.GREY, ls="--", lw=1); ax.axhline(95, color=style.GREY, ls=":", lw=1)
    n80 = (g.abc_class == "A").sum()
    ax.axvline(n80 / len(g) * 100, color=style.ORANGE, lw=1)
    ax.set_title(f"{nm}: top {n80/len(g)*100:.0f}% of items give 80% of sales"); ax.set_xlabel(f"Cumulative % of {nm.lower()} (ranked by sales)")
axs[0].set_ylabel("Cumulative % of sales")
style.save(fig, "ba_pareto_abc.png")

# ---------- d) RFM + K-means
snap = df["Order Date"].max() + pd.Timedelta(days=1)
rfm = df.groupby("Customer ID").agg(recency_days=("Order Date", lambda s: (snap - s.max()).days), frequency=("Order ID", "nunique"),
                                    monetary=("Sales", "sum"), profit=("Profit", "sum")).reset_index()
X = StandardScaler().fit_transform(np.log1p(rfm[["recency_days", "frequency", "monetary"]]))
ksel = []
for k in range(2, 9):
    km = KMeans(n_clusters=k, n_init=20, random_state=42).fit(X)
    ksel.append({"k": k, "inertia": km.inertia_, "silhouette": silhouette_score(X, km.labels_)})
ksel = pd.DataFrame(ksel); ksel.round(4).to_csv(OUT / "rfm_k_selection.csv", index=False)
K = 4   # silhouette is highest at k=2 (too coarse for marketing); among k>=3 k=3 and k=4 are tied (0.2546 vs 0.2537), k=4 separates recency from value
SIL_BEST_K = int(ksel.sort_values("silhouette", ascending=False).iloc[0].k)
km = KMeans(n_clusters=K, n_init=20, random_state=42).fit(X)
rfm["cluster"] = km.labels_
prof = rfm.groupby("cluster").agg(customers=("Customer ID", "size"), avg_recency_days=("recency_days", "mean"), avg_orders=("frequency", "mean"),
                                  avg_sales=("monetary", "mean"), total_sales=("monetary", "sum"), total_profit=("profit", "sum")).reset_index()
prof["pct_customers"] = prof.customers / len(rfm) * 100; prof["pct_sales"] = prof.total_sales / prof.total_sales.sum() * 100
# name segments from fixed tiers: recency (<=60 days Active, <=180 Cooling, else Lapsed) and average spend per customer
# (>= overall customer mean = high-value, >= $1,000 mid-value, else low-value)
MEAN_M = rfm.monetary.mean()
def name_seg(r):
    rec = "Active" if r.avg_recency_days <= 60 else "Cooling" if r.avg_recency_days <= 180 else "Lapsed"
    val = "high-value" if r.avg_sales >= MEAN_M else "mid-value" if r.avg_sales >= 1000 else "low-value"
    return f"{rec} {val}"
prof["segment_name"] = prof.apply(name_seg, axis=1)
prof = prof.sort_values("total_sales", ascending=False)
rfm = rfm.merge(prof[["cluster", "segment_name"]], on="cluster")
rfm.round(2).to_csv(OUT / "rfm_customers.csv", index=False); prof.round(2).to_csv(OUT / "rfm_segment_profile.csv", index=False)
fig, axs = plt.subplots(1, 2, figsize=(11, 4.5))
axs[0].plot(ksel.k, ksel.inertia, marker="o", color=style.BLUE); axs[0].set_xlabel("Number of clusters k"); axs[0].set_ylabel("Within-cluster sum of squares")
axs[0].set_title("Elbow plot")
axs[1].plot(ksel.k, ksel.silhouette, marker="o", color=style.ORANGE); axs[1].axvline(K, color=style.GREY, ls="--")
axs[1].set_xlabel("Number of clusters k"); axs[1].set_ylabel("Silhouette score"); axs[1].set_title(f"Silhouette (chosen k = {K})")
style.save(fig, "ba_rfm_k_selection.png")
fig, axs = plt.subplots(1, 2, figsize=(12, 4.8))
lab = [f"{n.split(' (')[0]}\n(cluster {c})" for n, c in zip(prof.segment_name, prof.cluster)]
axs[0].bar(lab, prof.customers, color=style.PALETTE[:len(prof)]); axs[0].set_ylabel("Customers"); axs[0].set_title("Customers per RFM segment")
axs[1].bar(lab, prof.total_sales, color=style.PALETTE[:len(prof)]); axs[1].set_ylabel("Total sales (USD)"); axs[1].set_title("Sales per RFM segment"); money(axs[1])
for a in axs: a.tick_params(axis="x", labelsize=8)
style.save(fig, "ba_rfm_segments.png")
fig, ax = plt.subplots(figsize=(8, 5.5))
for (c, n), col in zip(prof[["cluster", "segment_name"]].itertuples(index=False), style.PALETTE):
    g = rfm[rfm.cluster == c]
    ax.scatter(g.recency_days, g.monetary, s=14, alpha=.6, color=col, label=n)
ax.set_yscale("log"); ax.set_xlabel("Recency (days since last order)"); ax.set_ylabel("Total sales (USD, log scale)")
ax.set_title("RFM clusters: recency vs spend"); ax.legend(fontsize=8)
style.save(fig, "ba_rfm_scatter.png")

# ---------- e) seasonality index (year-normalised: month sales / that year's mean month, averaged over 4 years)
m = df.set_index("Order Date")["Sales"].resample("MS").sum().to_frame("sales")
m["year"], m["month"] = m.index.year, m.index.month
m["ratio"] = m.sales / m.groupby("year").sales.transform("mean")
si = m.groupby("month").agg(seasonality_index=("ratio", "mean"), sd=("ratio", "std"), avg_sales=("sales", "mean")).reset_index()
si["month_name"] = pd.to_datetime(si.month, format="%m").dt.strftime("%b")
si["seasonality_index"] *= 100; si["sd"] *= 100
si.round(2).to_csv(OUT / "seasonality_index.csv", index=False)
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.bar(si.month_name, si.seasonality_index, yerr=si.sd, color=[style.ORANGE if v > 100 else style.BLUE for v in si.seasonality_index], ecolor=style.GREY, capsize=3)
ax.axhline(100, color="black", lw=1); ax.set_ylabel("Seasonality index (100 = average month of the year)"); ax.set_xlabel("Month")
ax.set_title("Seasonality index by calendar month (bars = SD across 4 years)")
style.save(fig, "ba_seasonality_index.png")

# ---------- f) state / city profit tables
stt = df.groupby(["Region", "State"]).agg(orders=("Order ID", "nunique"), customers=("Customer ID", "nunique"), sales=("Sales", "sum"), profit=("Profit", "sum"),
                                         avg_discount=("Discount", "mean")).reset_index()
stt["margin_pct"] = margin(stt); stt = stt.sort_values("profit", ascending=False)
stt.round(2).to_csv(OUT / "state_profit_map.csv", index=False)
cty = df.groupby(["State", "City"]).agg(orders=("Order ID", "nunique"), sales=("Sales", "sum"), profit=("Profit", "sum")).reset_index()
cty["margin_pct"] = margin(cty); cty = cty.sort_values("profit", ascending=False)
cty.round(2).to_csv(OUT / "city_profit.csv", index=False)
fig, ax = plt.subplots(figsize=(9, 7))
t = pd.concat([stt.head(10), stt.tail(10)]).iloc[::-1]
ax.barh(t.State, t.profit, color=[style.GREEN if v >= 0 else style.RED for v in t.profit])
ax.set_xlabel("Total profit (USD)"); ax.set_title("Ten most and ten least profitable states"); money(ax, "x")
style.save(fig, "ba_state_profit.png")

print("[10] discount bands:\n", db[["discount_band", "order_lines", "margin_pct"]].round(2).to_string(index=False))
print(f"[10] RFM k={K}; silhouettes:", ksel.silhouette.round(3).tolist())
print(prof[["cluster", "segment_name", "customers", "pct_sales"]].round(1).to_string(index=False))
print("[10] wrote data/analytics/*.csv and reports/figures/ba_*.png")
