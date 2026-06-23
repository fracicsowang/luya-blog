#!/usr/bin/env python3
"""
gen_blog_sitemap.py — Build /site/blog/sitemap.xml from the markdown files
currently in /site-src/src/content/blog/. Only published articles appear
in the sitemap (the publish queue copies them into content/ on their
release date, so this naturally stays in sync).

Called by daily_publish.sh after the rsync step.
"""
from __future__ import annotations
import datetime as dt
import re
import xml.sax.saxutils as sax
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "site-src" / "src" / "content" / "blog"
OUT = ROOT / "site" / "sitemap.xml"
SITE = "https://blog.luyaxyz.com"


def parse_date(md: str) -> str:
    m = re.search(r"^date:\s*([\d-]+)", md, flags=re.M)
    return m.group(1) if m else dt.date.today().isoformat()


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    entries: list[tuple[str, str]] = []
    if CONTENT.exists():
        for md in sorted(CONTENT.glob("*.md")):
            slug = md.stem
            date = parse_date(md.read_text(encoding="utf-8"))
            entries.append((slug, date))

    today = dt.date.today().isoformat()
    parts: list[str] = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        # The /blog/ landing
        f"  <url>\n    <loc>{SITE}/</loc>\n"
        f"    <lastmod>{today}</lastmod>\n"
        f"    <changefreq>weekly</changefreq>\n"
        f"    <priority>0.9</priority>\n  </url>",
    ]
    for slug, date in entries:
        url = f"{SITE}/{slug}/"
        parts.append(
            f"  <url>\n    <loc>{sax.escape(url)}</loc>\n"
            f"    <lastmod>{date}</lastmod>\n"
            f"    <changefreq>monthly</changefreq>\n"
            f"    <priority>0.7</priority>\n  </url>"
        )
    parts.append("</urlset>\n")

    OUT.write_text("\n".join(parts), encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({len(entries)} articles)")


if __name__ == "__main__":
    main()
