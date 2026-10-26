#!/usr/bin/env python3
"""Build the generated parts of visorvolt.ai.

  python3 _build/build.py                 rebuild pages, home-page blocks, sitemap, robots, then run the checks
  python3 _build/build.py --preview DIR   also write a self-contained preview copy (links end in index.html)

Standard library only. Page bodies live in _build/pages/, data in _build/data/.
Jekyll skips folders that start with "_", so nothing in here is published.
"""
import json, os, re, shutil, sys, html
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "_build")
SITE = "https://visorvolt.ai/"
MAIL = "mailto:umang@visorvolt.ai?subject=Start%20with%2040%20images"
CTA = "Start with 40 images"
LINKEDIN = "https://www.linkedin.com/company/visorvolt/"
ZEBRA_TM = ("ZEBRA and the stylized Zebra head are trademarks of Zebra Technologies Corp., "
            "registered in many jurisdictions worldwide. All other trademarks are the property of their respective owners.")

def load(name):
    with open(os.path.join(B, "data", name)) as f:
        return json.load(f)

HF = load("healthfields.json")
LOG = sorted(load("healthfields_log.json"), key=lambda e: e["date"], reverse=True)
NEWS = sorted(load("news.json"), key=lambda e: e["date"], reverse=True)
LAST = LOG[0]["date"]

def nice(d):
    y, m, dd = map(int, d.split("-"))
    return date(y, m, dd).strftime("%-d %B %Y")

# ---------------------------------------------------------------- links

class Ctx:
    def __init__(self, path, preview):
        self.depth = path.count("/")          # "partners/prolifics/" -> 2, "" -> 0
        self.preview = preview
    def url(self, target):
        """target is site-relative: '', 'partners/', 'case-studies/healthfields/', '#domains', 'assets/x.webp'."""
        if target.startswith(("http", "mailto:")):
            return target
        anchor = ""
        if "#" in target:
            target, anchor = target.split("#", 1)
            anchor = "#" + anchor
        if self.depth == 0 and target == "" and anchor:
            return anchor
        rel = "../" * self.depth + target
        if self.preview and (rel == "" or rel.endswith("/")):
            rel += "index.html"
        return (rel or "./") + anchor

def fill(text, ctx):
    text = re.sub(r"\{\{url:([^}]*)\}\}", lambda m: ctx.url(m.group(1)), text)
    text = text.replace("{{mail}}", MAIL).replace("{{cta}}", CTA)
    return text

# ---------------------------------------------------------------- shared blocks

LOGO_SVG = """<svg viewBox="0 0 500 100" role="img" aria-label="VisorVolt">
      <polygon points="50,10 84,30 84,70 50,90 16,70 16,30" fill="none" stroke="#1E4080" stroke-width="5" stroke-linejoin="round"/>
      <polyline points="16,30 50,10 84,30" fill="none" stroke="#E07B00" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
      <polygon points="50,26 72,38 72,62 50,74 28,62 28,38" fill="none" stroke="#1E4080" stroke-width="2" stroke-linejoin="round"/>
      <line x1="16" y1="50" x2="84" y2="50" stroke="#E07B00" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="16" cy="30" r="3.5" fill="#E07B00"/>
      <circle cx="84" cy="30" r="3.5" fill="#1E4080" stroke="#E07B00" stroke-width="2"/>
      <polygon points="50,28 40,48 49,48 44,64 62,49 52,49 57,28" fill="#E07B00"/>
      <text font-family="Arial,Helvetica,sans-serif" font-size="40" font-weight="800" letter-spacing="-1">
        <tspan x="100" y="58" fill="#FFFFFF">Visor</tspan><tspan fill="#BF7B30">Volt</tspan>
      </text>
      <text x="100" y="78" font-family="Arial,Helvetica,sans-serif" font-size="11" font-weight="400" fill="#6B8BB0" letter-spacing="2.5">DOMAIN-AGNOSTIC VISION</text>
    </svg>"""

