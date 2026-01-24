from annotated_types import doc
from reportlab.platypus import (
    BaseDocTemplate, Frame, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
    PageBreak, Flowable, Image
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import matplotlib.pyplot as plt
import tempfile
import json
import os
import re
import numpy as np

# ================= FONTS =================
pdfmetrics.registerFont(TTFont("Montserrat", "assets/fonts/Montserrat-Regular.ttf"))
pdfmetrics.registerFont(TTFont("Montserrat-Bold", "assets/fonts/Montserrat-Bold.ttf"))

# ================= GRADIENT =================
def draw_horizontal_gradient(canvas, y_start, height, width):
    stops = [
        colors.HexColor("#FFD580"),
        colors.HexColor("#FF6B6B"),
        colors.HexColor("#D946EF"),
        colors.HexColor("#7C3AED"),
    ]

    steps = 400
    segment = steps // (len(stops) - 1)

    for i in range(steps):
        seg_index = min(i // segment, len(stops) - 2)
        ratio = (i % segment) / float(segment)

        start = stops[seg_index]
        end = stops[seg_index + 1]

        r = start.red + (end.red - start.red) * ratio
        g = start.green + (end.green - start.green) * ratio
        b = start.blue + (end.blue - start.blue) * ratio

        canvas.setFillColor(colors.Color(r, g, b))
        x = (width / steps) * i
        canvas.rect(x, y_start, width / steps + 1, height, stroke=0, fill=1)

# ================= HEADER / FOOTER =================
def draw_branding(canvas, doc):
    width, height = A4
    header_height = 10
    footer_height = 40

    draw_horizontal_gradient(canvas, height - header_height, header_height, width)
    draw_horizontal_gradient(canvas, 0, footer_height, width)

    canvas.setFillColor(colors.white)
    canvas.setFont("Montserrat", 10)
    canvas.drawString(20, 14, "Confidential – Report K6 AI Performance Intelligence")
    canvas.drawRightString(width - 20, 14, f"Page {doc.page - 1}")

def draw_brand_cover(canvas, doc):
    width, height = A4
    header_height = 10
    footer_height = 10

    draw_horizontal_gradient(canvas, height - header_height, header_height, width)
    draw_horizontal_gradient(canvas, 0, footer_height, width)


# ================= SECTION HEADER =================
class SectionHeader(Flowable):
    def __init__(self, text):
        Flowable.__init__(self)
        self.text = text

    def draw(self):
        self.canv.setFillColor(colors.HexColor("#7C3AED"))
        self.canv.rect(0, 8, 6, 24, fill=1)
        self.canv.setFillColor(colors.black)
        self.canv.setFont("Montserrat-Bold", 16)
        self.canv.drawString(15, 12, self.text)

    def wrap(self, availWidth, availHeight):
        return availWidth, 36

# ================= CHART HELPERS =================
def save_chart(fig):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    fig.savefig(tmp.name, bbox_inches="tight", dpi=140)
    plt.close(fig)
    return tmp.name

def latency_chart(timeline, sla=500):
    data = timeline.get("latency", {})
    if not data:
        return None
    times = sorted(data.keys())
    avg = [np.mean(data[t]) for t in times]

    fig = plt.figure(figsize=(6, 3))
    plt.plot(avg)
    plt.axhline(y=sla, linestyle="--")
    plt.title("Latency Over Time (SLA Overlay)")
    plt.ylabel("ms")
    plt.tight_layout()
    return save_chart(fig)

def throughput_chart(timeline):
    data = timeline.get("requests", {})
    if not data:
        return None
    times = sorted(data.keys())
    rps = [data[t] for t in times]

    fig = plt.figure(figsize=(6, 3))
    plt.plot(rps)
    plt.title("Throughput (Requests/sec)")
    plt.tight_layout()
    return save_chart(fig)

def error_chart(timeline):
    checks = timeline.get("checks", {})
    if not checks:
        return None

    times = sorted(checks.keys())
    rates = []
    for t in times:
        total = checks[t]["pass"] + checks[t]["fail"]
        rate = checks[t]["fail"] / total if total else 0
        rates.append(rate)

    fig = plt.figure(figsize=(6, 3))
    plt.plot(rates)
    plt.title("Error Rate Trend")
    plt.tight_layout()
    return save_chart(fig)

def histogram_chart(timeline):
    data = timeline.get("latency", {})
    values = []
    for arr in data.values():
        values.extend(arr)

    if not values:
        return None

    fig = plt.figure(figsize=(6, 3))
    plt.hist(values, bins=30)
    plt.title("Latency Distribution")
    plt.tight_layout()
    return save_chart(fig)

# ================= MAIN =================
def generate(path, project_name, url, structured_json, analysis):

    data = json.loads(structured_json)
    metrics = data.get("metrics", {})
    timeline = data.get("timeline", {})
    scorecard = data.get("scorecard", {})

    doc = BaseDocTemplate(path, pagesize=A4)

    frame = Frame(
        60,
        75,
        A4[0] - 120,
        A4[1] - 175,
        id='normal'
    )

    cover_template = PageTemplate(
        id='cover',
        frames=frame,
        onPage=draw_brand_cover
    )

    brand_template = PageTemplate(
        id='brand',
        frames=frame,
        onPage=draw_branding
    )

    doc.addPageTemplates([cover_template, brand_template])


    elements = []

    # COVER
    elements.append(Spacer(1, 2 * inch))

    # Main Title
    elements.append(Paragraph(
        "<font name='Montserrat-Bold' size=26>Load Test Report</font>",
        ParagraphStyle(name="coverTitle", fontName="Montserrat-Bold", alignment=TA_LEFT)
    ))
    elements.append(Spacer(1, 0.6 * inch))

    # Project Name (Old Orange)
    elements.append(Paragraph(
        f"<font name='Montserrat-Bold' size=18 color='#D97706'>{project_name}</font>",
        ParagraphStyle(name="coverProject", fontName="Montserrat-Bold", alignment=TA_LEFT)
    ))
    elements.append(Spacer(1, 0.15 * inch))

    # URL (Purple)
    elements.append(Paragraph(
        f"<font name='Montserrat' size=14 color='#7C3AED'>{url}</font>",
        ParagraphStyle(name="coverUrl", fontName="Montserrat", alignment=TA_LEFT)
    ))

    from datetime import datetime
    generated_at = datetime.now().strftime("%B %d, %Y • %H:%M")
    elements.append(Spacer(1, 0.2 * inch))

    elements.append(Paragraph(
        f"<font name='Montserrat' size=11 color='#666666'>Generated on {generated_at}</font>",
        ParagraphStyle(name="coverDate", fontName="Montserrat", alignment=TA_LEFT)
    ))
    elements.append(Spacer(1, 1.2 * inch))

    logo_path = "assets/logo.png"
    if os.path.exists(logo_path):
        elements.append(
            Image(
                logo_path,
                width=3 * inch,
                height=3 * inch,
                kind='proportional'
            )
        )
    elements.append(PageBreak())
    doc.handle_nextPageTemplate('brand')

    # DASHBOARD
    elements.append(SectionHeader("Performance Dashboard"))
    elements.append(Spacer(1, 0.6 * inch))

    charts = [
        latency_chart(timeline),
        throughput_chart(timeline),
        error_chart(timeline),
        histogram_chart(timeline),
    ]

    for chart in charts:
        if chart:
            elements.append(Image(chart, width=6*inch, height=3*inch))
            elements.append(Spacer(1, 0.6 * inch))

    elements.append(PageBreak())

    # SCORECARD
    elements.append(SectionHeader("Executive Scorecard"))
    elements.append(Spacer(1, 0.4 * inch))

    score_table = Table([
        ["Performance Score", scorecard.get("score", "N/A")],
        ["SLA Grade", scorecard.get("grade", "N/A")],
        ["Risk Level", scorecard.get("risk", "N/A")]
    ], colWidths=[3 * inch, 2 * inch])

    score_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7C3AED")),
        ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))

    elements.append(score_table)
    elements.append(Spacer(1, 0.4 * inch))
    elements.append(Spacer(1, 0.4 * inch))

    # PERFORMANCE METRICS
    elements.append(SectionHeader("Performance Metrics"))
    elements.append(Spacer(1, 0.4 * inch))

    http = metrics.get("http_req_duration", {})
    checks = metrics.get("checks", {})
    reqs = metrics.get("http_reqs", {})

    metrics_table = Table([
        ["Avg (ms)", http.get("avg", "N/A")],
        ["P95 (ms)", http.get("p(95)", "N/A")],
        ["P99 (ms)", http.get("p(99)", "N/A")],
        ["Requests/sec", reqs.get("rate", "N/A")],
        ["Error Rate", checks.get("error_rate", "N/A")]
    ], colWidths=[3 * inch, 2 * inch])

    metrics_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7C3AED")),
        ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
    ]))

    elements.append(metrics_table)
    elements.append(PageBreak())

    # AI ENGINEERING ANALYSIS
    elements.append(SectionHeader("AI Engineering Analysis"))
    elements.append(Spacer(1, 0.6 * inch))

    heading_style = ParagraphStyle(
        name="heading",
        fontName="Montserrat-Bold",
        fontSize=16,
        alignment=TA_LEFT,
        spaceBefore=10,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        name="body",
        fontName="Montserrat",
        fontSize=11,
        leading=18,
        alignment=TA_JUSTIFY
    )

    clean = analysis.replace("`", "").replace("**", "")

    for line in clean.split("\n"):
        line = line.strip()

        if not line:
            elements.append(Spacer(1, 0.25 * inch))
            continue

        if line.startswith("## ") or line.startswith("### "):
            elements.append(Paragraph(line.replace("#", "").strip(), heading_style))
            elements.append(Spacer(1, 0.2 * inch))
            continue

        number_match = re.match(r"^(\d+\.)\s*(.*)", line)
        if number_match:
            elements.append(
                Paragraph(
                    number_match.group(2),
                    body_style,
                    bulletText=number_match.group(1)
                )
            )
            elements.append(Spacer(1, 0.2 * inch))
            continue

        if line.startswith("- ") or line.startswith("* "):
            elements.append(
                Paragraph(line[2:], body_style, bulletText="•")
            )
            elements.append(Spacer(1, 0.2 * inch))
            continue

        elements.append(Paragraph(line, body_style))

    doc.build(elements)
