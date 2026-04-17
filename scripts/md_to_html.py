"""Converts Wealth Guide markdown roadmaps to styled HTML with inline SVG charts.

Usage: python3 md_to_html.py <roadmap.md>
Output: /path/to/roadmap.html (same directory, same name)

Zero dependencies — Python 3.8+ standard library only.
"""
import re
import os
import sys
import math
import html as html_module


def parse_blocks(md):
    """Parse markdown text into a list of typed block dicts.

    Block types: header, table, paragraph, code, blockquote, list, hr.
    """
    lines = md.split("\n")
    blocks = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Skip blank lines
        if line.strip() == "":
            i += 1
            continue

        # Code block (fenced with ```)
        if line.strip().startswith("```"):
            content_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                content_lines.append(lines[i])
                i += 1
            blocks.append({"type": "code", "content": "\n".join(content_lines)})
            i += 1  # skip closing ```
            continue

        # Table (line starts with |)
        if line.strip().startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            if len(table_lines) >= 2:
                headers = [c.strip() for c in table_lines[0].strip().strip("|").split("|")]
                sep_cells = [c.strip() for c in table_lines[1].strip().strip("|").split("|")]
                alignments = []
                for cell in sep_cells:
                    cell = cell.strip()
                    if cell.startswith(":") and cell.endswith(":"):
                        alignments.append("center")
                    elif cell.endswith(":"):
                        alignments.append("right")
                    else:
                        alignments.append("left")
                rows = []
                for tl in table_lines[2:]:
                    row = [c.strip() for c in tl.strip().strip("|").split("|")]
                    rows.append(row)
                blocks.append({
                    "type": "table",
                    "headers": headers,
                    "rows": rows,
                    "alignments": alignments
                })
            continue

        # Horizontal rule
        if re.match(r"^\s*-{3,}\s*$", line):
            blocks.append({"type": "hr"})
            i += 1
            continue

        # Header
        header_match = re.match(r"^(#{1,3})\s+(.+)$", line)
        if header_match:
            level = len(header_match.group(1))
            text = header_match.group(2).strip()
            blocks.append({"type": "header", "level": level, "text": text})
            i += 1
            continue

        # Blockquote
        if line.strip().startswith(">"):
            bq_lines = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                bq_lines.append(re.sub(r"^>\s?", "", lines[i]))
                i += 1
            blocks.append({"type": "blockquote", "lines": bq_lines})
            continue

        # Unordered list
        if re.match(r"^- ", line):
            items = []
            while i < len(lines) and re.match(r"^- ", lines[i]):
                items.append(lines[i][2:].strip())
                i += 1
            blocks.append({"type": "list", "items": items})
            continue

        # Paragraph (default)
        para_lines = []
        while i < len(lines) and lines[i].strip() != "" and not lines[i].strip().startswith(("#", "|", ">", "```")) and not re.match(r"^- ", lines[i]) and not re.match(r"^\s*-{3,}\s*$", lines[i]):
            para_lines.append(lines[i].strip())
            i += 1
        if para_lines:
            blocks.append({"type": "paragraph", "lines": para_lines})

    return blocks


def parse_inline(text):
    """Convert inline markdown (bold, links, code) to HTML."""
    parts = []
    remaining = text
    while "`" in remaining:
        before, _, after = remaining.partition("`")
        if "`" in after:
            code_content, _, after = after.partition("`")
            parts.append(_escape_and_inline(before))
            parts.append(f"<code>{html_module.escape(code_content)}</code>")
            remaining = after
        else:
            parts.append(_escape_and_inline(before + "`" + after))
            remaining = ""
            break
    if remaining:
        parts.append(_escape_and_inline(remaining))
    return "".join(parts)


def _escape_and_inline(text):
    """Apply bold and link transforms to text (no code spans here)."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" target="_blank">\1</a>',
        text
    )
    return text


def _slugify(text):
    """Create a URL-friendly id from header text."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"[\s]+", "-", slug).strip("-")


