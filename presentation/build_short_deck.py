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
DIAG = os.path.join(ROOT, "presentation", "diagrams")
PLACE = RGBColor(0xFF, 0xF3, 0xD6)


def arrow(s, x, y, w, h):
    a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    a.fill.solid(); a.fill.fore_color.rgb = TEAL; a.line.fill.background()


def image_or_placeholder(s, folder, names, x, y, w, h, label, pt=14):
    """Insert the first existing file from names, else an amber placeholder box that says what to drop in."""
    for nm in names:
        p = os.path.join(folder, nm)
        if os.path.exists(p):
            iw, ih = Image.open(p).size; sc = min(w / iw, h / ih)
            s.shapes.add_picture(p, Inches(x + (w - iw * sc) / 2), Inches(y + (h - ih * sc) / 2), Inches(iw * sc), Inches(ih * sc))
            return
    card(s, x, y, w, h, [label, "file: " + names[0]], pt=pt, fill=PLACE, color=AMBER, bold=True)
    warnings.append("PLACEHOLDER " + names[0])


NUM = {"pipeline": "1", "star_schema": "2", "forecast_validation": "3", "dashboard_flow": "4"}


def dia(s, stem, x, y, w, h, label):
    k = NUM[stem]
    image_or_placeholder(s, DIAG, [stem + ".jpg", stem + ".jpeg", stem + ".png", k + ".png", k + ".jpg", k + ".jpeg"], x, y, w, h, label)


def shot(s, fname, x, y, w, h, label):
    image_or_placeholder(s, SHOTS, [fname], x, y, w, h, "Screenshot to insert: " + label)


def caption(s, x, y, w, text):
    tb(s, x, y, w, 0.4, text, pt=12, color=GREY, align=PP_ALIGN.CENTER, tag="cap " + text[:12])


# ---------------- design layer: two fonts (Georgia headings, Segoe UI body), header, footer, shadows ----------------
from pptx.oxml import parse_xml
from pptx.oxml.ns import qn, nsdecls

FONT = "Segoe UI"
HEAD = "Georgia"
GOLD = RGBColor(0xF2, 0xA3, 0x3A)
BG = RGBColor(0xF4, 0xF7, 0xFA)
RULE = RGBColor(0xD5, 0xDC, 0xE5)
DEEP = RGBColor(0x0F, 0x3D, 0x4F)
TOTAL = 7


def soft_shadow(sh):
    sp = sh._element.spPr
    for e in sp.findall(qn("a:effectLst")):
        sp.remove(e)
    sp.append(parse_xml(
        '<a:effectLst %s><a:outerShdw blurRad="88900" dist="38100" dir="5400000" algn="t" rotWithShape="0">'
        '<a:srgbClr val="1F2A44"><a:alpha val="24000"/></a:srgbClr></a:outerShdw></a:effectLst>' % nsdecls("a")))


def gradient(sh, c1, c2, angle=0):
    sh.fill.gradient(); sh.fill.gradient_angle = angle
    st = sh.fill.gradient_stops
    st[0].color.rgb = c1; st[0].position = 0
    st[1].color.rgb = c2; st[1].position = 1


def rect(s, x, y, w, h, fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.08, shadow=False):
    sh = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sh.fill.solid(); sh.fill.fore_color.rgb = fill
    sh.line.fill.background()
    if shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        sh.adjustments[0] = radius
    if shadow:
        soft_shadow(sh)
    else:
        sh.shadow.inherit = False
    return sh


def card(s, x, y, w, h, text, pt=14, fill=LIGHT, color=NAVY, bold=False, tag=""):
    plain = fill == LIGHT
    sh = rect(s, x, y, w, h, WHITE if plain else fill, shadow=True)
    if plain:
        rect(s, x, y + 0.12, 0.07, h - 0.24, TEAL, shape=MSO_SHAPE.RECTANGLE)
    tf = sh.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.18); tf.margin_right = Inches(0.1)
    lines = text if isinstance(text, list) else [text]
    fit_check(lines, w - 0.1, h, pt, tag or lines[0][:20])
    for i, t in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run(); r.text = t; r.font.size = Pt(pt); r.font.name = FONT
        r.font.color.rgb = color; r.font.bold = bold if i == 0 else False
        if i == 0 and bold and plain:
            r.font.name = HEAD
    return sh


