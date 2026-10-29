import math, os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "reports", "figures")
OUT = os.path.join(ROOT, "presentation", "Retail_Sales_Forecasting_Final.pptx")
NAVY = RGBColor(0x1F, 0x2A, 0x44); TEAL = RGBColor(0x1B, 0x7F, 0x8C)
GREY = RGBColor(0x55, 0x5B, 0x66); LIGHT = RGBColor(0xEE, 0xF2, 0xF6)
AMBER = RGBColor(0xB4, 0x5F, 0x06); WHITE = RGBColor(255, 255, 255)
FONT = "Calibri"
prs = Presentation(); prs.slide_width = Inches(13.333); prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
warnings = []


def fit_check(text_paras, w_in, h_in, pt, tag):
    cpl = max(1, int((w_in - 0.2) * 72 / (pt * 0.53)))
    lines = sum(max(1, math.ceil(len(t) / cpl)) for t in text_paras)
    need = lines * pt * 1.3 / 72 + 0.1 + 0.07 * len(text_paras)
    if need > h_in:
        warnings.append("OVERFLOW %s: need %.2fin > %.2fin" % (tag, need, h_in))


def tb(s, x, y, w, h, paras, pt=16, color=GREY, bold=False, bullets=False, align=None, tag=""):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True
    paras = [paras] if isinstance(paras, str) else paras
    fit_check([("- " if bullets else "") + p for p in paras], w, h, pt, tag)
    for i, t in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run(); r.text = ("• " if bullets else "") + t
        r.font.size = Pt(pt); r.font.name = FONT; r.font.bold = bold; r.font.color.rgb = color
        p.space_after = Pt(5)
        if align: p.alignment = align
    return box


def rect(s, x, y, w, h, fill):
    sh = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    sh.shadow.inherit = False
    return sh


def card(s, x, y, w, h, text, pt=14, fill=LIGHT, color=NAVY, bold=False, tag=""):
    sh = rect(s, x, y, w, h, fill)
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    lines = text if isinstance(text, list) else [text]
    fit_check(lines, w, h, pt, tag or lines[0][:20])
    for i, t in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = t; r.font.size = Pt(pt); r.font.name = FONT
        r.font.color.rgb = color; r.font.bold = bold if i == 0 else False


def pic(s, name, x, y, w, h):
    iw, ih = Image.open(os.path.join(FIG, name)).size
    sc = min(w / iw, h / ih); pw, ph = iw * sc, ih * sc
    s.shapes.add_picture(os.path.join(FIG, name), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))


def table(s, x, y, w, rows, colw, pt=12, rh=0.36, hl=None):
    shp = s.shapes.add_table(len(rows), len(rows[0]), Inches(x), Inches(y), Inches(w), Inches(rh * len(rows)))
    t = shp.table
    for j, cw in enumerate(colw): t.columns[j].width = Inches(cw)
    for i, row in enumerate(rows):
        t.rows[i].height = Inches(rh)
        for j, v in enumerate(row):
            c = t.cell(i, j); c.text = str(v)
            c.margin_left = c.margin_right = Inches(0.06); c.margin_top = c.margin_bottom = Inches(0.02)
            cpl = int((colw[j] - 0.12) * 72 / (pt * 0.53))
            if len(str(v)) > cpl: warnings.append("TABLE cell wrap: %s col %d (cpl %d)" % (v, j, cpl))
            p = c.text_frame.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            f = p.runs[0].font; f.size = Pt(pt); f.name = FONT
            c.fill.solid()
            if i == 0:
                c.fill.fore_color.rgb = NAVY; f.color.rgb = WHITE; f.bold = True
            else:
                c.fill.fore_color.rgb = RGBColor(0xDD, 0xEF, 0xF1) if hl and i in hl else (LIGHT if i % 2 else WHITE)
                f.color.rgb = NAVY; f.bold = bool(hl and i in hl)


n = [0]