def nav(ctx, current=""):
    items = [("Proof", "#domains"), ("How It Works", "#platform"), ("Customers", "case-studies/"),
             ("Partners", "partners/"), ("News", "news/")]
    links = "\n    ".join(
        f'<a href="{ctx.url(t)}"{" aria-current=\"page\"" if current and t == current else ""}>{n}</a>'
        for n, t in items)
    return f"""<nav>
  <a class="nav-logo" href="{ctx.url('')}">
    {LOGO_SVG}
  </a>
  <button class="nav-hamburger" id="nav-hamburger" aria-label="Menu" aria-expanded="false" aria-controls="nav-links">
    <span></span><span></span><span></span>
  </button>
  <div class="nav-links" id="nav-links">
    {links}
    <a href="{MAIL}" class="nav-cta">{CTA}</a>
  </div>
</nav>"""

def footer(ctx, zebra_logo=False):
    groups = [
        ("Product", [("Proof", "#domains"), ("How It Works", "#platform"), ("After It Ships", "#economics"),
                     ("Runs with no internet", "no-internet/")]),
        ("Customers", [("Healthfields", "case-studies/healthfields/")]),
        ("Partners", [("Prolifics", "partners/prolifics/"), ("Zebra Technologies", "partners/zebra/")]),
        ("Company", [("News", "news/"), ("Founder", "#founder"), ("Contact", "#contact"), ("LinkedIn", LINKEDIN)]),
    ]
    cols = "\n".join(
        f'    <div class="footer-group"><h2 class="footer-h">{g}</h2>'
        + "".join(f'<a href="{ctx.url(t)}">{n}</a>' for n, t in links) + "</div>"
        for g, links in groups)
    tm = f'\n  <p class="footer-tm">{ZEBRA_TM}</p>' if zebra_logo else ""
    return f"""<footer class="site-footer">
  <div class="footer-top">
    <a class="footer-logo" href="{ctx.url('')}" aria-label="VisorVolt home">{LOGO_SVG.replace('role="img" aria-label="VisorVolt"', 'aria-hidden="true"')}</a>
    <div class="footer-groups">
{cols}
    </div>
  </div>
  <div class="footer-copy">&copy; 2026 VisorVolt Inc. &nbsp;&middot;&nbsp; Allerton Street, Redwood City, CA 94063 &nbsp;&middot;&nbsp; umang@visorvolt.ai</div>{tm}
</footer>"""

def crumbs_html(ctx, trail):
    parts = [f'<a href="{ctx.url("")}">Home</a>']
    for name, target in trail[:-1]:
        parts.append(f'<a href="{ctx.url(target)}">{name}</a>')
    parts.append(f'<span aria-current="page">{trail[-1][0]}</span>')
    return '<div class="crumbs" role="navigation" aria-label="Breadcrumb">' + '<span class="sep" aria-hidden="true">/</span>'.join(parts) + "</div>"

def crumbs_ld(trail):
    items = [{"@type": "ListItem", "position": 1, "name": "Home", "item": SITE}]
    for i, (name, target) in enumerate(trail, start=2):
        items.append({"@type": "ListItem", "position": i, "name": name, "item": SITE + target})
    return {"@type": "BreadcrumbList", "itemListElement": items}

ORG_REF = {"@type": "Organization", "@id": SITE + "#org", "name": "VisorVolt", "url": SITE}
ORG_FULL = {
    "@type": "Organization", "@id": SITE + "#org", "name": "VisorVolt", "legalName": "VisorVolt Inc.",
    "url": SITE, "logo": SITE + "icon_192.png", "email": "umang@visorvolt.ai",
    "description": "Vision AI that learns a new site from 40 images and keeps improving after it ships. "
                   "Counting and inspection run on the customer's own hardware with no internet.",
    "address": {"@type": "PostalAddress", "streetAddress": "Allerton Street", "addressLocality": "Redwood City",
                "addressRegion": "CA", "postalCode": "94063", "addressCountry": "US"},
    "founder": {"@type": "Person", "name": "Umang Sharma", "jobTitle": "Founder and CEO",
                "sameAs": ["https://www.linkedin.com/in/umang-sharma-datascience"]},
    "sameAs": [LINKEDIN],
}
PROLIFICS = {"@type": "Organization", "name": "Prolifics", "url": "https://prolifics.ai/", "sameAs": ["https://prolifics.ai/"]}
ZEBRA = {"@type": "Organization", "name": "Zebra Technologies", "url": "https://www.zebra.com/"}
HEALTHFIELDS = {"@type": "Organization", "name": "Healthfields", "legalName": "Brahhm Arpan Organic Private Limited",
                "url": "https://healthfields.in/",
                "sameAs": ["https://www.linkedin.com/showcase/health-fields", "https://www.facebook.com/healthfieldsorganic/",
                           "https://www.instagram.com/health.fields/", "https://x.com/Health_Fields"]}

