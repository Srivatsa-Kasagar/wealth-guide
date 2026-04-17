import sys, os, tempfile
sys.path.insert(0, os.path.dirname(__file__))
from md_to_html import parse_blocks, parse_inline, render_blocks_to_html, generate_gauge_svg, generate_projection_svg, parse_currency

def test_parse_headers():
    md = "# Title\n\nSome text\n\n## Section\n\n### Subsection"
    blocks = parse_blocks(md)
    assert blocks[0] == {"type": "header", "level": 1, "text": "Title"}
    assert blocks[1] == {"type": "paragraph", "lines": ["Some text"]}
    assert blocks[2] == {"type": "header", "level": 2, "text": "Section"}
    assert blocks[3] == {"type": "header", "level": 3, "text": "Subsection"}

def test_parse_table():
    md = "| Name | Value |\n|------|-------|\n| A | 100 |\n| B | 200 |"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "table"
    assert blocks[0]["headers"] == ["Name", "Value"]
    assert blocks[0]["rows"] == [["A", "100"], ["B", "200"]]
    assert blocks[0]["alignments"] == ["left", "left"]

def test_parse_table_alignment():
    md = "| Left | Center | Right |\n|:-----|:------:|------:|\n| a | b | c |"
    blocks = parse_blocks(md)
    assert blocks[0]["alignments"] == ["left", "center", "right"]

def test_parse_code_block():
    md = "```\n[====-----] 75/100\n Savings ██████\n```"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "code"
    assert "[====-----] 75/100" in blocks[0]["content"]

def test_parse_blockquote():
    md = "> **Prepared:** 16 April 2026\n> Important disclaimer"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "blockquote"
    assert len(blocks[0]["lines"]) == 2

def test_parse_unordered_list():
    md = "- Item one\n- Item two\n- Item three"
    blocks = parse_blocks(md)
    assert blocks[0]["type"] == "list"
    assert blocks[0]["items"] == ["Item one", "Item two", "Item three"]

def test_parse_horizontal_rule():
    md = "Some text\n\n---\n\nMore text"
    blocks = parse_blocks(md)
    assert blocks[1]["type"] == "hr"

def test_parse_mixed():
    md = """# Title

> A quote

| H1 | H2 |
|----|-----|
| a  | b   |

- list item

```
code
```

A paragraph."""
    blocks = parse_blocks(md)
    types = [b["type"] for b in blocks]
    assert types == ["header", "blockquote", "table", "list", "code", "paragraph"]

def test_inline_bold():
    assert "<strong>hello</strong>" in parse_inline("**hello** world")

def test_inline_link():
    result = parse_inline("[click](https://example.com)")
    assert 'href="https://example.com"' in result
    assert 'target="_blank"' in result
    assert ">click</a>" in result

def test_inline_code():
    assert "<code>Section 80C</code>" in parse_inline("`Section 80C` deduction")

def test_inline_combined():
    result = parse_inline("**Bold** and `code` and [link](url)")
    assert "<strong>Bold</strong>" in result
    assert "<code>code</code>" in result
    assert "<a " in result

def test_render_header():
    blocks = [{"type": "header", "level": 2, "text": "Section Title"}]
    html = render_blocks_to_html(blocks)
    assert "<h2" in html
    assert "Section Title" in html

def test_render_table():
    blocks = [{
        "type": "table",
        "headers": ["Name", "Value"],
        "rows": [["A", "₹1,00,000"]],
        "alignments": ["left", "right"]
    }]
    html = render_blocks_to_html(blocks)
    assert "<table" in html
    assert "<thead>" in html
    assert "<tbody>" in html
    assert "₹1,00,000" in html

def test_render_paragraph():
    blocks = [{"type": "paragraph", "lines": ["Hello world"]}]
    html = render_blocks_to_html(blocks)
    assert "<p>" in html
    assert "Hello world" in html

def test_render_code():
    blocks = [{"type": "code", "content": "def hello():\n    return 42"}]
    html = render_blocks_to_html(blocks)
    assert "<pre>" in html
    assert "<code>" in html

def test_render_blockquote():
    blocks = [{"type": "blockquote", "lines": ["A quote line"]}]
    html = render_blocks_to_html(blocks)
    assert "<blockquote>" in html

def test_render_list():
    blocks = [{"type": "list", "items": ["One", "Two"]}]
    html = render_blocks_to_html(blocks)
    assert "<ul>" in html
    assert "<li>" in html