def slide(title, notes):
    s = prs.slides.add_slide(BLANK); n[0] += 1
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.05))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    tb(s, 0.5, 0.15, 12.3, 0.8, title, pt=28, color=WHITE, bold=True, tag="title " + title[:20])
    tb(s, 0.5, 7.05, 9, 0.35, "Mayur Chauhan  |  Enrollment No.: [to be added]  |  DSC Individual Project", pt=10, color=GREY, tag="foot")
    tb(s, 12.0, 7.05, 0.8, 0.35, str(n[0]), pt=10, color=GREY, align=PP_ALIGN.RIGHT, tag="num")
    s.notes_slide.notes_text_frame.text = notes
    return s


def takeaway(s, text, y=6.4):
    card(s, 0.5, y, 12.3, 0.55, text, pt=14, fill=TEAL, color=WHITE, tag="takeaway " + text[:15])


# 1 Title
s = prs.slides.add_slide(BLANK); n[0] += 1
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
tb(s, 0.8, 1.6, 11.7, 2.2, "Retail Sales Forecasting: ARIMA, SARIMA and Holt-Winters Compared with Rolling-Origin Validation", pt=36, color=WHITE, bold=True, tag="t1")
tb(s, 0.8, 4.2, 11.7, 1.9, ["Mayur Chauhan  |  Enrollment No.: [to be added]",
                            "Data Science (DSC) - Individual Project",
                            "L.J. Institute of Engineering and Technology"], pt=20, color=RGBColor(0xCF, 0xE3, 0xE8), tag="t1b")
s.notes_slide.notes_text_frame.text = ("Introduce yourself and the project: forecasting monthly retail sales on the public Sample Superstore data, "
    "comparing Holt-Winters, ARIMA and SARIMA honestly. Mention that the analysis, forecasting and data engineering are complete, and that the Power BI dashboard is the one pending part, shown as a plan.")

# 2 Problem
s = slide("Problem and objectives", "Managers need next-month and next-year sales estimates, but monthly sales swing strongly with the season. The question is which method predicts best on this data. Walk through the objectives; the final one, the dashboard, is still pending and is shown later as a plan only.")
card(s, 0.5, 1.35, 12.3, 1.1, "Which forecasting method predicts monthly retail sales best, and how reliable is the 2019 forecast?", pt=22, fill=LIGHT, bold=True, tag="q")
tb(s, 0.5, 2.7, 12.3, 3.6, [
    "Profile and clean the raw data, and measure data quality",
    "Build an ETL pipeline and a star-schema warehouse",
    "Explore the data: seasonality, discounts, concentration, customer value",
    "Compare Holt-Winters, ARIMA and SARIMA with a hold-out and rolling-origin cross-validation",
    "Check residual diagnostics and produce a 2019 forecast with prediction intervals",
    "Plan an interactive Power BI dashboard (build pending)"], pt=18, bullets=True, tag="obj")
takeaway(s, "Scope: 48 monthly points, Jan 2015 to Dec 2018, so conclusions are deliberately cautious.")

# 3 Data and cleaning
s = slide("Data and cleaning", "The data is the real public Sample Superstore. The copy we downloaded had 806 stray empty rows appended from other Excel sheets, which is why the raw file has 10,800 rows. Cleaning removed them and left the 9,994 genuine order lines. The only real defect was 11 missing postal codes. The 1,167 large sales outliers were kept because they are genuine large orders. Totals: sales 2,297,201 and profit 286,397, a 12.5 percent margin.")
for i, (a, b) in enumerate([("9,994", "order lines"), ("793", "customers"), ("1,862", "products"), ("2,297,201", "total sales"), ("286,397", "profit (12.5% margin)")]):
    card(s, 0.5 + i * 2.5, 1.35, 2.3, 1.3, [a, b], pt=14, bold=True, tag="kpi " + a)
tb(s, 0.5, 2.95, 12.3, 3.3, [
    "Source: public Sample Superstore, orders from 2015-01-03 to 2018-12-30",
    "Raw file 10,800 rows, cleaned 9,994 rows; 806 stray empty rows removed",
    "0 true duplicates and no other missing values after that; 11 missing Postal Codes set to 'Unknown'",
    "Text standardised (32 values), dates parsed, Postal Code stored as text",
    "1,167 Sales outliers flagged but kept as genuine large orders",
    "Yearly sales: 2015 484,247; 2016 470,532; 2017 609,206; 2018 733,215"], pt=16, bullets=True, tag="data")