def ld_script(nodes):
    data = {"@context": "https://schema.org", "@graph": nodes}
    return '<script type="application/ld+json">\n' + json.dumps(data, indent=1, ensure_ascii=False) + "\n</script>"

def head(ctx, p):
    url = SITE + p["path"]
    og = SITE + p["og"]
    t = html.escape(p["title"], quote=True)
    d = html.escape(p["desc"], quote=True)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t}</title>
<meta name="description" content="{d}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="{p.get('ogtype', 'website')}">
<meta property="og:site_name" content="VisorVolt">
<meta property="og:url" content="{url}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">
<meta property="og:image" content="{og}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{html.escape(p['og_alt'], quote=True)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{t}">
<meta name="twitter:description" content="{d}">
<meta name="twitter:image" content="{og}">
<link rel="icon" type="image/svg+xml" href="{ctx.url('favicon.svg')}">
<link rel="icon" type="image/png" sizes="32x32" href="{ctx.url('favicon_32.png')}">
<link rel="apple-touch-icon" sizes="192x192" href="{ctx.url('icon_192.png')}">
<script>document.documentElement.classList.add('js')</script>
<link rel="preload" href="{ctx.url('assets/fonts/DMSans-normal-151a53.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="{ctx.url('assets/fonts/PlayfairDisplay-normal-542c91.woff2')}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{ctx.url('css/styles.css')}">
{ld_script(p['ld'])}
</head>
<body class="subpage">
"""

def render(p, preview):
    ctx = Ctx(p["path"], preview)
    body = fill(p["body"], ctx)
    crumbs = crumbs_html(ctx, p["trail"]) if p.get("trail") else ""
    return (head(ctx, p) + nav(ctx, p.get("nav", "")) + f'\n<main class="page" id="main">\n<div class="page-inner">\n{crumbs}\n'
            + body + "\n</div>\n</main>\n" + footer(ctx, p.get("zebra_logo", False))
            + f'\n<script src="{ctx.url("js/main.js")}"></script>\n'
            + '<script data-goatcounter="https://umangai.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>\n</body>\n</html>\n')

def page_body(name):
    with open(os.path.join(B, "pages", name)) as f:
        return f.read()

# ---------------------------------------------------------------- Healthfields blocks

def hf_tiles(which=("cartons", "packing", "trucks")):
    out = []
    for k in which:
        m = HF["metrics"][k]
        out.append(f'<div class="tile"><div class="tile-fig">{m["fig"]}</div>'
                   f'<div class="tile-label">{m["label"]}</div><p class="tile-def">{m["def"]}</p></div>')
    return '<div class="tiles">' + "".join(out) + "</div>"

def hf_log():
    rows = []
    for e in LOG:
        parts = [f'<p><span class="log-k">What we did</span> {e["did"]}</p>']
        if e.get("measured"):
            parts.append(f'<p><span class="log-k">What we measured</span> {e["measured"]}</p>')
        if e.get("next"):
            parts.append(f'<p><span class="log-k">What&rsquo;s next</span> {e["next"]}</p>')
        rows.append(f'<li class="log-entry"><time class="log-date" datetime="{e["date"]}">Week of {nice(e["date"])}</time>'
                    f'<div class="log-body">{"".join(parts)}</div></li>')
    return '<ol class="log" reversed>' + "".join(rows) + "</ol>"

def hf_logo(ctx):
    for ext in ("svg", "png", "webp"):
        rel = f"assets/case-studies/healthfields/healthfields-logo.{ext}"
        if os.path.exists(os.path.join(ROOT, rel)):
            return f'<span class="logo-plate"><img src="{ctx.url(rel)}" alt="Healthfields" height="40"></span>'
    return '<span class="logo-plate logo-plate--text">Healthfields</span>'

def hf_quote():
    q = HF.get("quote")
    if not q or not q.get("approved"):
        return ""
    return (f'<figure class="quote"><blockquote><p>{q["text"]}</p></blockquote>'
            f'<figcaption>{q["name"]}, {q["title"]}, Healthfields</figcaption></figure>')

def home_live(ctx):
    return f"""<section class="live-band" id="live" aria-labelledby="live-h">
  <div class="section-inner">
    <div class="eyebrow"><span class="live-dot" aria-hidden="true"></span>// Live in production</div>
    <h2 id="live-h">At Healthfields, it counts<br><em>on cameras they already had.</em></h2>
    <p class="section-sub">Cartons counted at dispatch and on the packing line, on site with no internet, and written into their warehouse system. Measured on days the models never saw.</p>
    {hf_tiles(("cartons", "packing", "trucks"))}
    <p class="live-foot"><a href="{ctx.url('case-studies/healthfields/')}" class="btn-outline">Read the live case study &rarr;</a>
      <span class="live-upd">Last updated <time datetime="{LAST}">{nice(LAST)}</time></span></p>
  </div>
