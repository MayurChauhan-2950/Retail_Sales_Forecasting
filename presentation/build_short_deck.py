import math, os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(ROOT, "reports", "figures")
OUT = os.path.join(ROOT, "presentation", "Retail_Sales_Forecasting_Short.pptx")
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


SHOTS = os.path.join(ROOT, "powerbi", "screenshots")


def arrow(s, x, y, w, h):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = TEAL; a.line.fill.background()


def shot(s, fname, x, y, w, h, label):
    p = os.path.join(SHOTS, fname)
    if os.path.exists(p):
        iw, ih = Image.open(p).size; sc = min(w / iw, h / ih)
        s.shapes.add_picture(p, Inches(x + (w - iw * sc) / 2), Inches(y + (h - ih * sc) / 2), Inches(iw * sc), Inches(ih * sc))
    else:
        card(s, x, y, w, h, ["Screenshot to insert", label], pt=14, fill=RGBColor(0xFF, 0xF3, 0xD6), color=AMBER, bold=True)
        warnings.append("MISSING screenshot " + fname)


# 1 Title
s = prs.slides.add_slide(BLANK); n[0] += 1
bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
tb(s, 0.8, 1.6, 11.7, 2.2, "Retail Sales Forecasting: A Comparison of ARIMA, SARIMA and Holt-Winters Using an Interactive Power BI Dashboard", pt=34, color=WHITE, bold=True, tag="t1")
tb(s, 0.8, 4.4, 11.7, 1.6, ["Mayur Chauhan  |  Enrollment No.: [to be added]", "Data Science (DSC), Semester 7  |  L.J. Institute of Engineering and Technology", "Guide: [to be added]  |  Date: [to be added]"], pt=18, color=RGBColor(0xDD, 0xEF, 0xF1), tag="t2")
s.notes_slide.notes_text_frame.text = "Introduce the project: forecast monthly retail sales, compare three methods, present it in Power BI."

# 2 Problem and data
s = slide("Problem and data", "Managers need to know what sells and what will sell next. Data: Sample Superstore, 2015 to 2018. Everything on this slide comes from the cleaning and quality reports.")
tb(s, 0.5, 1.3, 12.3, 1.6, ["Managers cannot easily see which products, regions and customers drive sales and profit, or what to expect next.", "Goal: clean the data, model it as a star schema, forecast monthly sales with three methods, and compare them in an interactive dashboard."], pt=18, bullets=True, tag="p2")
for i, (a, b) in enumerate([("9,994", "order lines, 2015 to 2018"), ("99.46%", "data quality score"), ("$2.30M", "total sales"), ("12.5%", "overall profit margin")]):
    card(s, 0.5 + i * 3.1, 3.3, 2.9, 1.7, [a, b], pt=18, bold=True, tag="kpi%d" % i)
takeaway(s, "Real data, cleaned and checked before any model is fitted")

# 3 Pipeline flowchart
s = slide("Pipeline: from raw data to dashboard", "Read left to right. Raw CSV is cleaned into the curated star schema. From there two branches: business analytics and forecasting. Forecast files and the curated tables load into Power BI. PlantUML source is in presentation/diagrams/pipeline.puml.")
steps = [["Raw CSV", "9,994 lines"], ["Profile + clean", "quality 99.46%"], ["Star schema", "fact + 4 dims"], ["Python analysis", "EDA, RFM, forecasts"], ["Forecast CSVs", "2018 hold-out, 2019"], ["Power BI model", "DAX measures"], ["Dashboard", "2 interactive pages"]]
for i, t in enumerate(steps):
    x = 0.4 + i * 1.82
    last = i == len(steps) - 1
    card(s, x, 2.5, 1.5, 1.5, t, pt=12, bold=True, fill=TEAL if last else LIGHT, color=WHITE if last else NAVY, tag="step%d" % i)
    if not last:
        arrow(s, x + 1.52, 3.05, 0.28, 0.4)
tb(s, 0.5, 4.5, 12.3, 1.6, ["Analysis branch: Pareto 80/20, RFM customer segments, discount versus profit.", "Forecast branch: Holt-Winters, ARIMA, SARIMA with rolling-origin cross-validation and residual diagnostics."], pt=16, bullets=True, tag="p3")
takeaway(s, "Every number in the dashboard is produced by a script, so the pipeline can be re-run end to end")

# 4 Star schema
s = slide("Data model: star schema", "Fact table at the centre, dimensions around it. The forecast table joins to the date table and to the model list. Row counts are from the curated CSV files. PlantUML source is in presentation/diagrams/star_schema.puml.")
card(s, 5.15, 2.9, 3.0, 1.5, ["fact_sales", "9,994 rows", "sales, quantity, discount, profit"], pt=13, bold=True, fill=NAVY, color=WHITE, tag="fact")
for (x, y, t) in [(0.6, 1.4, ["dim_date", "1,826 rows"]), (9.7, 1.4, ["dim_customer", "793 rows"]), (0.6, 4.6, ["dim_product", "1,862 rows"]), (9.7, 4.6, ["dim_geography", "632 rows"])]:
    card(s, x, y, 3.0, 1.2, t, pt=14, bold=True, tag=t[0])