takeaway(s, "Honest note: the raw defects were mostly the appended stray rows, not messy real orders.")

# 4 DQ
s = slide("Data quality: 99.46% overall", "The scorecard applies 17 pass or fail rules. The overall unweighted mean is 99.46 percent. Completeness is lowered by the raw-data rule that shows the 806 stray rows, which is what cleaning fixed. Consistency is below 100 percent because 32 Product IDs carry more than one product name; the star schema keeps the first name. Also mention that all 9 of 9 reconciliation checks pass, so totals are preserved from raw to curated.")
table(s, 0.5, 1.35, 6.2, [["Dimension", "Mean score %"], ["Completeness", "97.51"], ["Consistency", "99.66"], ["Referential integrity", "100"],
                          ["Timeliness", "100"], ["Uniqueness", "100"], ["Validity", "100"]], [3.6, 2.6], pt=14, rh=0.45)
tb(s, 7.0, 1.35, 5.8, 4.6, [
    "Unweighted mean of all rule scores: 99.46%",
    "Raw completeness 92.54% (9,994 of 10,800 rows are real orders)",
    "32 of 1,862 Product IDs carry several names; star schema keeps the first",
    "Fact-table foreign keys: 49,970 of 49,970 present in dimensions",
    "Reconciliation: 9 of 9 checks pass"], pt=16, bullets=True, tag="dq")
takeaway(s, "The 99.46% is an average of rule scores on cleaned data; the raw file scored lower on completeness.")

# 5 Star schema
s = slide("ETL and star schema", "Data flows raw, staging, clean, curated. The curated zone is a star schema with one fact table and four dimensions. Row counts are customers 793, products 1,862, dates 1,826 and geographies 632, with 9,994 fact rows. All key integrity checks pass. This supports OLAP-style roll-up, slice and dice, and feeds Power BI.")
card(s, 4.9, 3.0, 3.5, 1.5, ["fact_sales", "9,994 rows: sales, quantity, discount, profit"], pt=14, fill=TEAL, color=WHITE, bold=True, tag="fact")
for (x, y, a, b) in [(0.8, 1.4, "dim_customer", "793 customers, segment"), (8.9, 1.4, "dim_product", "1,862 products, category, sub-category"),
                     (0.8, 4.7, "dim_date", "1,826 days, year, quarter, month"), (8.9, 4.7, "dim_geography", "632 locations: region, state, city")]:
    left = x < 5
    ln = s.shapes.add_connector(1, Inches(x + 3.6 if left else x), Inches(y + 0.65), Inches(4.9 if left else 8.4), Inches(3.75))
    ln.line.color.rgb = GREY; ln.line.width = Pt(1.5)
    card(s, x, y, 3.6, 1.3, [a, b], pt=14, bold=True, tag=a)
tb(s, 4.2, 5.2, 5.0, 0.7, "Zones: raw, staging, clean, curated", pt=14, align=PP_ALIGN.CENTER, tag="zones")
takeaway(s, "All primary and foreign key checks pass; total sales are preserved through the pipeline.")

# 6 EDA trend
s = slide("EDA: growth and strong seasonality", "Monthly sales are flat across 2015 and 2016 and grow in 2017 and 2018. The seasonality index, where 100 is an average month, shows November at 185, December at 173 and September at 164, while February is 30 and January 48. A simple linear trend fitted by gradient descent matched the closed-form answer exactly at about 902 dollars per month, but R squared is only 0.251, so trend alone explains little and seasonality matters.")
pic(s, "04_monthly_sales_trend.png", 0.4, 1.25, 8.0, 5.0)
tb(s, 8.6, 1.4, 4.3, 4.8, [
    "Sales flat in 2015-2016, higher in 2017-2018",
    "Seasonality index (100 = average): Nov 185, Dec 173, Sep 164",
    "Weakest months: Feb 30, Jan 48",
    "Linear trend about 902 per month (gradient descent equals closed form), R-squared 0.251"], pt=15, bullets=True, tag="eda1")
