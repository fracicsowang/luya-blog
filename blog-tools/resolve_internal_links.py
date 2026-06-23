#!/usr/bin/env python3
# resolve_internal_links.py — runs during daily_publish before Astro build.
#
# The blog-drafts/ corpus is fully cross-linked, but publication is staggered
# (a few slugs per day from publish-queue.yml). Links from a published article
# to an unpublished target therefore 404. This script does two things on every
# build:
#
#   1. Refresh each already-published article in site-src/src/content/blog/
#      from its master in blog-drafts/. That way, when a target later goes
#      live, the next build re-resolves the link to it.
#   2. Walk all markdown links of the form [text](/blog/<slug>/) and, if the
#      target slug is not in the current published set, strip the link
#      wrapper — keep the visible text, drop the anchor. Anchors and
#      trailing slashes are tolerated. The frontmatter `internal_links`
#      array is also filtered down to currently-published targets.
#
# wire_figures.py must run AFTER this script, because step 1 overwrites the
# content collection with raw masters and would otherwise blow away its
# figure-markup edits.

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFTS = ROOT / "blog-drafts"
CONTENT = ROOT / "site-src" / "src" / "content" / "blog"
QUEUE = ROOT / "publish-queue.yml"

LINK_RE = re.compile(
    r"\[([^\]]+)\]\(/blog/([a-z0-9-]+)/?(#[^)]*)?\)"
)
FRONTMATTER_LINKS_RE = re.compile(
    r'^(internal_links:\s*\[)([^\]]*)(\])', re.MULTILINE
)
FRONTMATTER_DATE_RE = re.compile(
    r'^date:\s*\S+\s*$', re.MULTILINE
)
SLUG_FROM_URL_RE = re.compile(r"^/blog/([a-z0-9-]+)/?")
QUEUE_DATE_RE = re.compile(r'^"(\d{4}-\d{2}-\d{2})":\s*$')
QUEUE_SLUG_RE = re.compile(r'^\s*-\s+([a-z0-9-]+)\s*$')


def published_slugs() -> set[str]:
    return {p.stem for p in CONTENT.glob("*.md")}


def queue_publish_dates() -> dict[str, str]:
    """Parse publish-queue.yml into {slug: 'YYYY-MM-DD'}.

    The queue is the canonical source for each article's real publish date.
    Frontmatter `date:` in blog-drafts/ encodes the draft authoring date
    (all 100 drafts share 2026-05-09) and would otherwise leak into the
    rendered HTML and the blog-index sort.
    """
    if not QUEUE.exists():
        return {}
    mapping: dict[str, str] = {}
    current_date: str | None = None
    for line in QUEUE.read_text().splitlines():
        dm = QUEUE_DATE_RE.match(line)
        if dm:
            current_date = dm.group(1)
            continue
        sm = QUEUE_SLUG_RE.match(line)
        if sm and current_date:
            slug = sm.group(1)
            # First occurrence wins — protects against accidental re-scheduling.
            mapping.setdefault(slug, current_date)
    return mapping


def stamp_publish_date(text: str, publish_date: str) -> tuple[str, bool]:
    """Rewrite the frontmatter `date:` line. Returns (new_text, changed)."""
    new = FRONTMATTER_DATE_RE.sub(f"date: {publish_date}", text, count=1)
    return new, new != text


def prune_body_links(text: str, published: set[str]) -> tuple[str, int]:
    pruned = 0

    def repl(m: re.Match[str]) -> str:
        nonlocal pruned
        label, slug, anchor = m.group(1), m.group(2), m.group(3) or ""
        if slug in published:
            return m.group(0)
        pruned += 1
        return label

    return LINK_RE.sub(repl, text), pruned


def prune_frontmatter_links(text: str, published: set[str]) -> str:
    def repl(m: re.Match[str]) -> str:
        items_raw = m.group(2)
        items = [
            it.strip().strip('"').strip("'")
            for it in items_raw.split(",")
            if it.strip()
        ]
        kept: list[str] = []
        for url in items:
            sm = SLUG_FROM_URL_RE.match(url)
            if sm and sm.group(1) in published:
                kept.append(url)
        rendered = ", ".join(f'"{u}"' for u in kept)
        return m.group(1) + rendered + m.group(3)

    return FRONTMATTER_LINKS_RE.sub(repl, text)


def main() -> int:
    if not CONTENT.exists():
        print(f"resolve_internal_links: {CONTENT} does not exist", file=sys.stderr)
        return 1

    published = published_slugs()
    if not published:
        print("resolve_internal_links: no published articles yet — nothing to do")
        return 0

    publish_dates = queue_publish_dates()
    missing_dates: list[str] = []
    print(f"resolve_internal_links: {len(published)} published slug(s)")

    total_pruned = 0
    total_dated = 0
    for dst in sorted(CONTENT.glob("*.md")):
        slug = dst.stem
        src = DRAFTS / f"{slug}.md"
        if not src.exists():
            print(f"  WARN: no master draft for {slug} — skipping refresh")
            continue

        shutil.copyfile(src, dst)

        text = dst.read_text()
        text = prune_frontmatter_links(text, published)
        text, pruned = prune_body_links(text, published)

        pub_date = publish_dates.get(slug)
        if pub_date:
            text, dated = stamp_publish_date(text, pub_date)
            if dated:
                total_dated += 1
        else:
            missing_dates.append(slug)

        dst.write_text(text)
        total_pruned += pruned

        if pruned:
            print(f"  {slug}: pruned {pruned} unresolved link(s)")

    print(
        f"resolve_internal_links: {total_pruned} link(s) pruned, "
        f"{total_dated} date(s) stamped"
    )
    if missing_dates:
        print(
            "  WARN: no queue date for these published slug(s) — "
            "frontmatter date left as authored:"
        )
        for s in missing_dates:
            print(f"    {s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