</section>"""

def home_proof(ctx):
    return f"""<div class="proof-strip" aria-label="Customers and partners">
  <a href="{ctx.url('case-studies/healthfields/')}"><span class="ps-k">Customer</span>Live in production at Healthfields</a>
  <a href="{ctx.url('partners/prolifics/')}"><span class="ps-k">Systems integrator</span>Prolifics, 2,000+ experts worldwide</a>
  <a href="{ctx.url('partners/zebra/')}"><span class="ps-k">ISV partner</span>Zebra Technologies Registered ISV</a>
</div>"""

def news_list(ctx):
    rows = []
    for n in NEWS:
        rows.append(f'<li class="news-item"><time datetime="{n["date"]}">{nice(n["date"])}</time>'
                    f'<h2><a href="{ctx.url(n["path"])}">{n["headline"]}</a></h2><p>{n["summary"]}</p></li>')
    return '<ol class="news-list">' + "".join(rows) + "</ol>"

# ---------------------------------------------------------------- pages

def pages():
    P = []
    def add(**k):
        P.append(k)

    add(path="partners/", nav="partners/", title="Partners: Prolifics and Zebra Technologies | VisorVolt",
        desc="VisorVolt partners: Prolifics, a global systems integrator with 2,000+ experts, and Zebra Technologies, where VisorVolt is a Registered ISV.",
        og="assets/og/partners.png", og_alt="VisorVolt partners: Prolifics and Zebra Technologies",
        trail=[("Partners", "partners/")], zebra_logo=True, body=page_body("partners.html"),
        ld=[ORG_REF, {"@type": "CollectionPage", "@id": SITE + "partners/", "url": SITE + "partners/",
                      "name": "VisorVolt partners", "about": [PROLIFICS, ZEBRA], "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Partners", "partners/")])])

    add(path="partners/prolifics/", nav="partners/",
        title="Prolifics and VisorVolt: Vision AI Systems Integrator Partner",
        desc="Prolifics, a global systems integrator with 2,000+ experts in 10 locations, delivers VisorVolt vision AI to clients in every industry. 40 images per site.",
        og="assets/og/prolifics.png", og_alt="Prolifics and VisorVolt partnership",
        trail=[("Partners", "partners/"), ("Prolifics", "partners/prolifics/")], body=page_body("prolifics.html"),
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "partners/prolifics/", "url": SITE + "partners/prolifics/",
                      "name": "Prolifics and VisorVolt", "about": PROLIFICS, "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Partners", "partners/"), ("Prolifics", "partners/prolifics/")])])

    add(path="partners/zebra/", nav="partners/",
        title="Zebra Technologies Registered ISV: Vision AI | VisorVolt",
        desc="VisorVolt is a Registered ISV in Zebra Technologies' PartnerConnect program in North America and Asia-Pacific. Vision AI for warehouses and plants.",
        og="assets/og/zebra.png", og_alt="VisorVolt, Zebra Technologies Registered ISV",
        trail=[("Partners", "partners/"), ("Zebra Technologies", "partners/zebra/")], zebra_logo=True,
        body=page_body("zebra.html"),
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "partners/zebra/", "url": SITE + "partners/zebra/",
                      "name": "VisorVolt, Zebra Technologies Registered ISV", "about": ZEBRA, "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Partners", "partners/"), ("Zebra Technologies", "partners/zebra/")])])

    add(path="case-studies/", nav="case-studies/", title="Customer case studies | VisorVolt",
        desc="How VisorVolt runs in production: counting and inspection on customers' own cameras and hardware, with no internet. Live case study: Healthfields.",
        og="assets/og/healthfields.jpg", og_alt="VisorVolt customer case studies",
        trail=[("Customers", "case-studies/")], body=page_body("case-studies.html"),
        ld=[ORG_REF, {"@type": "CollectionPage", "@id": SITE + "case-studies/", "url": SITE + "case-studies/",
                      "name": "VisorVolt case studies", "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Customers", "case-studies/")])])

    hf_path = "case-studies/healthfields/"
    add(path=hf_path, nav="case-studies/", ogtype="article",
        title="Healthfields Case Study: Warehouse Counting with Computer Vision | VisorVolt",
        desc="Live case study: Healthfields counts cartons on its existing cameras with VisorVolt, on site with no internet. Cartons within 1% on a held-out day.",
        og="assets/og/healthfields.jpg", og_alt="Healthfields case study: cartons counted on existing cameras",
        trail=[("Customers", "case-studies/"), ("Healthfields", hf_path)], body=page_body("healthfields.html"),
        ld=[ORG_REF, {"@type": "Article", "@id": SITE + hf_path + "#article", "url": SITE + hf_path,
                      "mainEntityOfPage": SITE + hf_path,
                      "headline": "Healthfields counts cartons on the cameras it already had",
                      "image": [SITE + "assets/og/healthfields.jpg"], "datePublished": HF["published"],
                      "dateModified": LAST, "author": {"@id": SITE + "#org"}, "publisher": {"@id": SITE + "#org"},
                      "about": HEALTHFIELDS},
            crumbs_ld([("Customers", "case-studies/"), ("Healthfields", hf_path)])])

    add(path="no-internet/", nav="", title="Vision AI That Runs With No Internet: On-Premises and Air-Gapped | VisorVolt",
        desc="Computer vision that counts and inspects on your own hardware with no internet. Updates arrive as a signed file, and a person approves every change.",
        og="assets/og/no-internet.png", og_alt="Vision AI that runs with no internet",
        trail=[("Runs with no internet", "no-internet/")], body=page_body("no-internet.html"),
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "no-internet/", "url": SITE + "no-internet/",
                      "name": "Vision AI that runs with no internet", "publisher": {"@id": SITE + "#org"}},
            faq_ld(), crumbs_ld([("Runs with no internet", "no-internet/")])])

    add(path="news/", nav="news/", title="News | VisorVolt",
        desc="VisorVolt news: the Prolifics systems integrator partnership, Zebra Technologies Registered ISV, and Healthfields live in production.",
        og="assets/og/news.png", og_alt="VisorVolt news", trail=[("News", "news/")], body=page_body("news.html"),
        ld=[ORG_REF, {"@type": "CollectionPage", "@id": SITE + "news/", "url": SITE + "news/", "name": "VisorVolt news",
                      "publisher": {"@id": SITE + "#org"},
                      "hasPart": [{"@type": "NewsArticle", "headline": n["headline"], "url": SITE + n["path"],
                                   "datePublished": n["date"]} for n in NEWS]},
            crumbs_ld([("News", "news/")])])

    for n in NEWS:
        about = {"prolifics": PROLIFICS, "zebra": ZEBRA, "healthfields": HEALTHFIELDS}[n["about"]]
        add(path=n["path"], nav="news/", ogtype="article", title=n["title"], desc=n["desc"], og=n["og"],
            og_alt=n["headline"], trail=[("News", "news/"), (n["crumb"], n["path"])],
            zebra_logo=False, body=page_body(n["body"]),
            ld=[ORG_REF, {"@type": "NewsArticle", "@id": SITE + n["path"] + "#article", "url": SITE + n["path"],
                          "mainEntityOfPage": SITE + n["path"], "headline": n["headline"],
                          "image": [SITE + n["og"]], "datePublished": n["date"], "dateModified": n.get("modified", n["date"]),
                          "author": {"@id": SITE + "#org"}, "publisher": {"@id": SITE + "#org"}, "about": about},
                crumbs_ld([("News", "news/"), (n["crumb"], n["path"])])])
    return P

FAQ = [
    ("Does counting need an internet connection?",
     "No. Detection, counting, tracking, the review queue and the nightly reports all run on a computer on your site. If the connection drops, nothing stops."),
    ("How does the model improve without the internet?",
     "Retraining happens in our cloud, by agreement, or in your own cloud account if your images cannot leave it. The new model comes back as a signed file. Your computer checks the signature before installing it, and a person approves every promotion."),
    ("What leaves the site?",
     "Only what you agree to, such as the frames we pick for labelling. Live video and counts stay on your network."),
    ("Can it run on an air-gapped network?",
     "Yes. Nothing on site needs to reach the internet. Updates cross the gap as a signed file, in whatever way your security team approves."),
    ("Does it work with the cameras we already have?",
     "Usually, yes. At Healthfields it runs on the existing CCTV cameras. Tell us the camera and how far it sits from the objects, and we will tell you what to expect before you buy."),
    ("What hardware does it need?",
     "One GPU computer on site. At Healthfields, one such computer runs five services and four nightly reports, and processes recorded footage about five times faster than real time."),
]

def faq_ld():
    return {"@type": "FAQPage", "@id": SITE + "no-internet/#faq",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in FAQ]}

def faq_html():
    return '<div class="faq">' + "".join(
        f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in FAQ) + "</div>"

# ---------------------------------------------------------------- home page blocks

def update_home(preview):
    ctx = Ctx("", preview)
    with open(os.path.join(ROOT, "index.html")) as f:
        s = f.read()
    blocks = {
        "NAV": nav(ctx),
        "PROOF": home_proof(ctx),
        "LIVE": home_live(ctx),
        "FOOTER": footer(ctx),
        "JSONLD": ld_script([ORG_FULL, {"@type": "WebSite", "@id": SITE + "#site", "url": SITE, "name": "VisorVolt",
                                        "publisher": {"@id": SITE + "#org"}}]),
    }
    for k, v in blocks.items():
        pat = re.compile(rf"<!-- BUILD:{k} -->.*?<!-- /BUILD:{k} -->", re.S)
        assert pat.search(s), f"index.html is missing the BUILD:{k} markers"
        s = pat.sub(lambda m: f"<!-- BUILD:{k} -->\n{v}\n<!-- /BUILD:{k} -->", s)
    return s

# ---------------------------------------------------------------- output

def expand(body, ctx):
    body = body.replace("{{hf_tiles}}", hf_tiles()).replace("{{hf_log}}", hf_log())
    body = body.replace("{{hf_logo}}", hf_logo(ctx)).replace("{{hf_quote}}", hf_quote())
    body = body.replace("{{hf_last}}", f'<time datetime="{LAST}">{nice(LAST)}</time>')
    body = body.replace("{{hf_since}}", HF["live_since"]).replace("{{faq}}", faq_html())
    body = body.replace("{{news_list}}", news_list(ctx)).replace("{{zebra_tm}}", ZEBRA_TM)
    for n in NEWS:
        body = body.replace("{{date:%s}}" % n["about"], nice(n["date"])).replace("{{iso:%s}}" % n["about"], n["date"])
    return body

def build(preview_dir=None):
    out = {}
    for p in pages():
        for preview in ([False, True] if preview_dir else [False]):
            ctx = Ctx(p["path"], preview)
            q = dict(p, body=expand(p["body"], ctx))
            out[(p["path"], preview)] = render(q, preview)
    for (path, preview), text in out.items():
        if preview:
            continue
        dst = os.path.join(ROOT, path, "index.html")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w") as f:
            f.write(text)
    home = update_home(False)
    with open(os.path.join(ROOT, "index.html"), "w") as f:
        f.write(home)
    write_sitemap()
    write_robots()
    write_404()
    if preview_dir:
        write_preview(preview_dir, out)
    print(f"built {len(pages())} pages; case study last updated {LAST}")

def write_sitemap():
    home_mod = max([LAST] + [n["date"] for n in NEWS])
    urls = [("", home_mod)]
    for p in pages():
        mod = LAST if p["path"].startswith("case-studies") else HF["published"]
        for n in NEWS:
            if n["path"] == p["path"]:
                mod = n.get("modified", n["date"])
        if p["path"] == "news/":
            mod = NEWS[0]["date"]
        urls.append((p["path"], mod))
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    xml += [f"  <url><loc>{SITE}{u}</loc><lastmod>{m}</lastmod></url>" for u, m in urls]
    xml.append("</urlset>")
    with open(os.path.join(ROOT, "sitemap.xml"), "w") as f:
        f.write("\n".join(xml) + "\n")

def write_robots():
    txt = """# Search engines and AI answer engines may read the site.