def takeaway(s, text, y=6.4):
    bar = rect(s, 0.5, y, 12.3, 0.55, TEAL, shadow=True, radius=0.2)
    rect(s, 0.5, y, 0.14, 0.55, GOLD, shape=MSO_SHAPE.RECTANGLE)
    tf = bar.text_frame; tf.word_wrap = True; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Inches(0.3)
    fit_check([text], 12.0, 0.55, 14, "takeaway " + text[:15])
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT
    r = p.add_run(); r.text = text; r.font.size = Pt(14); r.font.name = FONT; r.font.color.rgb = WHITE; r.font.bold = True


n = [0]


def slide(title, notes):
    s = prs.slides.add_slide(BLANK); n[0] += 1
    s.background.fill.solid(); s.background.fill.fore_color.rgb = BG
    band = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, Inches(1.05))
    band.line.fill.background(); gradient(band, NAVY, DEEP, 0); soft_shadow(band)
    rect(s, 0, 1.05, 13.333, 0.05, TEAL, shape=MSO_SHAPE.RECTANGLE)
    rect(s, 0.5, 1.05, 1.3, 0.05, GOLD, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 0.5, 0.2, 10.4, 0.7, title, pt=28, color=WHITE, bold=True, tag="title " + title[:20])
    for r_ in s.shapes[-1].text_frame.paragraphs[0].runs:
        r_.font.name = HEAD
    chip = rect(s, 11.45, 0.3, 1.35, 0.45, GOLD, radius=0.5)
    tf = chip.text_frame; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = "%02d / %02d" % (n[0], TOTAL); r.font.size = Pt(14); r.font.bold = True; r.font.name = FONT; r.font.color.rgb = NAVY
    # footer: rule, text, progress bar
    rect(s, 0.5, 7.0, 12.3, 0.01, RULE, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 0.5, 7.03, 9, 0.35, "Mayur Chauhan  |  Enrollment No.: [to be added]  |  DSC Individual Project", pt=10, color=GREY, tag="foot")
    tb(s, 10.8, 7.03, 2.0, 0.35, "Page %d of %d" % (n[0], TOTAL), pt=10, color=GREY, align=PP_ALIGN.RIGHT, tag="num")
    rect(s, 0, 7.42, 13.333, 0.08, RULE, shape=MSO_SHAPE.RECTANGLE)
    rect(s, 0, 7.42, 13.333 * n[0] / TOTAL, 0.08, TEAL, shape=MSO_SHAPE.RECTANGLE)
    s.notes_slide.notes_text_frame.text = notes
    return s


def title_slide():
    s = prs.slides.add_slide(BLANK); n[0] += 1
    bg = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
    bg.line.fill.background(); gradient(bg, NAVY, DEEP, 315)
    c1 = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(9.2), Inches(3.6), Inches(6.5), Inches(6.5))
    c1.fill.solid(); c1.fill.fore_color.rgb = RGBColor(0x17, 0x55, 0x66); c1.line.fill.background()
    c2 = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(10.6), Inches(-1.6), Inches(4.0), Inches(4.0))
    c2.fill.solid(); c2.fill.fore_color.rgb = RGBColor(0x1B, 0x7F, 0x8C); c2.line.fill.background()
    rect(s, 0.8, 1.35, 1.6, 0.08, GOLD, shape=MSO_SHAPE.RECTANGLE)
    tb(s, 0.8, 0.8, 8, 0.5, "DATA SCIENCE (DSC)  |  INDIVIDUAL PROJECT", pt=13, color=GOLD, bold=True, tag="t0")
    tb(s, 0.8, 1.6, 9.6, 3.0, "Retail Sales Forecasting", pt=44, color=WHITE, bold=True, tag="t1")
    for r_ in s.shapes[-1].text_frame.paragraphs[0].runs:
        r_.font.name = HEAD
    tb(s, 0.8, 2.75, 9.4, 1.6, "A Comparison of ARIMA, SARIMA and Holt-Winters Using an Interactive Power BI Dashboard", pt=22, color=RGBColor(0xDD, 0xEF, 0xF1), tag="t1b")
    tb(s, 0.8, 4.9, 9.0, 1.6, ["Mayur Chauhan  |  Enrollment No.: [to be added]", "Semester 7  |  L.J. Institute of Engineering and Technology", "Guide: [to be added]  |  Date: [to be added]"], pt=16, color=WHITE, tag="t2")
    s.notes_slide.notes_text_frame.text = "Introduce the project: forecast monthly retail sales, compare three methods, present the result in Power BI."
    return s


