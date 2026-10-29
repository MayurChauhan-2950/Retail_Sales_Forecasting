"""Step 2 - Cleaning and transformation (Ch6).
Fixes: stray rows, duplicates, text consistency, data types, dates, missing values, invalid values.
Then demonstrates scaling (min-max, z-score, log) and encoding (one-hot, label, target).
Outputs: data/clean/superstore_clean.csv(+parquet), data/clean/superstore_ml_ready_demo.csv,
         data/clean/cleaning_log.csv, reports/cleaning_log.md"""
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold
from sklearn.preprocessing import LabelEncoder, MinMaxScaler, StandardScaler
from common import read_raw, parse_dates, md_table, CLEAN, REPORTS

df = read_raw()
df.columns = df.columns.str.strip()
rows_before = len(df)
log = []


def step(name, rule, affected, action):
    """Record one cleaning step: what was checked, how many rows/cells were affected, what we did."""
    log.append({"step": name, "rule": rule, "rows_or_cells_affected": int(affected), "action": action, "rows_after": len(df)})


# --- 1. stray rows: all business columns empty (e.g. other Excel sheets appended to the CSV)
biz = [c for c in df.columns if c not in ("Row ID", "Order ID")]
mask = df[biz].isna().all(axis=1)
k = mask.sum(); df = df[~mask].copy()
step("1 stray rows", "all columns except Row ID/Order ID empty", k, "dropped")

# --- 2. duplicates
k = df.duplicated().sum(); df = df.drop_duplicates()
step("2 duplicates", "fully identical rows", k, "kept first, dropped rest")
k = df.duplicated(subset=["Row ID"]).sum(); df = df.drop_duplicates(subset=["Row ID"])
step("2b duplicate Row ID", "same Row ID twice", k, "kept first")

# --- 3. text consistency: trim, collapse spaces, standard casing
text_cols = ["Ship Mode", "Segment", "Country", "City", "State", "Region", "Category", "Sub-Category",
             "Customer Name", "Product Name"]
changed = 0
for c in text_cols:
    new = df[c].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    if c in ("Ship Mode", "Segment", "Region", "Category", "Sub-Category"):
        new = new.str.title()
    changed += int((new.fillna("") != df[c].fillna("")).sum())
    df[c] = new
step("3 text consistency", "strip/collapse spaces; Title Case for category-like columns", changed, "standardised")

# --- 4. data types
df["Row ID"] = pd.to_numeric(df["Row ID"], errors="coerce")
for c in ("Sales", "Quantity", "Discount", "Profit"):
    df[c] = pd.to_numeric(df[c], errors="coerce")
od, sd = parse_dates(df["Order Date"]), parse_dates(df["Ship Date"])
bad = int(od.isna().sum() + sd.isna().sum())
df["Order Date"], df["Ship Date"] = od, sd
step("4 data types", "Row ID/Sales/Quantity/Discount/Profit -> numeric; dates parsed from mixed formats",
     bad, f"{bad} values could not be parsed -> NaT (handled in step 5)")

