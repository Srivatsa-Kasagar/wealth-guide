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
            escaped = html_module.escape(block["content"])
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