takeaway(s, "Seasonality dominates the trend, so a model without a seasonal term will do poorly.")

# 7 EDA category region
s = slide("EDA: category and region", "Technology has the highest sales and profit; Furniture has sales of 742,000 but only 18,451 profit, a thin margin. By region, West leads on both sales and profit. These values are summed from the curated fact table.")
pic(s, "01_sales_by_category.png", 0.4, 1.2, 6.2, 3.6)
pic(s, "02_sales_by_region.png", 6.8, 1.2, 6.2, 3.6)
table(s, 0.5, 4.95, 6.0, [["Category", "Sales", "Profit"], ["Furniture", "742,000", "18,451"], ["Office Supplies", "719,047", "122,491"], ["Technology", "836,154", "145,455"]], [2.4, 1.8, 1.8], pt=12, rh=0.34)
table(s, 6.8, 4.95, 6.0, [["Region", "Sales", "Profit"], ["Central", "501,240", "39,706"], ["East", "678,781", "91,523"], ["South", "391,722", "46,749"], ["West", "725,458", "108,418"]], [2.4, 1.8, 1.8], pt=11, rh=0.3)

# 8 Discount
s = slide("Discount versus profit", "This is one of the main business findings. With no discount the margin is 29.5 percent. At 10 to 20 percent it is 11.6 percent. From 20 percent upward it turns negative: minus 10.1, minus 19.4, minus 35.7, and minus 119.2 percent above 50 percent, where all 856 lines lose money. Lines discounted above 20 percent lose 135,376 in total over 1,393 lines. The Spearman correlation is minus 0.54. Be clear this is an association, not proof of cause, because heavily discounted lines cluster in certain sub-categories so product mix confounds it.")
pic(s, "ba_discount_bands.png", 0.4, 1.25, 7.4, 5.0)
tb(s, 8.0, 1.4, 4.9, 4.8, [
    "Margin 29.5% with no discount (4,798 lines), 11.6% at 10-20%",
    "Negative from 20%: -10.1%, -19.4%, -35.7%, and -119.2% above 50% (856 lines, all loss-making)",
    "Lines discounted above 20% lose 135,376 in total (1,393 lines)",
    "Spearman correlation of discount and profit: -0.54",
    "Association only: product mix is a confounder"], pt=15, bullets=True, tag="disc")
takeaway(s, "Discounts above 20% are where profit disappears; test the cause before changing policy.")

# 9 Subcategory
s = slide("Profit by sub-category", "Copiers, Phones and Accessories earn the most profit at 55,618, 44,516 and 41,937. Tables lose 17,725, Bookcases lose 3,473 and Supplies lose 1,189. Machines have only a 1.8 percent margin on 189,239 of sales, with an average discount of 31 percent, which links back to the discount finding.")
pic(s, "ba_subcategory_profit.png", 0.4, 1.25, 7.0, 5.0)
tb(s, 7.6, 1.4, 5.3, 4.8, [
    "Top profit: Copiers 55,618; Phones 44,516; Accessories 41,937",
    "Loss-making: Tables -17,725; Bookcases -3,473; Supplies -1,189",
    "Machines: 1.8% margin on 189,239 of sales, average discount 31%"], pt=16, bullets=True, tag="sub")
takeaway(s, "A few sub-categories lose money; deep discounts are one likely reason.")

# 10 Pareto
s = slide("Pareto 80/20 analysis", "Products are concentrated: 414 of 1,862 products, 22.2 percent, produce 80 percent of sales and 70.6 percent of profit; these are class A. Class C is 959 products, 51.5 percent of the range, yet only 5 percent of sales. Customers are less concentrated: about half of 793 customers produce 80 percent of sales.")
pic(s, "ba_pareto_abc.png", 0.4, 1.25, 8.0, 5.0)
tb(s, 8.6, 1.4, 4.3, 4.8, [
    "414 of 1,862 products (22.2%) give 80.0% of sales and 70.6% of profit (class A)",
    "959 products (51.5%) are class C with 5.0% of sales",
    "Customers less concentrated: 396 of 793 (49.9%) give 80.1% of sales"], pt=15, bullets=True, tag="par")
