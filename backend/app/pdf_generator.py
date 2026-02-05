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

# ================= SECURITY ONLY PDF =================
def generate_security_pdf(path, project_name, url, security):
    doc = BaseDocTemplate(path, pagesize=A4)

    frame = Frame(
        60,
        75,
        A4[0] - 120,
        A4[1] - 175,
        id='normal'
    )

    brand_template = PageTemplate(
        id='brand',
        frames=frame,
        onPage=draw_branding
    )

    doc.addPageTemplates([brand_template])

    elements = []

    elements.append(Spacer(1, 0.6 * inch))
    elements.append(SectionHeader("Security Header Report"))
    elements.append(Spacer(1, 0.4 * inch))

    heading = ParagraphStyle(
        name="headingSec",
        fontName="Montserrat-Bold",
        fontSize=12,
    )

    body = ParagraphStyle(
        name="bodySec",
        fontName="Montserrat",
        fontSize=10,
        leading=14,
    )

    summary_rows = [
        ["Grade", security.get("score") or security.get("grade", "N/A")],
        ["Target", security.get("url", url)],
    ]

    if security.get("recommendations"):
        summary_rows.append([
            "Recommendations",
            ", ".join(security.get("recommendations", [])),
        ])

    summary_table = Table(summary_rows, colWidths=[2.5 * inch, 3.5 * inch])
    summary_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7C3AED")),
        ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.3 * inch))

    headers_status = security.get("headers") or {}
    if headers_status:
        rows = [["Header", "Status"]]
        for key, val in headers_status.items():
            rows.append([key, str(val)])

        header_table = Table(rows, colWidths=[3 * inch, 3 * inch])
        header_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3E8FF")),
            ("FONTNAME", (0, 0), (-1, 0), "Montserrat-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Montserrat"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
        ]))
        elements.append(header_table)
    else:
        elements.append(Paragraph(
            "No header data available.",
            body
        ))

    if security.get("error") or security.get("pdf_error"):
        elements.append(Spacer(1, 0.2 * inch))
        elements.append(Paragraph(
            "Scan error:", heading
        ))
        elements.append(Paragraph(
            security.get("error") or security.get("pdf_error"),
            body
        ))

    recommendations = security.get("recommendations") or []
    if recommendations:
        elements.append(Spacer(1, 0.3 * inch))
        elements.append(Paragraph("Next Actions", heading))
        elements.append(Spacer(1, 0.1 * inch))
        for rec in recommendations:
            elements.append(Paragraph(rec, body, bulletText="•"))

    doc.build(elements)