def _detect_verdict(text):
    """Wrap verdict keywords in styled spans."""
    text = re.sub(
        r"\bRECOMMENDED\b",
        '<span class="verdict verdict-recommended">RECOMMENDED</span>',
        text
    )
    text = re.sub(
        r"\bPROCEED WITH CAUTION\b",
        '<span class="verdict verdict-caution">PROCEED WITH CAUTION</span>',
        text
    )
    text = re.sub(
        r"\bNOT SUITABLE[^<]*",
        lambda m: f'<span class="verdict verdict-not-suitable">{m.group(0).strip()}</span>',
        text
    )
    return text


def generate_gauge_svg(score):
    """Generate a semi-circular gauge SVG for the health score."""
    score = max(0, min(100, score))
    cx, cy, r = 150, 140, 110
    angle = math.pi * (1 - score / 100)
    end_x = cx + r * math.cos(angle)
    end_y = cy - r * math.sin(angle)

    bg_arc = f'M {cx - r} {cy} A {r} {r} 0 1 1 {cx + r} {cy}'

    large_arc = 1 if score > 50 else 0
    score_arc = f'M {cx - r} {cy} A {r} {r} 0 {large_arc} 1 {end_x:.1f} {end_y:.1f}'

    if score < 40:
        color = "#e74c3c"
    elif score < 70:
        color = "#f39c12"
    else:
        color = "#27ae60"

    ticks = ""
    for val in [0, 25, 50, 75, 100]:
        a = math.pi * (1 - val / 100)
        tx = cx + (r + 15) * math.cos(a)
        ty = cy - (r + 15) * math.sin(a)
        ticks += f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" font-size="11" fill="#999">{val}</text>\n'

    needle_len = r - 15
    nx = cx + needle_len * math.cos(angle)
    ny = cy - needle_len * math.sin(angle)

    svg = f'''<div class="chart-container">
<svg viewBox="0 0 300 180" xmlns="http://www.w3.org/2000/svg">
  <path d="{bg_arc}" fill="none" stroke="#e9ecef" stroke-width="20" stroke-linecap="round"/>
  <path d="{score_arc}" fill="none" stroke="{color}" stroke-width="20" stroke-linecap="round"/>
  <line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{color}" stroke-width="3" stroke-linecap="round"/>
  <circle cx="{cx}" cy="{cy}" r="6" fill="{color}"/>
  <text x="{cx}" y="{cy + 35}" text-anchor="middle" font-size="28" font-weight="bold" fill="{color}">{score}/100</text>
  {ticks}
</svg>
</div>'''
    return svg


def parse_currency(value_str):
    """Strip currency symbols and formatting, return float."""
    cleaned = value_str.strip()
    cleaned = re.sub(r"[₹$\s]", "", cleaned)
    upper = cleaned.upper().rstrip(".")
    if upper.endswith("CR"):
        num = float(re.sub(r"[,]", "", upper[:-2]))
        return round(num * 10000000)
    if upper.endswith("L"):
        num = float(re.sub(r"[,]", "", upper[:-1]))
        return round(num * 100000)
    cleaned = re.sub(r"[,]", "", cleaned)
    return float(cleaned)


def _format_axis_value(value):
    """Format a numeric value for axis labels."""
    if value >= 10000000:
        return f"₹{value/10000000:.1f}Cr"
    if value >= 100000:
        return f"₹{value/100000:.0f}L"
    if value >= 1000:
        return f"{value/1000:.0f}K"
    return str(int(value))