takeaway(s, "Product range is concentrated; customer sales are spread more evenly.")

# 11 RFM
s = slide("Customer value: RFM segmentation", "Customers are grouped with k-means on recency, frequency and monetary value, k equals 4. Cooling high-value is 244 customers, 30.8 percent, but 51.5 percent of sales. The segment names are labels assigned from recency and spend thresholds, k-means does not name them. Silhouette is highest at k equals 2 (0.350 versus 0.254 at k equals 4); k equals 4 was chosen for interpretability, and results depend on the snapshot date.")
pic(s, "ba_rfm_segments.png", 0.4, 1.25, 8.0, 5.0)
tb(s, 8.6, 1.4, 4.3, 4.8, [
    "Cooling high-value: 244 customers (30.8%), 51.5% of sales, recency 98 days",
    "Active mid-value: 198, 23.4% of sales, 20 days",
    "Lapsed mid-value: 260, 23.2% of sales, 229 days",
    "Lapsed low-value: 91, 1.9% of sales, 328 days",
    "k=4 chosen for interpretability (silhouette 0.254 vs 0.350 at k=2)"], pt=14, bullets=True, tag="rfm")
takeaway(s, "The largest value group is cooling, a win-back target. Segment labels are our own.")

# 12 CV table
s = slide("Forecasting: method comparison with rolling-origin CV", "Method: monthly total sales, 48 points. Rolling-origin expanding-window cross-validation with minimum training 24 months, horizon 6, step 3, which gives 7 folds. Eleven models were tested; the main ones are shown. Damped additive Holt-Winters has the lowest mean CV MAE and the lowest 2018 hold-out MAE, and beat seasonal naive in 7 of 7 folds. SARIMA did not beat the seasonal-naive baseline on average. Plain ARIMA with no seasonal term is far worse. Note the minimum Wilcoxon p-value with 7 folds is 0.016, and folds overlap, so p-values are indicative only.")
table(s, 0.5, 1.3, 12.3, [
    ["Model", "CV MAE", "CV RMSE", "CV MAPE %", "2018 MAE", "2018 MAPE %"],
    ["Holt-Winters additive (damped)", "10,981", "13,445", "21.7", "10,897", "18.5"],
    ["Seasonal naive (baseline)", "13,739", "16,542", "25.0", "15,468", "24.5"],
    ["SARIMA(1,1,1)(0,1,1,12)", "14,513", "16,199", "36.6", "15,105", "34.0"],
    ["ARIMA(1,1,1)", "22,601", "27,047", "49.1", "23,451", "54.1"]], [4.3, 1.5, 1.5, 1.7, 1.6, 1.7], pt=15, rh=0.5, hl=[1])
tb(s, 0.5, 4.0, 12.3, 2.3, [
    "Damped Holt-Winters has the lowest CV MAE and beat seasonal naive in 7 of 7 folds (Wilcoxon p = 0.016, the smallest possible with 7 folds)",
    "SARIMA did not beat seasonal naive on average (MAE 14,513 vs 13,739); fold MAE SD 6,974 vs 3,265",
    "Damped HW vs SARIMA: gap 3,532, HW better in 4 of 7 folds, p = 0.375, not distinguishable",
    "Eleven models tested; 7 folds, 24-month minimum training, 6-month horizon"], pt=14, bullets=True, tag="cvt")
takeaway(s, "Best: damped Holt-Winters, but only clearly better than naive, SES and ARIMA.")

# 13 CV chart caveats
s = slide("Why SARIMA struggles, and honest caveats", "Be upfront here. With 48 points and one seasonal difference, a 24-month training window leaves about 12 usable points for up to 5 SARIMA parameters, so its poor result reflects the small sample and does not show SARIMA is a bad method in general. The folds overlap so they are not independent. Model choice is tentative: damped Holt-Winters leads ETS, undamped Holt-Winters and SARIMA by amounts within fold-to-fold variation.")
pic(s, "cv_mae_by_model.png", 0.4, 1.25, 7.2, 5.0)
tb(s, 7.8, 1.4, 5.1, 4.8, [
    "Only 48 points: with D=1, a 24-month window leaves about 12 usable points for up to 5 SARIMA parameters",
    "SARIMA's weak result reflects small data, not a general weakness",
    "7 folds overlap, so p-values are indicative only",
    "Model choice is tentative: gaps to ETS, undamped HW and SARIMA are within fold variation"], pt=15, bullets=True, tag="cvc")