# 1 Title
title_slide()

# 2 Problem and data
s = slide("Problem and data", "Managers need to know what sells and what will sell next. Data: the public Sample Superstore retail dataset, downloaded from the leonism/sample-superstore GitHub repository, 2015 to 2018. 10,800 raw rows, of which 806 stray empty rows were removed. Everything on this slide comes from the cleaning and quality reports.")
tb(s, 0.5, 1.3, 12.3, 1.9, ["Problem: managers cannot easily see which products, regions and customers drive sales and profit, or what to expect next.", "Data: public Sample Superstore retail orders (GitHub copy), kept unchanged in data/raw. 806 empty rows removed, leaving 9,994 order lines.", "Goal: clean the data, model it as a star schema, forecast monthly sales with three methods, and compare them in an interactive dashboard."], pt=15, bullets=True, tag="p2")
for i, (a, b) in enumerate([("9,994", "order lines, 2015 to 2018"), ("99.46%", "data quality score"), ("$2.30M", "total sales"), ("12.5%", "overall profit margin")]):
    card(s, 0.5 + i * 3.1, 3.5, 2.9, 1.9, [a, b], pt=22, bold=True, tag="kpi%d" % i)
takeaway(s, "Real data, cleaned and checked before any model is fitted")

# 3 Pipeline
s = slide("Pipeline: from raw data to dashboard", "Read the flowchart left to right or top to bottom. Raw CSV is checked and cleaned, loaded into a star schema, analysed in Python (EDA and forecasts), and the output CSV files are loaded into Power BI. Replace the placeholder with the pipeline diagram image.")
dia(s, "pipeline", 0.5, 1.3, 5.2, 5.0, "Pipeline flowchart (pipeline.puml)")
tb(s, 6.2, 1.5, 6.6, 4.8, ["1. Check quality: 99.46% score", "2. Clean and fix types", "3. Build the star schema", "4. Explore: Pareto, RFM, discounts", "5. Forecast with three methods and test them", "6. Save CSV files", "7. Power BI reads the CSV files"], pt=18, bullets=False, tag="p3")
takeaway(s, "Every number in the dashboard comes from a script, so the whole pipeline can be re-run")

# 4 Star schema
s = slide("Data model: star schema", "Fact table at the centre, dimensions around it. The forecast table joins to the date table and to the model list. Row counts are from the curated CSV files. Replace the placeholder with the star schema diagram image.")
dia(s, "star_schema", 0.5, 1.3, 7.7, 2.9, "Star schema diagram (star_schema.puml)")
table(s, 8.4, 1.4, 4.4, [["Table", "Rows"], ["fact_sales", "9,994"], ["dim_date", "1,826"], ["dim_product", "1,862"], ["dim_customer", "793"], ["dim_geography", "632"], ["fact_forecast", "48"], ["dim_model", "3"]], [2.6, 1.8], pt=13, rh=0.42)
tb(s, 0.5, 4.4, 7.7, 1.9, ["Fact table: one row per order line, with sales, quantity, discount and profit.", "Dimensions: date, product, customer and geography describe each sale.", "fact_forecast holds actual and forecast values by month and model; dim_model lets one slicer switch the model."], pt=14, bullets=True, tag="p4")
takeaway(s, "Standard star schema: fast to query and the shape Power BI expects")