def generate_projection_svg(years, conservative, base, optimistic):
    """Generate a 3-line SVG chart for wealth projections."""
    if len(years) < 2:
        return ""

    w, h = 780, 380
    pad_l, pad_r, pad_t, pad_b = 80, 30, 30, 50
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    all_vals = conservative + base + optimistic
    min_val = min(all_vals) * 0.9
    max_val = max(all_vals) * 1.05
    val_range = max_val - min_val if max_val != min_val else 1

    def x_pos(i):
        return pad_l + (i / (len(years) - 1)) * plot_w

    def y_pos(v):
        return pad_t + plot_h - ((v - min_val) / val_range) * plot_h

    def points(values):
        return " ".join(f"{x_pos(i):.1f},{y_pos(v):.1f}" for i, v in enumerate(values))

    colors = {"Conservative": "#e74c3c", "Base Case": "#3498db", "Optimistic": "#27ae60"}

    grid = ""
    for i in range(6):
        val = min_val + (val_range * i / 5)
        y = y_pos(val)
        grid += f'<line x1="{pad_l}" y1="{y:.1f}" x2="{w - pad_r}" y2="{y:.1f}" stroke="#e9ecef" stroke-width="1"/>\n'
        grid += f'<text x="{pad_l - 10}" y="{y:.1f}" text-anchor="end" font-size="11" fill="#999" dominant-baseline="middle">{_format_axis_value(val)}</text>\n'

    x_labels = ""
    step = max(1, len(years) // 6)
    for i, yr in enumerate(years):
        if i % step == 0 or i == len(years) - 1:
            x_labels += f'<text x="{x_pos(i):.1f}" y="{h - 10}" text-anchor="middle" font-size="11" fill="#999">{yr}</text>\n'

    dots = ""
    for values, color in [(conservative, colors["Conservative"]), (base, colors["Base Case"]), (optimistic, colors["Optimistic"])]:
        for i, v in enumerate(values):
            dots += f'<circle cx="{x_pos(i):.1f}" cy="{y_pos(v):.1f}" r="3" fill="{color}"/>\n'

    legend_y = h - 5
    legend = f'''
    <rect x="{pad_l}" y="{legend_y}" width="12" height="3" fill="{colors['Conservative']}"/>
    <text x="{pad_l + 16}" y="{legend_y + 3}" font-size="11" fill="#666">Conservative</text>
    <rect x="{pad_l + 120}" y="{legend_y}" width="12" height="3" fill="{colors['Base Case']}"/>
    <text x="{pad_l + 136}" y="{legend_y + 3}" font-size="11" fill="#666">Base Case</text>
    <rect x="{pad_l + 240}" y="{legend_y}" width="12" height="3" fill="{colors['Optimistic']}"/>
    <text x="{pad_l + 256}" y="{legend_y + 3}" font-size="11" fill="#666">Optimistic</text>
    '''

    svg = f'''<div class="chart-container">
<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  {grid}
  {x_labels}
  <polyline points="{points(conservative)}" fill="none" stroke="{colors['Conservative']}" stroke-width="2.5"/>
  <polyline points="{points(base)}" fill="none" stroke="{colors['Base Case']}" stroke-width="2.5"/>
  <polyline points="{points(optimistic)}" fill="none" stroke="{colors['Optimistic']}" stroke-width="2.5"/>
  {dots}
  {legend}
</svg>
</div>'''
    return svg


def _detect_chart_type(headers, rows):
    """Match table headers to determine if a chart should be generated."""
    header_text = " ".join(headers).lower()
    if "conservative" in header_text and ("base" in header_text or "moderate" in header_text) and "optimistic" in header_text:
        return "projection_line"
    if ("category" in header_text or "item" in header_text) and ("value" in header_text or "inr" in header_text or "usd" in header_text):
        row_text = " ".join(" ".join(r) for r in rows).lower()
        if "savings" in row_text or "investment" in row_text:
            return "net_worth_donut"
    if "monthly" in header_text and "annual" in header_text:
        row_text = " ".join(" ".join(r) for r in rows).lower()
        if "income" in row_text or "surplus" in row_text:
            return "cashflow_waterfall"
    return None


def _build_projection_chart(headers, rows):
    """Extract projection data from table and generate line chart."""
    try:
        h_lower = [h.lower() for h in headers]
        year_idx = next(i for i, h in enumerate(h_lower) if "year" in h)
        con_idx = next(i for i, h in enumerate(h_lower) if "conservative" in h)
        base_idx = next(i for i, h in enumerate(h_lower) if "base" in h)
        opt_idx = next(i for i, h in enumerate(h_lower) if "optimistic" in h)

        years, conservative, base, optimistic = [], [], [], []
        for row in rows:
            cleaned_row = [cell.replace("**", "") for cell in row]
            try:
                years.append(cleaned_row[year_idx].strip())
                conservative.append(parse_currency(cleaned_row[con_idx]))
                base.append(parse_currency(cleaned_row[base_idx]))
                optimistic.append(parse_currency(cleaned_row[opt_idx]))
            except (ValueError, IndexError):
                continue

        if len(years) >= 2:
            return generate_projection_svg(years, conservative, base, optimistic)
    except (StopIteration, ValueError, IndexError):
        pass
    return None


def generate_donut_svg(assets, debts):
    """Generate a donut chart SVG for net worth breakdown."""
    if not assets:
        return ""

    cx, cy, r_outer, r_inner = 200, 180, 140, 85
    total_assets = sum(v for _, v in assets)
    if total_assets == 0:
        return ""

    asset_colors = ["#3498db", "#2ecc71", "#1abc9c", "#9b59b6", "#f1c40f"]
    debt_colors = ["#e74c3c", "#e67e22", "#c0392b"]

    paths = ""
    labels_svg = ""
    angle_start = -math.pi / 2

    for i, (label, value) in enumerate(assets):
        fraction = value / total_assets
        angle_end = angle_start + fraction * 2 * math.pi
        color = asset_colors[i % len(asset_colors)]

        x1 = cx + r_outer * math.cos(angle_start)
        y1 = cy + r_outer * math.sin(angle_start)
        x2 = cx + r_outer * math.cos(angle_end)
        y2 = cy + r_outer * math.sin(angle_end)
        ix1 = cx + r_inner * math.cos(angle_end)
        iy1 = cy + r_inner * math.sin(angle_end)
        ix2 = cx + r_inner * math.cos(angle_start)
        iy2 = cy + r_inner * math.sin(angle_start)

        large_arc = 1 if fraction > 0.5 else 0

        path = (
            f"M {x1:.1f} {y1:.1f} "
            f"A {r_outer} {r_outer} 0 {large_arc} 1 {x2:.1f} {y2:.1f} "
            f"L {ix1:.1f} {iy1:.1f} "
            f"A {r_inner} {r_inner} 0 {large_arc} 0 {ix2:.1f} {iy2:.1f} Z"
        )
        paths += f'<path d="{path}" fill="{color}"/>\n'

        mid_angle = (angle_start + angle_end) / 2
        label_r = r_outer + 20
        lx = cx + label_r * math.cos(mid_angle)
        ly = cy + label_r * math.sin(mid_angle)
        anchor = "start" if lx > cx else "end"
        short_label = label.split("(")[0].strip()
        labels_svg += f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="{anchor}" font-size="11" fill="#666">{short_label}</text>\n'

        angle_start = angle_end

    net_worth = total_assets - sum(v for _, v in debts)
    center_text = _format_axis_value(net_worth)
    center_svg = f'''
    <text x="{cx}" y="{cy - 5}" text-anchor="middle" font-size="13" fill="#999">Net Worth</text>
    <text x="{cx}" y="{cy + 18}" text-anchor="middle" font-size="20" font-weight="bold" fill="#1a2332">{center_text}</text>
    '''

    debt_bars = ""
    if debts:
        bar_y = cy + r_outer + 40
        max_debt = max(v for _, v in debts) if debts else 1
        bar_max_w = 250
        for j, (label, value) in enumerate(debts):
            by = bar_y + j * 30
            bw = (value / max_debt) * bar_max_w if max_debt > 0 else 0
            color = debt_colors[j % len(debt_colors)]
            short_label = label.replace("Less: ", "").split("(")[0].strip()
            debt_bars += f'<rect x="{cx - bar_max_w // 2}" y="{by}" width="{bw:.1f}" height="18" rx="3" fill="{color}" opacity="0.8"/>\n'
            debt_bars += f'<text x="{cx - bar_max_w // 2 - 5}" y="{by + 13}" text-anchor="end" font-size="11" fill="#666">{short_label}</text>\n'
            debt_bars += f'<text x="{cx - bar_max_w // 2 + bw + 5:.1f}" y="{by + 13}" font-size="11" fill="#666">{_format_axis_value(value)}</text>\n'

    total_h = cy + r_outer + 40 + len(debts) * 30 + 20 if debts else cy + r_outer + 40
    svg = f'''<div class="chart-container">
<svg viewBox="0 0 400 {total_h}" xmlns="http://www.w3.org/2000/svg">
  {paths}
  {labels_svg}
  {center_svg}
  {debt_bars}
</svg>
</div>'''
    return svg


def _build_net_worth_chart(rows):
    """Extract net worth data from table rows and generate donut chart."""
    try:
        assets = []
        debts = []
        for row in rows:
            if len(row) < 2:
                continue
            label = row[0].replace("**", "").strip()
            value_str = row[1].replace("**", "").strip()

            if "net worth" in label.lower() or "total" in label.lower():
                continue

            try:
                if value_str.startswith("-") or "less:" in label.lower():
                    val = abs(parse_currency(value_str.lstrip("-")))
                    debts.append((label, val))
                else:
                    val = parse_currency(value_str)
                    if val > 0:
                        assets.append((label, val))
            except (ValueError, IndexError):
                continue

        if assets:
            return generate_donut_svg(assets, debts)
    except Exception:
        pass
    return None


def generate_waterfall_svg(items):
    """Generate a waterfall bar chart SVG for cash flow."""
    if not items:
        return ""

    w, h = 580, 330
    pad_l, pad_r, pad_t, pad_b = 100, 30, 30, 60
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b

    income = items[0][1] if items else 1
    if income == 0:
        return ""

    bar_w = min(80, plot_w // (len(items) * 2))
    gap = (plot_w - bar_w * len(items)) / (len(items) + 1)

    running = 0
    bars = ""
    connectors = ""
    labels = ""

    for i, (label, value, item_type) in enumerate(items):
        x = pad_l + gap + i * (bar_w + gap)

        if item_type == "income":
            bar_h = plot_h
            y = pad_t
            running = value
            color = "#27ae60"
        elif item_type == "expense":
            bar_h = (value / income) * plot_h
            y = pad_t + ((income - running) / income) * plot_h
            running -= value
            color = "#e74c3c"
        else:  # surplus
            bar_h = (value / income) * plot_h
            y = pad_t + plot_h - bar_h
            color = "#27ae60"

        bars += f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w}" height="{bar_h:.1f}" rx="3" fill="{color}" opacity="0.85"/>\n'

        val_label = _format_axis_value(value)
        label_y = y - 8 if item_type != "expense" else y + bar_h + 15
        bars += f'<text x="{x + bar_w / 2:.1f}" y="{label_y:.1f}" text-anchor="middle" font-size="12" font-weight="bold" fill="{color}">{val_label}</text>\n'

        short_label = label.replace("**", "").strip()
        if len(short_label) > 12:
            short_label = short_label[:12] + "..."
        labels += f'<text x="{x + bar_w / 2:.1f}" y="{h - 15}" text-anchor="middle" font-size="11" fill="#666">{short_label}</text>\n'

        if i < len(items) - 1 and item_type != "surplus":
            next_x = pad_l + gap + (i + 1) * (bar_w + gap)
            if item_type == "income":
                conn_y = y + bar_h
            else:
                conn_y = y + bar_h
            connectors += f'<line x1="{x + bar_w:.1f}" y1="{conn_y:.1f}" x2="{next_x:.1f}" y2="{conn_y:.1f}" stroke="#ccc" stroke-width="1" stroke-dasharray="4,3"/>\n'

    svg = f'''<div class="chart-container">
<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">
  {connectors}
  {bars}
  {labels}
</svg>
</div>'''
    return svg


def _build_cashflow_chart(rows):
    """Extract cash flow data from table rows and generate waterfall chart."""
    try:
        items = []
        for row in rows:
            if len(row) < 2:
                continue
            label = row[0].replace("**", "").strip()
            value_str = row[1].replace("**", "").strip()
            try:
                value = parse_currency(value_str)
            except (ValueError, IndexError):
                continue

            label_lower = label.lower()
            if "income" in label_lower and "sustainable" not in label_lower:
                items.append((label, value, "income"))
            elif "tax" in label_lower or "expense" in label_lower:
                items.append((label, value, "expense"))
            elif "surplus" in label_lower or "available" in label_lower:
                items.append((label, value, "surplus"))

        if items and any(t == "income" for _, _, t in items):
            return generate_waterfall_svg(items)
    except Exception:
        pass
    return None


def render_blocks_to_html(blocks):
    """Convert a list of block dicts to an HTML string."""
    parts = []
    for block in blocks:
        btype = block["type"]

        if btype == "header":
            slug = _slugify(block["text"])
            level = block["level"]
            text = _detect_verdict(parse_inline(block["text"]))
            parts.append(f'<h{level} id="{slug}">{text}</h{level}>')

        elif btype == "table":
            parts.append(_render_table(block))

        elif btype == "paragraph":
            text = " ".join(block["lines"])
            text = _detect_verdict(parse_inline(text))
            parts.append(f"<p>{text}</p>")

        elif btype == "code":
            content = block["content"]
            score_match = re.search(r"(\d+)/100", content)
            if score_match and re.search(r"\[=+", content):
                score = int(score_match.group(1))
                parts.append(generate_gauge_svg(score))
            else:
                escaped = html_module.escape(content)
                parts.append(f"<pre><code>{escaped}</code></pre>")

        elif btype == "blockquote":
            inner = "<br>".join(parse_inline(line) for line in block["lines"])
            parts.append(f"<blockquote>{inner}</blockquote>")

        elif btype == "list":
            items = "".join(f"<li>{_detect_verdict(parse_inline(item))}</li>" for item in block["items"])
            parts.append(f"<ul>{items}</ul>")

        elif btype == "hr":
            parts.append("<hr>")

    return "\n".join(parts)


def _render_table(block):
    """Render a table block to HTML with alignment and currency detection."""
    headers = block["headers"]
    rows = block["rows"]
    alignments = block.get("alignments", ["left"] * len(headers))

    while len(alignments) < len(headers):
        alignments.append("left")

    html_parts = ['<table>']

    html_parts.append("<thead><tr>")
    for i, h in enumerate(headers):
        align = f' style="text-align:{alignments[i]}"' if alignments[i] != "left" else ""
        html_parts.append(f"<th{align}>{_detect_verdict(parse_inline(h))}</th>")
    html_parts.append("</tr></thead>")

    html_parts.append("<tbody>")
    for row in rows:
        html_parts.append("<tr>")
        for i, cell in enumerate(row):
            align_str = alignments[i] if i < len(alignments) else "left"
            if re.search(r"[₹$]|^\s*-?[\d,]+\s*$", cell):
                align_str = "right"
            align = f' style="text-align:{align_str}"' if align_str != "left" else ""
            html_parts.append(f"<td{align}>{_detect_verdict(parse_inline(cell))}</td>")
        html_parts.append("</tr>")
    html_parts.append("</tbody></table>")

    # Generate chart if this table matches a known pattern
    chart_type = _detect_chart_type(headers, rows)
    if chart_type == "projection_line":
        chart_svg = _build_projection_chart(headers, rows)
        if chart_svg:
            html_parts.append(chart_svg)
    elif chart_type == "net_worth_donut":
        chart_svg = _build_net_worth_chart(rows)
        if chart_svg:
            html_parts.append(chart_svg)
    elif chart_type == "cashflow_waterfall":
        chart_svg = _build_cashflow_chart(rows)
        if chart_svg:
            html_parts.append(chart_svg)

    return "\n".join(html_parts)


CSS = """
:root {
    --navy: #1a2332;
    --text: #2c3e50;
    --bg: #ffffff;
    --table-header-bg: #f8f9fa;
    --table-stripe: #f8f9fa;
    --blockquote-border: #3498db;
    --link: #2980b9;
    --code-bg: #f4f5f7;
    --green-bg: #d4edda; --green-text: #155724;
    --amber-bg: #fff3cd; --amber-text: #856404;
    --red-bg: #f8d7da; --red-text: #721c24;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    color: var(--text);
    background: var(--bg);
    max-width: 900px;
    margin: 0 auto;
    padding: 2rem;
    line-height: 1.6;
}

h1, h2, h3 {
    color: var(--navy);
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
h1 { font-size: 2em; border-bottom: 3px solid var(--navy); padding-bottom: 0.3em; }
h2 { font-size: 1.5em; border-bottom: 1px solid #e0e0e0; padding-bottom: 0.2em; }
h3 { font-size: 1.2em; }

p { margin: 0.8em 0; }

table {
    width: 100%;
    border-collapse: collapse;
    margin: 1em 0;
    font-size: 0.9em;
}
thead th {
    background: var(--table-header-bg);
    font-weight: 600;
    padding: 0.6rem 1rem;
    border-bottom: 2px solid #dee2e6;
    text-align: left;
}
tbody td {
    padding: 0.6rem 1rem;
    border-bottom: 1px solid #e9ecef;
}
tbody tr:nth-child(even) { background: var(--table-stripe); }
tbody tr:hover { background: #e8f4f8; }

blockquote {
    border-left: 4px solid var(--blockquote-border);
    background: var(--table-stripe);
    padding: 1em 1.5em;
    margin: 1em 0;
    font-style: italic;
    border-radius: 0 4px 4px 0;
}

ul {
    margin: 0.8em 0;
    padding-left: 1.5em;
}
li { margin: 0.3em 0; }

pre {
    background: var(--code-bg);
    padding: 1em;
    border-radius: 6px;
    overflow-x: auto;
    margin: 1em 0;
    font-size: 0.85em;
}
code {
    font-family: "SF Mono", "Fira Code", "Consolas", monospace;
    font-size: 0.9em;
}
p code, li code, td code {
    background: var(--code-bg);
    padding: 0.15em 0.4em;
    border-radius: 3px;
}

a { color: var(--link); text-decoration: none; }
a:hover { text-decoration: underline; }

hr {
    border: none;
    border-top: 1px solid #e0e0e0;
    margin: 2em 0;
}

.verdict {
    display: inline-block;
    padding: 0.15em 0.6em;
    border-radius: 4px;
    font-weight: 600;
    font-size: 0.85em;
    letter-spacing: 0.02em;
}
.verdict-recommended { background: var(--green-bg); color: var(--green-text); }
.verdict-caution { background: var(--amber-bg); color: var(--amber-text); }
.verdict-not-suitable { background: var(--red-bg); color: var(--red-text); }

.chart-container {
    text-align: center;
    margin: 1.5em 0;
    padding: 1em;
    background: #fafbfc;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
}
.chart-container svg { max-width: 100%; height: auto; }

@media print {
    body { max-width: none; padding: 0; color: #000; }
    h2 { page-break-before: always; }
    h2:first-of-type { page-break-before: avoid; }
    table, .chart-container, pre, blockquote { page-break-inside: avoid; }
    a[href^="http"]::after { content: " (" attr(href) ")"; font-size: 0.8em; color: #666; }
    .chart-container { box-shadow: none; background: none; }
    @page { margin: 1.5cm; }
}
"""


def convert_file(md_path):
    """Read a markdown file, convert to styled HTML, save alongside it.

    Args:
        md_path: Path to the markdown file.

    Returns:
        Path to the generated HTML file.
    """
    with open(md_path, "r", encoding="utf-8") as f:
        md = f.read()

    blocks = parse_blocks(md)
    body = render_blocks_to_html(blocks)

    title = "Wealth Roadmap"
    for block in blocks:
        if block["type"] == "header" and block["level"] == 1:
            title = block["text"]
            break

    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html_module.escape(title)}</title>
<style>{CSS}</style>
</head>
<body>
{body}
</body>
</html>"""

    html_path = re.sub(r"\.md$", ".html", md_path)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    return html_path
