import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from md_to_html import parse_blocks

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

if __name__ == "__main__":
    test_parse_headers()
    test_parse_table()
    test_parse_table_alignment()
    test_parse_code_block()
    test_parse_blockquote()
    test_parse_unordered_list()
    test_parse_horizontal_rule()
    test_parse_mixed()
    print("All block parsing tests passed!")