User-agent: *
Allow: /
Disallow: /demo.html

# Crawlers that collect training data for AI models may not.
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: Google-Extended
Disallow: /

User-agent: Applebot-Extended
Disallow: /

User-agent: Bytespider
Disallow: /

Sitemap: https://visorvolt.ai/sitemap.xml
"""
    with open(os.path.join(ROOT, "robots.txt"), "w") as f:
        f.write(txt)

def write_404():
    p = dict(path="404/", title="Page not found | VisorVolt", desc="This page does not exist. Start from the VisorVolt home page.",
             og="assets/og-image.png", og_alt="VisorVolt", ld=[ORG_REF], trail=None,
             body='<h1>That page is not here.</h1>\n<p class="page-lede">It may have moved. These are the pages people look for most.</p>\n'
                  '<ul class="link-list"><li><a href="/">Home</a></li><li><a href="/case-studies/healthfields/">Healthfields case study</a></li>'
                  '<li><a href="/partners/">Partners</a></li><li><a href="/news/">News</a></li></ul>')
    text = render(p, False)
    # 404.html is served from whatever URL was missed, so its links must be root-absolute.
    text = re.sub(r'(href|src)="(\.\./)+', r'\1="/', text)
    text = text.replace('<link rel="canonical" href="https://visorvolt.ai/404/">', '<meta name="robots" content="noindex">')
    with open(os.path.join(ROOT, "404.html"), "w") as f:
        f.write(text)

def write_preview(dst, out):
    """A copy that works from a file listing: every folder link ends in index.html."""
    if os.path.exists(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for (path, preview), text in out.items():
        if not preview:
            continue
        p = os.path.join(dst, path, "index.html")
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(text)
    home = update_home(True)
    # the home page's own links to its sub-pages, outside the BUILD blocks
    home = re.sub(r'href="((?:case-studies|partners|news|no-internet)/(?:[a-z0-9-]+/)*)"', r'href="\1index.html"', home)
    with open(os.path.join(dst, "index.html"), "w") as f:
        f.write(home)
    for d in ("css", "js"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(dst, d))
    for f in ("favicon.svg", "favicon_32.png", "icon_192.png", "favicon.ico"):
        shutil.copy(os.path.join(ROOT, f), dst)
    refs = set()
    for root, _, files in os.walk(dst):
        for fn in files:
            if fn.endswith((".html", ".css")):
                s = open(os.path.join(root, fn)).read()
                for m in re.finditer(r'(?:src|href|data-src(?:-lg)?)="([^"#?]+)"|url\([\'"]?([^\'")]+)', s):
                    u = m.group(1) or m.group(2)
                    if "assets/" in u and not u.startswith("http"):
                        refs.add(os.path.normpath(os.path.join(os.path.relpath(root, dst), u)))
                for m in re.finditer(r'srcset="([^"]+)"', s):
                    for part in m.group(1).split(","):
                        u = part.strip().split(" ")[0]
                        refs.add(os.path.normpath(os.path.join(os.path.relpath(root, dst), u)))
    for r in sorted(refs):
        src = os.path.join(ROOT, r)
        if os.path.isfile(src):
            os.makedirs(os.path.dirname(os.path.join(dst, r)), exist_ok=True)
            shutil.copy(src, os.path.join(dst, r))

if __name__ == "__main__":
    prev = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
    build(prev)
    import subprocess
    sys.exit(subprocess.call([sys.executable, os.path.join(B, "check.py")]))