card(s, 5.15, 5.1, 3.0, 1.1, ["fact_forecast", "48 rows: hold-out + 2019"], pt=13, bold=True, fill=RGBColor(0xDD, 0xEF, 0xF1), tag="ff")
card(s, 5.15, 1.4, 3.0, 1.0, ["dim_model", "3 models"], pt=13, bold=True, tag="dm")
for (x, y) in [(3.6, 2.3), (8.15, 2.3), (3.6, 4.4), (8.15, 4.4)]:
    ln = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(1.55), Inches(0.06))
    ln.fill.solid(); ln.fill.fore_color.rgb = TEAL; ln.line.fill.background()
takeaway(s, "Standard star schema: one fact table, four dimensions, plus a forecast table linked to dates and models")

# 5 Forecast comparison
s = slide("Forecast comparison: ARIMA vs SARIMA vs Holt-Winters", "Rolling-origin cross-validation: 7 folds, expanding window, horizon 6 months. Lower error is better. Holt-Winters wins, SARIMA did not beat the seasonal-naive baseline, ARIMA is worst. Caveat: only 48 months, folds overlap, Holt-Winters vs SARIMA is not statistically significant (p 0.375). Numbers from reports/RESULTS_SUMMARY.md.")
table(s, 0.5, 1.4, 6.2, [["Model", "CV MAE", "CV MAPE %", "2018 MAPE %"], ["Holt-Winters (damped)", "10,981", "21.7", "18.5"], ["Seasonal naive", "13,739", "25.0", "24.5"], ["SARIMA(1,1,1)(0,1,1,12)", "14,513", "36.6", "34.0"], ["ARIMA(1,1,1)", "22,601", "49.1", "54.1"]], [2.6, 1.1, 1.3, 1.2], pt=13, rh=0.5, hl=[1])
pic(s, "cv_mae_by_model.png", 6.9, 1.3, 5.9, 4.4)
tb(s, 0.5, 4.3, 6.2, 1.9, ["Holt-Winters beat seasonal naive in 7 of 7 folds.", "SARIMA did not beat seasonal naive on average.", "With 48 months, SARIMA has little data to estimate from."], pt=15, bullets=True, tag="p5")
takeaway(s, "Holt-Winters gives the lowest error, but the gap to SARIMA is not statistically significant (p = 0.375)")

# 6 Dashboard
s = slide("Interactive Power BI dashboard", "Two pages built: Overview with KPI cards, monthly sales, category sales and Year and Region slicers; Forecasting Arena with a model slicer, hold-out chart, 2019 forecast with 95 percent interval and the accuracy table. Only two of the four planned pages are built. Screenshots are real screenshots of the report.")
shot(s, "page1_overview.png", 0.5, 1.3, 6.0, 4.4, "Page 1: Overview")
shot(s, "page2_forecasting_arena.png", 6.8, 1.3, 6.0, 4.4, "Page 2: Forecasting Arena")
tb(s, 0.5, 5.8, 12.3, 0.6, "Overview: KPIs, monthly sales, sales by category, Year and Region slicers.  Forecasting Arena: model slicer, hold-out vs forecast, 2019 with 95% interval, accuracy table.", pt=12, tag="p6")
takeaway(s, "Power BI shows Holt-Winters (additive) as best: 2019 forecast about $910K, +24.1% vs 2018")

# 7 Findings and limits
s = slide("Findings, limits and conclusion", "Business findings come from the analytics scripts. State the limits honestly: small sample, overlapping folds, only two dashboard pages, the 2019 forecast covers the best model only. Close by restating the answer to the title.")
tb(s, 0.5, 1.3, 6.0, 4.9, ["Findings", "Margin is 29.5% with no discount and 11.6% at 10 to 20% discount.", "Lines discounted above 20% lose 135,376 in total.", "22.2% of products give 80% of sales.", "Holt-Winters had the lowest forecast error."], pt=16, bullets=True, tag="p7a")
tb(s, 6.8, 1.3, 6.0, 4.9, ["Limits", "Only 48 months of data.", "Cross-validation folds overlap, so p-values are indicative.", "Dashboard has 2 pages; the 2019 forecast is for the best model only.", "Discount and profit is an association, not proof of cause."], pt=16, bullets=True, tag="p7b")
takeaway(s, "Conclusion: Holt-Winters forecasts retail sales best here, and the dashboard lets users compare the three methods")

prs.save(OUT)
print("saved", OUT, "slides", len(prs.slides))
print("\n".join(warnings) if warnings else "no fit warnings")
