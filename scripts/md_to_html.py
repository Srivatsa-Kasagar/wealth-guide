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
