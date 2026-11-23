"""Artifacts: docs, decks, sheets, web apps — built locally as files."""
import csv
import html
import io
from pathlib import Path


def make_doc(title: str, body: str, out: str) -> str:
    Path(out).write_text(
        f"<!doctype html><html><head><meta charset=utf-8><title>{html.escape(title)}</title>"
        f"<style>body{{font-family:system-ui;max-width:760px;margin:40px auto;padding:0 16px;line-height:1.6}}</style></head>"
        f"<body><h1>{html.escape(title)}</h1><p>{html.escape(body).replace(chr(10), '<br>')}</p></body></html>",
        encoding="utf-8")
    return f"made {out}"


def make_deck(title: str, slides: list[str], out: str) -> str:
    parts = [f"<!doctype html><html><head><meta charset=utf-8><title>{html.escape(title)}</title>"
             "<style>body{font-family:system-ui}.slide{border:1px solid #ccc;border-radius:12px;padding:40px;margin:20px;font-size:28px}</style></head><body>"]
    parts.append(f"<div class=slide><h1>{html.escape(title)}</h1></div>")
    for s in slides:
        parts.append(f"<div class=slide>{html.escape(s)}</div>")
    parts.append("</body></html>")
    Path(out).write_text("\n".join(parts), encoding="utf-8")
    return f"made {out} ({len(slides)+1} slides)"


def make_sheet(rows: list[list[str]], out: str) -> str:
    buf = io.StringIO()
    csv.writer(buf).writerows(rows)
    Path(out).write_text(buf.getvalue(), encoding="utf-8")
    return f"made {out} ({len(rows)} rows)"


def make_webapp(title: str, body_html: str, out: str) -> str:
    Path(out).write_text(
        f"<!doctype html><html><head><meta charset=utf-8><meta name=viewport content='width=device-width,initial-scale=1'>"
        f"<title>{html.escape(title)}</title></head><body>{body_html}</body></html>",
        encoding="utf-8")
    return f"made {out}"
