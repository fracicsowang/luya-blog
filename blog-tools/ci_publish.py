#!/usr/bin/env python3
"""
ci_publish.py — cloud (GitHub Actions) counterpart of daily_publish.sh.

Runs in a GitHub Actions Linux runner instead of on the author's Mac, so the
blog publishes every day regardless of whether any laptop is awake. It does the
same content work as daily_publish.sh but deliberately does NOT touch git or
fire macOS notifications — the workflow (.github/workflows/daily-publish.yml)
handles commit/push and Pages deploy.

What it does:
  1. Read publish-queue.yml and select every slug whose date <= today
     (America/New_York), i.e. today PLUS any earlier day that was never
     published — natural catch-up, no day can be silently dropped.
  2. Copy each due draft from blog-drafts/ into the Astro content collection
     (site-src/src/content/blog/) if it isn't already there. Idempotent.
  3. resolve_internal_links.py  — refresh published copies, prune links to
     not-yet-published slugs.
  5. `npm run build` in site-src/  → Astro emits to site-src/dist/.
  6. rsync dist/ → site/blog/      (only /site/blog/, never the 8 static pages).
  7. gen_blog_sitemap.py        — refresh /site/blog/sitemap.xml.

All helper scripts resolve their own root via Path(__file__).parent.parent,
so they need no changes to run here.

Env:
  FORCE_DATE=YYYY-MM-DD   process as if today were this date (testing / backfill)
  DRY_PUBLISH=1           build only; skip nothing here (git is the workflow's job)

Exit codes: 0 = success (whether or not new articles were copied), 1 = build
or a hard error. The workflow inspects the printed summary + the git diff to
decide whether there is anything to commit.
"""

import os
import re
import sys
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

try:
    from zoneinfo import ZoneInfo  # py3.9+
    _NY = ZoneInfo("America/New_York")
except Exception:                  # pragma: no cover
    _NY = None

ROOT     = Path(__file__).resolve().parent.parent
DRAFTS   = ROOT / "blog-drafts"
CONTENT  = ROOT / "site-src" / "src" / "content" / "blog"
SITE     = ROOT / "site"
SITE_SRC = ROOT / "site-src"
DIST     = SITE_SRC / "dist"
QUEUE    = ROOT / "publish-queue.yml"
TOOLS    = ROOT / "blog-tools"

DATE_RE  = re.compile(r'^"(\d{4}-\d{2}-\d{2})":')
SLUG_RE  = re.compile(r'^\s*-\s+([a-z0-9-]+)\s*$')


def today_str() -> str:
    forced = os.environ.get("FORCE_DATE")
    if forced:
        return forced.strip()
    now = datetime.now(_NY) if _NY else datetime.now()
    return now.strftime("%Y-%m-%d")


def due_slugs(today: str) -> list[str]:
    """Every slug whose queue date <= today (ISO dates sort chronologically)."""
    out, in_block = [], False
    for line in QUEUE.read_text().splitlines():
        m = DATE_RE.match(line)
        if m:
            in_block = (m.group(1) <= today)
            continue
        if in_block:
            sm = SLUG_RE.match(line)
            if sm:
                out.append(sm.group(1))
    return out


def run(cmd, cwd=None, label=None):
    print(f"::group::{label or ' '.join(map(str, cmd))}", flush=True)
    res = subprocess.run(cmd, cwd=cwd)
    print("::endgroup::", flush=True)
    if res.returncode != 0:
        print(f"ERROR: command failed ({res.returncode}): {' '.join(map(str, cmd))}",
              file=sys.stderr)
        sys.exit(1)


def run_soft(cmd, cwd=None, label=None):
    """Like run() but non-fatal — matches the `|| true` calls in daily_publish.sh."""
    print(f"::group::{label or ' '.join(map(str, cmd))}", flush=True)
    res = subprocess.run(cmd, cwd=cwd)
    print("::endgroup::", flush=True)
    if res.returncode != 0:
        print(f"WARN: non-zero ({res.returncode}) from {' '.join(map(str, cmd))} — continuing")


def main():
    for p in (DRAFTS, SITE_SRC, QUEUE):
        if not p.exists():
            print(f"FATAL: expected path not found: {p}", file=sys.stderr)
            sys.exit(1)

    today = today_str()
    print(f"=== ci_publish: target date {today} ===")

    CONTENT.mkdir(parents=True, exist_ok=True)
    due = due_slugs(today)
    print(f"due (incl. back-fill): {len(due)} slug(s) up to {today}")

    copied, missing = [], []
    for slug in due:
        src = DRAFTS / f"{slug}.md"
        dst = CONTENT / f"{slug}.md"
        if not src.exists():
            missing.append(slug)
            print(f"  MISSING in blog-drafts/: {slug}")
            continue
        if dst.exists():
            continue  # already published
        shutil.copyfile(src, dst)
        copied.append(slug)
        print(f"  copied (new): {slug}")

    if copied:
        print(f"newly publishing {len(copied)}: {', '.join(copied)}")
    else:
        print("no new articles due today — rebuilding to keep site/blog in sync")

    py = sys.executable
    run_soft([py, str(TOOLS / "resolve_internal_links.py")], label="resolve internal links")

    run(["npm", "run", "build"], cwd=str(SITE_SRC), label="astro build")
    if not DIST.exists():
        print(f"FATAL: build produced no {DIST}", file=sys.stderr)
        sys.exit(1)

    (SITE / "blog").mkdir(parents=True, exist_ok=True)
    run(["rsync", "-a", "--delete",
         "--exclude=figures/", "--exclude=slides/",
         f"{DIST}/", f"{SITE / 'blog'}/"], label="rsync dist -> site/blog")

    run_soft([py, str(TOOLS / "gen_blog_sitemap.py")], label="regen blog sitemap")

    # Machine-readable summary for the workflow (GITHUB_OUTPUT) + humans.
    gh_out = os.environ.get("GITHUB_OUTPUT")
    if gh_out:
        with open(gh_out, "a") as fh:
            fh.write(f"copied_count={len(copied)}\n")
            fh.write(f"copied_slugs={','.join(copied)}\n")
            fh.write(f"date={today}\n")
    print("=" * 60)
    print(f"date={today}  newly_published={len(copied)}  missing_drafts={len(missing)}")
    if missing:
        print("WARNING — queued but no draft found: " + ", ".join(missing))


if __name__ == "__main__":
    main()