takeaway(s, "Treat the ranking of close models as tentative, not settled.")

# 14 Diagnostics
s = slide("Residual diagnostics", "For the damped Holt-Winters model the 48 one-step residuals show no significant leftover autocorrelation: Ljung-Box p is 0.329 at lag 6 and 0.165 at lag 12. Jarque-Bera p is 0.577 and Shapiro p is 0.181, so no evidence against normality. For comparison, SARIMA residuals have Ljung-Box lag 12 p of 0.010, i.e. leftover autocorrelation. With 36 to 48 residuals these tests are weak, so a pass is not proof. ADF and KPSS disagree on the level series; one regular difference satisfies both.")
pic(s, "diag_residuals.png", 0.4, 1.25, 7.4, 5.0)
tb(s, 8.0, 1.4, 4.9, 4.8, [
    "Holt-Winters (damped), 48 residuals: Ljung-Box p = 0.329 (lag 6), 0.165 (lag 12)",
    "Jarque-Bera p = 0.577, Shapiro p = 0.181: no evidence against normality",
    "SARIMA Ljung-Box lag 12 p = 0.010: leftover autocorrelation",
    "STL seasonal strength 0.86, trend strength 0.53",
    "ADF and KPSS disagree on level (p 0.0002 vs 0.019); one difference satisfies both"], pt=14, bullets=True, tag="diag")
takeaway(s, "No leftover pattern for Holt-Winters; small samples make these tests weak.")

# 15 Final forecast
s = slide("2019 forecast with prediction intervals", "The final model is damped additive Holt-Winters refit on all 48 months. Intervals come from a residual-bootstrap with 2,000 paths. The forecast runs from 41,476 in February to 115,687 in November and 116,031 in December. The December 95 percent band is 56,622 to 189,080, which is wide. These are forecasts, not expected actuals, and they assume the recent growth and seasonal pattern continue. Intervals will be too narrow if the model is wrong.")
pic(s, "fan_chart_total.png", 0.4, 1.25, 8.0, 5.0)
tb(s, 8.6, 1.4, 4.3, 4.8, [
    "Model: damped additive Holt-Winters, refit on all 48 months",
    "Bootstrap bands, 80% and 95% (2,000 paths)",
    "Range: 41,476 (Feb) to 115,687 (Nov) and 116,031 (Dec)",
    "Dec 95% band: 56,622 to 189,080",
    "Assumes recent growth and seasonality continue"], pt=15, bullets=True, tag="fc")
takeaway(s, "Use the shape and ranges, not point values, for planning.")

# 16 Segment forecasts
s = slide("Category, region and segment forecasts", "The best model differs by series, chosen by CV MAE. Where seasonal naive wins, the 2019 forecast simply repeats 2018. Hold-out errors of 15 to 60 percent MAPE mean these sub-series forecasts are directional, not precise. West is the most reliable at 15.4 percent; South is the least at 59.7 percent.")
table(s, 0.5, 1.3, 7.4, [
    ["Series", "Best model", "CV MAE", "2018 MAPE %"],
    ["Furniture", "Seasonal naive", "3,344", "24.0"], ["Office Supplies", "HW damped", "5,182", "24.1"],
    ["Technology", "SARIMA", "7,595", "46.8"], ["Central", "Seasonal naive", "4,836", "41.4"],
    ["East", "HW damped", "6,055", "39.7"], ["South", "HW damped", "4,462", "59.7"],
    ["West", "HW damped", "4,130", "15.4"], ["Consumer", "HW multiplicative", "6,770", "32.6"],
    ["Corporate", "HW damped", "5,558", "49.7"], ["Home Office", "Seasonal naive", "4,667", "41.4"]],
    [1.9, 2.4, 1.4, 1.7], pt=12, rh=0.4)