# 5 Forecasting
s = slide("Forecasting: how the models were compared", "Each model is fitted on past months and tested on the next 6 months, seven times, using an expanding training window. Lower error is better. Holt-Winters has the lowest error, SARIMA did not beat the seasonal-naive baseline, ARIMA is worst. Caveats: only 48 months, folds overlap, Holt-Winters vs SARIMA is not statistically significant (p 0.375). Numbers from reports/RESULTS_SUMMARY.md.")
dia(s, "forecast_validation", 0.5, 1.3, 5.2, 5.0, "Validation flowchart (forecast_validation.puml)")
table(s, 5.9, 1.3, 6.9, [["Model", "CV MAE", "CV MAPE %", "2018 MAPE %"], ["Holt-Winters (damped)", "10,981", "21.7", "18.5"], ["Seasonal naive", "13,739", "25.0", "24.5"], ["SARIMA(1,1,1)(0,1,1,12)", "14,513", "36.6", "34.0"], ["ARIMA(1,1,1)", "22,601", "49.1", "54.1"]], [2.8, 1.2, 1.5, 1.4], pt=12, rh=0.4, hl=[1])
pic(s, "cv_mae_by_model.png", 5.9, 3.4, 6.9, 2.9)
takeaway(s, "Holt-Winters has the lowest error, but its gap to SARIMA is not statistically significant (p = 0.375)")

# 6 Findings with figures
s = slide("Findings", "Left: margin falls as discount rises and lines above 20 percent discount lose money in total. Middle: 22.2 percent of products give 80 percent of sales. Right: the 2019 forecast from the best model. Numbers from RESULTS_SUMMARY.md.")
for i, (f, c) in enumerate([("ba_discount_bands.png", "Discount vs profit"), ("ba_pareto_abc.png", "Pareto: products vs sales"), ("ts_final_forecast.png", "2019 sales forecast")]):
    pic(s, f, 0.5 + i * 4.15, 1.3, 4.0, 3.3)
    caption(s, 0.5 + i * 4.15, 4.62, 4.0, c)
tb(s, 0.5, 5.1, 12.3, 1.3, ["Margin is 29.5% with no discount and 11.6% at 10 to 20% discount; lines above 20% discount lose 135,376 in total.", "22.2% of products (414 of 1,862) give 80% of sales.", "Holt-Winters forecasts about $910K for 2019."], pt=14, bullets=True, tag="p6")
takeaway(s, "Discounting is the main profit risk; Holt-Winters is the best forecaster here")

# 7 Power BI and conclusion
s = slide("Power BI dashboard and conclusion", "Two pages are built: Overview and Forecasting Arena. Slicers filter the dimension tables and the DAX measures update the cards and charts. Only two of the four planned pages are built. Insert real screenshots of the two pages and the dashboard flow diagram.")
dia(s, "dashboard_flow", 0.5, 1.3, 7.6, 3.1, "Dashboard flow (dashboard_flow.puml)")
shot(s, "page1_overview.png", 8.4, 1.3, 4.4, 2.4, "Overview page")
shot(s, "page2_forecasting_arena.png", 8.4, 3.85, 4.4, 2.4, "Forecasting Arena page")
tb(s, 0.5, 4.5, 7.6, 1.85, ["Built: Overview and Forecasting Arena pages, with Year, Region and Model slicers.", "Limits: 48 months of data, overlapping folds, two pages, the 2019 forecast covers the best model only.", "Conclusion: Holt-Winters forecasts retail sales best here, and the dashboard lets users compare the three methods."], pt=13, bullets=True, tag="p7")
takeaway(s, "Answer to the title: Holt-Winters is the most accurate of the three methods on this data")

prs.save(OUT)
print("saved", OUT, "slides", len(prs.slides))
print("\n".join(warnings) if warnings else "no fit warnings")
