# luya-blog

SEO blog engine for **luyaxyz.com/blog/** — an Astro static site published one or two articles per day via GitHub Actions, served through Cloudflare.

Modeled on the cbtcbook.com blog playbook: static site + a queue of good articles + a daily auto-publisher = a compounding SEO asset.

## Layout
```
blog-drafts/        all article markdown (the backlog, fully written)
publish-queue.yml   date -> slug schedule (drip 1-2/day)
blog-tools/         Python publisher (ci_publish.py + helpers)
site-src/           the Astro project (site=luyaxyz.com, base=/blog)
site/               deployed output root (site/blog/ = what's served)
.github/workflows/  daily-publish.yml (cron)
```

## How publishing works
1. `ci_publish.py` reads `publish-queue.yml`, copies every due (date ≤ today, incl. back-fill) draft into `site-src/src/content/blog/`.
2. `resolve_internal_links.py` stamps the real publish date from the queue and strips links to not-yet-published articles.
3. Astro builds → `site-src/dist/` → rsync into `site/blog/`.
4. The workflow commits publish state and deploys `site/` to Cloudflare Pages.

## One-time setup
1. **Cloudflare Pages**: create a project named `luya-blog`.
2. **Repo secrets**: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, optional `GMAIL_APP_PASSWORD`.
3. **Routing**: a Cloudflare Worker (or Pages custom-domain + route) maps `luyaxyz.com/blog/*` to this site so the blog lives under the main domain (best for SEO).

## Local
```
cd site-src && npm install && npm run build   # outputs dist/
npm run preview                               # serve locally
# test a publish date:
FORCE_DATE=2026-06-24 python3 blog-tools/ci_publish.py
```

Images: hero + inline scenes were generated with gpt-image-2; data charts are hand-built SVG (never AI — accuracy). All live in `site-src/public/img/`.