tb(s, 8.2, 1.4, 4.7, 4.8, [
    "Best model differs by series (lowest CV MAE)",
    "Where seasonal naive wins, the 2019 forecast repeats 2018",
    "Hold-out MAPE 15-60%: directional, not precise"], pt=15, bullets=True, tag="seg")
takeaway(s, "Sub-series are noisier than the total; no single model wins everywhere.")

# 17 Power BI
s = slide("Power BI dashboard plan (build pending)", "Be explicit that the dashboard is not built yet; there are no screenshots here on purpose. The data is prepared for import: the star schema in data/curated and the forecast tables in data/forecast. The plan lists the intended pages. No mock screenshots are shown, to avoid presenting something that does not exist.")
card(s, 0.5, 1.3, 12.3, 0.8, "DASHBOARD BUILD PENDING - no screenshots shown", pt=22, fill=AMBER, color=WHITE, bold=True, tag="pend")
tb(s, 0.5, 2.35, 6.0, 3.9, ["Planned pages", "1. Overview: sales, profit, margin, yearly trend", "2. Forecast: actual vs 2019 forecast with 80/95% bands",
                            "3. Discount and profit: margin by discount band", "4. Products and customers: Pareto and RFM"], pt=16, tag="plan1")
tb(s, 6.8, 2.35, 6.0, 3.9, ["Data ready for import", "Star schema: data/curated (fact_sales + 4 dimensions)",
                            "Forecast tables: data/forecast (actual + forecast with intervals)", "Planned filters: year, category, region, segment"], pt=16, tag="plan2")
takeaway(s, "Status: data model and forecast files ready; report visuals not yet built.")

# 18 Limitations
s = slide("Limitations", "Summarise the caveats from the results summary. These matter for how far the findings can be trusted. The sample is public, not real company records, and small.")
tb(s, 0.5, 1.3, 12.3, 5.0, [
    "Small sample: 48 monthly points; SARIMA has about 12 usable points in a 24-month window",
    "CV folds overlap (6-month horizon, 3-month step), so p-values are indicative only",
    "Model choice is tentative: damped HW vs SARIMA gap is not significant (p = 0.375)",
    "Forecast assumes the 2017-2018 growth and seasonal pattern continue",
    "Intervals are bootstrap approximations and are too narrow if the model is wrong",
    "Sub-series hold-out MAPE reaches 40-60% for some series",
    "Discount-profit is an association; product mix confounds it. RFM depends on snapshot date and k",
    "Public sample data, not real company records; Power BI dashboard not yet built"], pt=16, bullets=True, tag="lim")

# 19 Conclusion
s = slide("Conclusion", "Wrap up. Damped Holt-Winters was most accurate on the 2018 hold-out with MAE 10,897 and MAPE 18.5 percent, and in cross-validation. SARIMA did not beat seasonal naive here, and this is a small-sample result. Business findings: discounts above 20 percent associate with losses, products are concentrated, and Q4 is the peak. Future work: more history, external drivers, finishing the dashboard.")
tb(s, 0.5, 1.3, 6.1, 5.0, ["Findings",
                           "Damped Holt-Winters: CV MAE 10,981; 2018 hold-out MAPE 18.5%",
                           "SARIMA did not beat seasonal naive (14,513 vs 13,739 CV MAE)",
                           "Residuals show no leftover autocorrelation for Holt-Winters",
                           "Discounts above 20% go with losses (135,376 lost)",
                           "22.2% of products give 80.0% of sales"], pt=16, tag="c1")
tb(s, 6.9, 1.3, 6.0, 5.0, ["Next steps",
                           "Build and publish the Power BI dashboard",
                           "Longer history and external drivers (promotions, holidays)",
                           "Test whether discounting causes losses, controlling for product mix",
                           "Re-run CV as more months arrive"], pt=16, tag="c2")
takeaway(s, "Seasonal structure plus a simple damped model beat more complex ones on this small series.")

prs.save(OUT)
print("saved", OUT, "slides", len(prs.slides))
print("\n".join(warnings) or "no fit warnings")