# ================= MAIN =================
def generate(path, project_name, url, structured_json, analysis):

    data = json.loads(structured_json)
    metrics = data.get("metrics", {})
    timeline = data.get("timeline", {})
    scorecard = data.get("scorecard", {})
    security = data.get("security_headers", {})
    ssl_data = data.get("ssl", {})
    wpt = data.get("webpagetest", {})

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

    # FINAL SECURITY RECAP (placed at end for clarity)
    if security:
        elements.append(PageBreak())
        elements.append(SectionHeader("Security Header Recap"))
        elements.append(Spacer(1, 0.3 * inch))

        present = security.get("present")
        total = security.get("total")
        score_fraction = f"{present}/{total}" if present is not None and total else "N/A"

        recap_body = ParagraphStyle(
            name="recapBody",
            parent=body_style,
            fontSize=10,
            leading=14,
        )

        recap_rows = [
            ["Score", Paragraph(str(score_fraction), recap_body)],
            ["Grade", Paragraph(str(security.get("grade", "N/A")), recap_body)],
            ["Target", Paragraph(str(security.get("url", url)), recap_body)],
            ["Status", Paragraph("Ready" if "error" not in security else "Error", recap_body)],
        ]

        if security.get("recommendations"):
            recap_rows.append([
                "Top Recommendations",
                Paragraph(", ".join(security.get("recommendations", [])), recap_body),
            ])

        recap_table = Table(recap_rows, colWidths=[2.8 * inch, 3.0 * inch])
        recap_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7C3AED")),
            ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        elements.append(recap_table)
        elements.append(Spacer(1, 0.25 * inch))

        hdrs = security.get("headers") or {}
        if hdrs:
            rows = [["Header", "Status"]]
            for key, val in hdrs.items():
                rows.append([key, str(val)])

            hdr_table = Table(rows, colWidths=[2.8 * inch, 3.0 * inch])
            hdr_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3E8FF")),
                ("FONTNAME", (0, 0), (-1, 0), "Montserrat-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(hdr_table)
            elements.append(Spacer(1, 0.2 * inch))

        if security.get("error") or security.get("pdf_error"):
            elements.append(Paragraph(
                f"Scan issues: {security.get('error') or security.get('pdf_error')}",
                body_style
            ))

        raw_hdrs = security.get("raw_headers")
        if raw_hdrs:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Raw Headers", heading_style))
            elements.append(Spacer(1, 0.3 * inch))

            small_body = ParagraphStyle(
                name="rawHdrBody",
                parent=body_style,
                fontSize=8,
                leading=10,
                wordWrap="CJK",
            )

            rows = [["Header", "Value"]]
            for line in raw_hdrs.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    rows.append([
                        Paragraph(k.strip(), small_body),
                        Paragraph(v.strip(), small_body),
                    ])
                elif line.strip():
                    rows.append([
                        Paragraph(line.strip(), small_body),
                        Paragraph("", small_body),
                    ])

            hdr_table = Table(rows[:80], colWidths=[2.8 * inch, 3.0 * inch])
            hdr_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3E8FF")),
                ("FONTNAME", (0, 0), (-1, 0), "Montserrat-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(hdr_table)

        if ssl_data:
            elements.append(Spacer(1, 0.3 * inch))
            elements.append(SectionHeader("SSL / TLS Analysis"))
            elements.append(Spacer(1, 0.2 * inch))

            ssl_body = ParagraphStyle(
                name="sslBody",
                parent=body_style,
                fontSize=10,
                leading=13,
                wordWrap="CJK",
            )

            def wrap_ssl(val):
                if val is None or val == "":
                    return Paragraph("-", ssl_body)
                if isinstance(val, list):
                    txt = ", ".join(str(v) for v in val) or "-"
                else:
                    txt = str(val)
                return Paragraph(txt, ssl_body)

            ssl_rows = [
                ["Status", wrap_ssl(ssl_data.get("status", "N/A"))],
                ["Rating", wrap_ssl(ssl_data.get("rating", "N/A"))],
                ["Score", wrap_ssl(ssl_data.get("score", "N/A"))],
                ["Protocol Score", wrap_ssl(ssl_data.get("protocol_score", "N/A"))],
                ["Key Exchange Score", wrap_ssl(ssl_data.get("key_exchange_score", "N/A"))],
                ["Cipher Strength Score", wrap_ssl(ssl_data.get("cipher_strength_score", "N/A"))],
                ["Supported", wrap_ssl(ssl_data.get("supported_versions", []))],
                ["Weak Protocols", wrap_ssl(ssl_data.get("weak_versions", []))],
                ["Negotiated Ciphers", wrap_ssl(ssl_data.get("negotiated_ciphers", []))],
                ["Key", wrap_ssl(f"{ssl_data.get('key_algorithm', 'N/A')} {ssl_data.get('key_size') or ''}".strip())],
                ["Cert expires (days)", wrap_ssl(ssl_data.get("expires_in_days", "N/A"))],
                ["Cert Subject", wrap_ssl(ssl_data.get("cert_subject", "N/A"))],
                ["Cert Issuer", wrap_ssl(ssl_data.get("cert_issuer", "N/A"))],
                ["Valid From", wrap_ssl(ssl_data.get("cert_not_before", "N/A"))],
                ["Valid To", wrap_ssl(ssl_data.get("cert_not_after", "N/A"))],
            ]

            if ssl_data.get("ssllabs_grade"):
                ssl_rows.append(["SSL Labs Grade", wrap_ssl(ssl_data.get("ssllabs_grade"))])
            if ssl_data.get("ssllabs_status"):
                ssl_rows.append(["SSL Labs Status", wrap_ssl(ssl_data.get("ssllabs_status"))])

            ssl_table = Table(ssl_rows, colWidths=[2.8 * inch, 3.0 * inch])
            ssl_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7C3AED")),
                ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(ssl_table)

            findings = ssl_data.get("findings") or []
            if findings:
                elements.append(Spacer(1, 0.15 * inch))
                elements.append(Paragraph("Findings", heading_style))
                elements.append(Spacer(1, 0.05 * inch))
                for f in findings[:20]:
                    elements.append(
                        Paragraph(
                            f"[{f.get('severity','')}] {f.get('message','')}",
                            body_style,
                            bulletText="•"
                        )
                    )

    # WEBPAGETEST SECTION (placed after SSL)
    if isinstance(wpt, dict) and (wpt.get("status") or wpt.get("error")):
        elements.append(Spacer(1, 0.4 * inch))
        elements.append(SectionHeader("WebPageTest (Playwright)"))
        elements.append(Spacer(1, 0.25 * inch))

        wpt_heading = ParagraphStyle(
            name="wptHeading",
            fontName="Montserrat-Bold",
            fontSize=12,
        )

        wpt_body = ParagraphStyle(
            name="wptBody",
            fontName="Montserrat",
            fontSize=10,
            leading=14,
            wordWrap="CJK",
        )

        def wrap_wpt(val):
            if val is None or val == "":
                return Paragraph("-", wpt_body)
            if isinstance(val, list):
                txt = ", ".join(str(v) for v in val) or "-"
            else:
                txt = str(val)
            return Paragraph(txt, wpt_body)

        settings_rows = [
            ["Status", wrap_wpt(wpt.get("status", "N/A"))],
            ["Agent", wrap_wpt(wpt.get("agent", "N/A"))],
            ["Score", wrap_wpt(wpt.get("score", "N/A"))],
            ["Grade", wrap_wpt(wpt.get("grade", "N/A"))],
        ]

        if wpt.get("settings"):
            settings = wpt.get("settings", {})
            settings_rows.extend([
                ["Network", wrap_wpt(settings.get("network_profile", "N/A"))],
                ["Latency (ms)", wrap_wpt(settings.get("latency_ms", "N/A"))],
                ["Download (B/s)", wrap_wpt(settings.get("download_bps", "N/A"))],
                ["Upload (B/s)", wrap_wpt(settings.get("upload_bps", "N/A"))],
                ["CPU Throttle", wrap_wpt(settings.get("cpu_throttle", "N/A"))],
            ])

        settings_table = Table(settings_rows, colWidths=[2.8 * inch, 3.0 * inch])
        settings_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7C3AED")),
            ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]))

        elements.append(settings_table)
        elements.append(Spacer(1, 0.2 * inch))

        if wpt.get("summary"):
            summary = wpt.get("summary")
            sum_rows = [
                ["TTFB (s)", wrap_wpt(round((summary.get("ttfb_ms") or 0) / 1000, 3))],
                ["FCP (s)", wrap_wpt(round((summary.get("fcp_ms") or 0) / 1000, 3))],
                ["LCP (s)", wrap_wpt(round((summary.get("lcp_ms") or 0) / 1000, 3))],
                ["CLS", wrap_wpt(summary.get("cls"))],
                ["Start Render (s)", wrap_wpt(round((summary.get("start_render_ms") or 0) / 1000, 3))],
                ["Speed Index (s)", wrap_wpt(round((summary.get("speed_index_ms") or 0) / 1000, 3))],
                ["TBT (s)", wrap_wpt(round((summary.get("tbt_ms") or 0) / 1000, 3))],
                ["Page Weight (KB)", wrap_wpt(summary.get("page_weight_kb"))],
                ["Total Requests", wrap_wpt(summary.get("total_requests"))],
                ["DC Time (s)", wrap_wpt(round((summary.get("dc_time_ms") or 0) / 1000, 3))],
                ["DC Bytes (KB)", wrap_wpt(summary.get("dc_bytes_kb"))],
                ["Total Time (s)", wrap_wpt(round((summary.get("total_time_ms") or 0) / 1000, 3))],
                ["Elapsed (s)", wrap_wpt(round((summary.get("elapsed_ms") or 0) / 1000, 3))],
            ]

            sum_table = Table(sum_rows, colWidths=[2.8 * inch, 3.0 * inch])
            sum_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(sum_table)
            elements.append(Spacer(1, 0.2 * inch))

        def add_view(title, view):
            if not view:
                return

            elements.append(Paragraph(title, wpt_heading))
            elements.append(Spacer(1, 0.1 * inch))

            timing = view.get("timing", {})
            vitals = view.get("vitals", {})
            network = view.get("network", {})

            timing_rows = [
                ["TTFB (ms)", wrap_wpt(timing.get("ttfb_ms", "N/A"))],
                ["DOMContentLoaded (ms)", wrap_wpt(timing.get("dom_content_loaded_ms", "N/A"))],
                ["Load Event (ms)", wrap_wpt(timing.get("load_event_ms", "N/A"))],
                ["First Paint (ms)", wrap_wpt(timing.get("first_paint_ms", "N/A"))],
                ["FCP (ms)", wrap_wpt(timing.get("first_contentful_paint_ms", "N/A"))],
                ["Elapsed (ms)", wrap_wpt(timing.get("elapsed_ms", "N/A"))],
            ]

            vitals_rows = [
                ["LCP (ms)", wrap_wpt(vitals.get("lcp_ms", "N/A"))],
                ["CLS", wrap_wpt(vitals.get("cls", "N/A"))],
                ["INP (ms)", wrap_wpt(vitals.get("inp_ms", "N/A"))],
            ]

            network_rows = [
                ["Resources", wrap_wpt(network.get("resource_count", "N/A"))],
                ["Transfer (KB)", wrap_wpt(network.get("transfer_kb", "N/A"))],
                ["Encoded (KB)", wrap_wpt(network.get("encoded_kb", "N/A"))],
            ]

            timing_table = Table(timing_rows, colWidths=[2.8 * inch, 3.0 * inch])
            timing_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            vitals_table = Table(vitals_rows, colWidths=[2.8 * inch, 3.0 * inch])
            vitals_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            network_table = Table(network_rows, colWidths=[2.8 * inch, 3.0 * inch])
            network_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))

            elements.append(timing_table)
            elements.append(Spacer(1, 0.12 * inch))
            elements.append(vitals_table)
            elements.append(Spacer(1, 0.12 * inch))
            elements.append(network_table)

            waterfall = view.get("waterfall") or []
            if waterfall:
                elements.append(Spacer(1, 0.3 * inch))
                elements.append(Paragraph("Top Resources (by order)", wpt_heading))
                elements.append(Spacer(1, 0.3 * inch))
                rows = [["Resource", "Initiator", "Start (ms)", "Duration (ms)", "Transfer (KB)"]]
                for res in waterfall[:12]:
                    rows.append([
                        Paragraph(res.get("name", "-"), wpt_body),
                        wrap_wpt(res.get("initiatorType", "-")),
                        wrap_wpt(round(res.get("startTime", 0), 2)),
                        wrap_wpt(round(res.get("duration", 0), 2)),
                        wrap_wpt(round((res.get("transferSize", 0) or 0) / 1024, 2)),
                    ])

                wf_table = Table(rows, colWidths=[2.8 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch, 0.9 * inch])
                wf_table.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.3, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3E8FF")),
                    ("FONTNAME", (0, 0), (-1, 0), "Montserrat-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Montserrat"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                elements.append(wf_table)
            elements.append(Spacer(1, 0.3 * inch))

        add_view("First View (Cold Cache)", wpt.get("first_view"))
        elements.append(Spacer(1, 0.3 * inch))
        add_view("Repeat View (Warm Cache)", wpt.get("repeat_view"))
        elements.append(Spacer(1, 0.3 * inch))

    # LIGHTHOUSE SECTION
    if isinstance(data.get("lighthouse"), dict):
        lh = data.get("lighthouse") or {}
        if lh.get("status") or lh.get("error"):
            elements.append(Spacer(1, 0.4 * inch))
            elements.append(SectionHeader("Lighthouse"))
            elements.append(Spacer(1, 0.2 * inch))

            lh_body = ParagraphStyle(
                name="lhBody",
                parent=body_style,
                fontSize=10,
                leading=14,
                wordWrap="CJK",
            )

            lh_heading = ParagraphStyle(
                name="lhHeading",
                fontName="Montserrat-Bold",
                fontSize=12,
            )

            def wrap_lh(val):
                if val is None or val == "":
                    return Paragraph("-", lh_body)
                if isinstance(val, list):
                    txt = ", ".join(str(v) for v in val) or "-"
                else:
                    txt = str(val)
                return Paragraph(txt, lh_body)

            cat = lh.get("categories") or {}
            metrics = lh.get("metrics") or {}

            header_rows = [
                ["Status", wrap_lh(lh.get("status", "N/A"))],
                ["Score", wrap_lh(lh.get("score", "N/A"))],
                ["Grade", wrap_lh(lh.get("grade", "N/A"))],
            ]

            header_table = Table(header_rows, colWidths=[2.8 * inch, 3.0 * inch])
            header_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#7C3AED")),
                ("FONTNAME", (0, 0), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(header_table)
            elements.append(Spacer(1, 0.15 * inch))

            cat_rows = [["Category", "Score"]]
            for k, label in [
                ("performance", "Performance"),
                ("accessibility", "Accessibility"),
                ("best_practices", "Best Practices"),
                ("seo", "SEO"),
                ("pwa", "PWA"),
            ]:
                cat_rows.append([label, wrap_lh(cat.get(k, "N/A"))])

            cat_table = Table(cat_rows, colWidths=[2.8 * inch, 3.0 * inch])
            cat_table.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3E8FF")),
                ("FONTNAME", (0, 0), (-1, 0), "Montserrat-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Montserrat"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            elements.append(cat_table)

            if metrics:
                elements.append(Spacer(1, 0.15 * inch))
                elements.append(Paragraph("Key Metrics", lh_heading))
                elements.append(Spacer(1, 0.3 * inch))
                metric_rows = [["Metric", "Value"]]
                for label, key in [
                    ("FCP", "first-contentful-paint"),
                    ("LCP", "largest-contentful-paint"),
                    ("CLS", "cumulative-layout-shift"),
                    ("TBT", "total-blocking-time"),
                    ("TTI", "interactive"),
                    ("Speed Index", "speed-index"),
                ]:
                    metric_rows.append([label, wrap_lh(metrics.get(key, "N/A"))])

                metric_table = Table(metric_rows, colWidths=[2.8 * inch, 3.0 * inch])
                metric_table.setStyle(TableStyle([
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#F3E8FF")),
                    ("FONTNAME", (0, 0), (-1, 0), "Montserrat-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Montserrat"),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))
                elements.append(metric_table)

    elements.append(PageBreak())

    # AI ENGINEERING ANALYSIS (moved after key metrics/security/ssl/wpt/lh)
    elements.append(SectionHeader("AI Engineering Analysis"))
    elements.append(Spacer(1, 0.6 * inch))

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
