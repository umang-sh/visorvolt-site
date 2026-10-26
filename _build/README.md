# Site build

Jekyll skips folders that start with `_`, so nothing in here is published.

```
python3 _build/build.py                    # rebuild generated pages, sitemap.xml, robots.txt, 404.html, then run the checks
python3 _build/build.py --preview DIR      # also write a preview copy whose folder links end in index.html
python3 _build/check.py                    # checks only
```

- **New progress-log entry for the Healthfields case study:** add one line to the top of `data/healthfields_log.json`, then run the build. "Last updated" (on the page and the home band), the article's `dateModified` and the sitemap all follow the newest entry.
- **Healthfields quote:** fill `quote` in `data/healthfields.json` and set `"approved": true` only after the person quoted has approved the exact words.
- **Healthfields logo:** save it as `assets/case-studies/healthfields/healthfields-logo.svg` (or `.png`). The build uses it in place of the text name.
- **News:** posts are listed in `data/news.json`; bodies are in `pages/news-*.html`.
- **Home page:** `index.html` is hand-written except the blocks between `<!-- BUILD:X -->` markers (nav, proof strip, live band, footer, JSON-LD), which the build rewrites.
- **Checks** (`check.py`) fail the build on: em dashes, banned label claims, 86% or 87%, withdrawn or superseded numbers, ROI, naming what the agent is built on, model-agnostic wording, internal model names, camera channel numbers, Zebra before Prolifics in one block, a Zebra logo without Zebra's trademark sentence, missing home-page guardrails, 89% beside any dataset count but 39, broken links, missing alt text, JSON-LD that does not parse, duplicate titles or descriptions, and pages without exactly one h1.

## Zebra logo rules (Zebra brand guide)

Black or white logo only, clear space on every side, never in a lockup with another logo without Zebra brand-team approval, and the trademark sentence on any page that shows it (the build adds it to the footer of those pages).

## Google Search Console (Umang, after deploy)

1. Go to search.google.com/search-console and add a **Domain** property for `visorvolt.ai`.
2. Verify it with the DNS TXT record Google shows, added at the domain registrar. It can take a few minutes to an hour to verify.
3. **Sitemaps:** submit `https://visorvolt.ai/sitemap.xml`.
4. **URL Inspection:** paste each new URL and click **Request indexing**:
   - https://visorvolt.ai/case-studies/healthfields/
   - https://visorvolt.ai/partners/prolifics/
   - https://visorvolt.ai/partners/zebra/
   - https://visorvolt.ai/no-internet/
   - https://visorvolt.ai/news/ and the three posts under it
5. After about a week, check **Pages** (indexed or not, and why) and **Enhancements** (breadcrumbs, FAQ, articles detected).
6. Optional: run each URL through search.google.com/test/rich-results to confirm the structured data is read without errors.
