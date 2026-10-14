"""Measure reader-facing Markdown body text without markup or metadata."""

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from markdown_it import MarkdownIt


PR_LINES = {
    "※本記事には広告・PRが含まれます。",
    "※この記事には広告・PRが含まれます。",
    "本記事には広告・PRが含まれます。",
}
URL_PATTERN = re.compile(r"https?://[^\s<>]+")


class VisibleHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hidden = []
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "pre", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.hidden.append(tag)

    def handle_endtag(self, tag):
        if self.hidden and self.hidden[-1] == tag:
            self.hidden.pop()

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def count_text(text):
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped in PR_LINES:
            continue
        if stripped.startswith("Amazonのアソシエイトとして") and stripped.endswith("収入を得ています。"):
            continue
        lines.append(URL_PATTERN.sub("", line))
    return sum(not char.isspace() for char in "".join(lines))


def measure(markdown):
    tokens = MarkdownIt("commonmark", {"html": True}).parse(markdown)
    sections = []
    current = {"heading": None, "level": None, "characters": 0}
    sections.append(current)
    total = 0
    for index, token in enumerate(tokens):
        if token.type == "heading_open":
            if token.tag in {"h2", "h3"}:
                current = {
                    "heading": tokens[index + 1].content,
                    "level": int(token.tag[1:]),
                    "characters": 0,
                }
                sections.append(current)
            continue
        if token.type == "inline" and (index == 0 or tokens[index - 1].type != "heading_open"):
            autolink = False
            html = VisibleHTML()
            for child in token.children or []:
                if child.type == "link_open":
                    autolink = child.markup == "autolink"
                elif child.type == "link_close":
                    autolink = False
                elif child.type in {"text", "code_inline"} and not autolink:
                    html.feed(child.content.replace("&", "&amp;").replace("<", "&lt;"))
                elif child.type in {"softbreak", "hardbreak"}:
                    html.feed("\n")
                elif child.type == "html_inline":
                    html.feed(child.content)
            html.close()
            amount = count_text("".join(html.parts))
        elif token.type == "html_block":
            html = VisibleHTML()
            html.feed(token.content)
            html.close()
            amount = count_text("".join(html.parts))
        else:
            continue
        total += amount
        current["characters"] += amount
    return {"body_characters": total, "sections": sections}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--min-chars", type=int, default=5000)
    args = parser.parse_args()
    if args.min_chars < 1:
        parser.error("--min-chars must be positive")
    results = []
    failed = False
    errors = False
    for path in args.files:
        try:
            result = measure(path.read_text(encoding="utf-8"))
            result.update(path=str(path), minimum=args.min_chars)
            result["passed"] = result["body_characters"] >= args.min_chars
            failed |= not result["passed"]
        except (OSError, UnicodeError) as error:
            result = {"path": str(path), "error": str(error), "passed": False}
            errors = True
        results.append(result)
    print(json.dumps({"articles": results}, ensure_ascii=False, indent=2))
    return 2 if errors else 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