def test_render_hr():
    blocks = [{"type": "hr"}]
    html = render_blocks_to_html(blocks)
    assert "<hr" in html

def test_render_verdict_badges():
    blocks = [{"type": "paragraph", "lines": ["Verdict: RECOMMENDED"]}]
    html = render_blocks_to_html(blocks)
    assert "verdict-recommended" in html

def test_convert_file_creates_html():
    md_content = """# Test Roadmap

> **Prepared:** 16 April 2026

## 1. Executive Summary

Some summary text with **bold** and [link](https://example.com).

| Name | Value |
|------|-------|
| A    | 100   |

---

## 2. Details

- Item one
- Item two

```
[====-----] 75/100
```
"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(md_content)
        md_path = f.name

    from md_to_html import convert_file
    html_path = convert_file(md_path)

    assert html_path.endswith(".html")
    assert os.path.exists(html_path)

    with open(html_path) as f:
        html = f.read()

    assert "<!DOCTYPE html>" in html
    assert "<style>" in html
    assert "max-width" in html
    assert "@media print" in html
    assert "Test Roadmap" in html
    assert "<table" in html
    assert "<blockquote>" in html

    os.unlink(md_path)
    os.unlink(html_path)


def test_gauge_svg_basic():
    svg = generate_gauge_svg(75)
    assert "<svg" in svg
    assert "75" in svg
    assert "viewBox" in svg

def test_gauge_svg_low_score():
    svg = generate_gauge_svg(25)
    assert "<svg" in svg
    assert "25" in svg

def test_gauge_svg_perfect():
    svg = generate_gauge_svg(100)
    assert "<svg" in svg
    assert "100" in svg

def test_gauge_replaces_ascii():
    md = "### 2.3 Financial Health Score: 75/100\n\n```\n[===============-----------] 75/100\n Savings ██████  Debt ████  Investing █████  Protection ███\n```"
    blocks = parse_blocks(md)
    html = render_blocks_to_html(blocks)
    assert "<svg" in html
    assert "<pre>" not in html  # ASCII replaced, not rendered as code

def test_parse_currency_inr():
    assert parse_currency("₹1,17,22,500") == 11722500
    assert parse_currency("₹7.54 Cr") == 75400000
    assert parse_currency("₹35.8L") == 3580000

def test_parse_currency_usd():
    assert parse_currency("$150,000") == 150000
    assert parse_currency("$1,200,000") == 1200000

def test_parse_currency_plain():
    assert parse_currency("100000") == 100000

def test_projection_svg():
    years = ["2027", "2028", "2029"]
    conservative = [1172250, 1682280, 2233112]
    base = [1193250, 1740757, 2348490]
    optimistic = [1214250, 1800495, 2468814]
    svg = generate_projection_svg(years, conservative, base, optimistic)
    assert "<svg" in svg
    assert "polyline" in svg
    assert "Conservative" in svg

def test_projection_detected_in_table():
    md = """| Year | Age | Phase | Conservative (8%) | Base Case (11%) | Optimistic (14%) |
|------|-----|-------|-------------------|-----------------|------------------|
| 2027 | 36 | Growth | ₹1,17,22,500 | ₹1,19,32,500 | ₹1,21,42,500 |
| 2028 | 37 | Growth | ₹1,68,22,800 | ₹1,74,07,575 | ₹1,80,04,950 |"""
    blocks = parse_blocks(md)
    html = render_blocks_to_html(blocks)
    assert "<svg" in html
    assert "<table" in html

if __name__ == "__main__":
    test_parse_headers()
    test_parse_table()
    test_parse_table_alignment()
    test_parse_code_block()
    test_parse_blockquote()
    test_parse_unordered_list()
    test_parse_horizontal_rule()
    test_parse_mixed()
    test_inline_bold()
    test_inline_link()
    test_inline_code()
    test_inline_combined()
    test_render_header()
    test_render_table()
    test_render_paragraph()
    test_render_code()
    test_render_blockquote()
    test_render_list()
    test_render_hr()
    test_render_verdict_badges()
    test_convert_file_creates_html()
    test_gauge_svg_basic()
    test_gauge_svg_low_score()
    test_gauge_svg_perfect()
    test_gauge_replaces_ascii()
    test_parse_currency_inr()
    test_parse_currency_usd()
    test_parse_currency_plain()
    test_projection_svg()
    test_projection_detected_in_table()
    print("All parser + renderer + assembly + gauge chart + projection chart tests passed!")