# --- 5. missing values
# 5a. critical fields missing -> row unusable
crit = ["Row ID", "Order ID", "Order Date", "Ship Date", "Customer ID", "Product ID", "Sales", "Quantity", "Profit"]
mask = df[crit].isna().any(axis=1); k = mask.sum(); df = df[~mask].copy()
step("5a missing critical fields", f"any of {len(crit)} key fields missing", k, "dropped")
# 5b. Discount missing -> assume no discount (0)
k = df["Discount"].isna().sum(); df["Discount"] = df["Discount"].fillna(0.0)
step("5b missing Discount", "Discount empty", k, "imputed with 0 (no discount)")
# 5c. Postal Code: text with 5 digits; fill from same City+State mode, else 'Unknown'
pc = df["Postal Code"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(5)
pc = pc.where(df["Postal Code"].notna())
df["Postal Code"] = pc
k = df["Postal Code"].isna().sum()
mode_pc = df.groupby(["City", "State"])["Postal Code"].agg(lambda s: s.mode().iloc[0] if s.notna().any() else pd.NA)
fill = pd.Series(list(zip(df["City"], df["State"])), index=df.index).map(mode_pc)
df["Postal Code"] = df["Postal Code"].fillna(fill).fillna("Unknown")
left = (df["Postal Code"] == "Unknown").sum()
step("5c missing Postal Code", "Postal Code empty", k, f"filled with mode of same City+State; {left} still 'Unknown'; stored as 5-char text")
# any other text column still missing
other = df[text_cols].isna().sum().sum()
for c in text_cols:
    df[c] = df[c].fillna("Unknown")
step("5d other missing text", "category-like columns empty", other, "filled with 'Unknown'")

# --- 6. invalid values
mask = (df["Quantity"] <= 0) | (df["Sales"] <= 0); k = mask.sum(); df = df[~mask].copy()
step("6a invalid Quantity/Sales", "Quantity <= 0 or Sales <= 0", k, "dropped")
mask = (df["Discount"] < 0) | (df["Discount"] > 1); k = mask.sum()
df["Discount"] = df["Discount"].clip(0, 1)
step("6b Discount range", "Discount outside 0..1", k, "clipped to 0..1")
mask = df["Ship Date"] < df["Order Date"]; k = mask.sum(); df = df[~mask].copy()
step("6c Ship before Order", "Ship Date < Order Date", k, "dropped")
df["Quantity"] = df["Quantity"].astype(int)
df["Row ID"] = df["Row ID"].astype(int)

# --- 7. consistency checks (reported, not changed)
c1 = (df.groupby("Customer ID")["Customer Name"].nunique() > 1).sum()
c2 = (df.groupby("Product ID")["Product Name"].nunique() > 1).sum()
step("7a Customer ID -> name", "one ID should have one name", c1, "checked (no change)")
step("7b Product ID -> name", "one ID should have one name", c2, "checked; star schema keeps first name per Product ID")
out_hi = (df["Sales"] > df["Sales"].quantile(.75) + 1.5 * (df["Sales"].quantile(.75) - df["Sales"].quantile(.25))).sum()
step("7c Sales outliers", "above Q3 + 1.5*IQR", out_hi, "kept (genuine large orders); flagged only")

# --- 8. derived columns
df["Order Year"] = df["Order Date"].dt.year
df["Order Month"] = df["Order Date"].dt.month
df["Order YearMonth"] = df["Order Date"].dt.to_period("M").astype(str)
df["Ship Days"] = (df["Ship Date"] - df["Order Date"]).dt.days
df["Profit Margin"] = (df["Profit"] / df["Sales"]).round(4)
df["Unit Price"] = (df["Sales"] / df["Quantity"]).round(4)
step("8 derived columns", "Order Year/Month/YearMonth, Ship Days, Profit Margin, Unit Price", len(df), "added")

df = df.sort_values(["Order Date", "Row ID"]).reset_index(drop=True)
assert df[["Order Date", "Sales", "Quantity"]].notna().all().all()
df.to_csv(CLEAN / "superstore_clean.csv", index=False)
df.to_parquet(CLEAN / "superstore_clean.parquet", index=False)

# ---------------- Scaling demonstration ----------------
num = ["Sales", "Quantity", "Discount", "Profit", "Ship Days"]
ml = pd.DataFrame(index=df.index)
mn, mx = df[num].min(), df[num].max()
minmax = (df[num] - mn) / (mx - mn)                      # min-max: (x-min)/(max-min) -> [0,1]
zs = (df[num] - df[num].mean()) / df[num].std(ddof=0)    # standardisation: (x-mean)/std
ok_mm = np.allclose(minmax, MinMaxScaler().fit_transform(df[num]))
ok_z = np.allclose(zs, StandardScaler().fit_transform(df[num]))
for c in num:
    ml[f"{c}_minmax"] = minmax[c].round(6)
    ml[f"{c}_zscore"] = zs[c].round(6)
ml["Sales_log1p"] = np.log1p(df["Sales"]).round(6)       # log transform for the skewed Sales column
skew_before, skew_after = df["Sales"].skew(), np.log1p(df["Sales"]).skew()

# ---------------- Encoding demonstration ----------------
onehot = pd.get_dummies(df[["Segment", "Ship Mode", "Category", "Region"]], dtype=int)   # one-hot (nominal)
le = LabelEncoder()
ml["SubCategory_label"] = le.fit_transform(df["Sub-Category"])                           # label (ordinal ids)
# target encoding of State = smoothed mean Profit, computed out-of-fold to avoid target leakage
glob, m = df["Profit"].mean(), 20
te = pd.Series(np.nan, index=df.index)
for tr, va in KFold(5, shuffle=True, random_state=42).split(df):
    g = df.iloc[tr].groupby("State")["Profit"].agg(["mean", "count"])
    sm = (g["count"] * g["mean"] + m * glob) / (g["count"] + m)
    te.iloc[va] = df.iloc[va]["State"].map(sm).fillna(glob).values
ml["State_target_enc"] = te.round(4)
ml = pd.concat([df[["Row ID"]], ml, onehot], axis=1)
ml.to_csv(CLEAN / "superstore_ml_ready_demo.csv", index=False)

# ---------------- Write logs ----------------
logdf = pd.DataFrame(log)
logdf.to_csv(CLEAN / "cleaning_log.csv", index=False)
rows_after = len(df)
md = ["# Cleaning and Transformation Log", "",
      f"- Rows before cleaning: **{rows_before:,}**", f"- Rows after cleaning: **{rows_after:,}**",
      f"- Rows removed: **{rows_before - rows_after:,}**", "", "## Every fix with counts", md_table(logdf), "",
      "## Scaling demonstration (Ch6)",
      md_table(pd.DataFrame({"min": mn, "max": mx, "mean": df[num].mean(), "std": df[num].std(ddof=0)}), index=True)
      .replace("| index |", "| column |"), "",
      f"- Min-max formula (x-min)/(max-min) matches sklearn MinMaxScaler: **{ok_mm}**",
      f"- Z-score formula (x-mean)/std matches sklearn StandardScaler: **{ok_z}**",
      f"- Skewness of Sales: {skew_before:.2f} before, {skew_after:.2f} after log1p transform", "",
      "## Encoding demonstration (Ch6)",
      f"- One-hot (Segment, Ship Mode, Category, Region): {onehot.shape[1]} dummy columns",
      f"- Label encoding of Sub-Category: {len(le.classes_)} classes -> 0..{len(le.classes_) - 1}",
      "- Target encoding of State: smoothed mean Profit (smoothing m=20), computed with 5-fold out-of-fold to avoid leakage",
      f"- ML-ready demo file: `data/clean/superstore_ml_ready_demo.csv` ({ml.shape[0]:,} rows x {ml.shape[1]} columns)", ""]
(REPORTS / "cleaning_log.md").write_text("\n".join(md), encoding="utf-8")
print(f"[02] rows before={rows_before:,} after={rows_after:,}")
print(logdf[["step", "rows_or_cells_affected", "rows_after"]].to_string(index=False))
