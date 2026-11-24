#!/usr/bin/env python3
"""Build visorvolt.ai (redesign v3).

  python3 _build/build.py                 rebuild every page, sitemap, robots, 404, then run the checks
  python3 _build/build.py --preview DIR   also write a self-contained preview copy (folder links end in index.html)

Standard library only. Page bodies live in _build/pages/ (macros: {{url:..}}, {{clip:..}}, {{illus:..}}, {{still:..}}, {{count:..}}),
reusable components in components.py, data in _build/data/. Jekyll skips folders that start with "_".
"""
import json, os, re, shutil, sys, html
from datetime import date
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import components as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
B = os.path.join(ROOT, "_build")
SITE = "https://visorvolt.ai/"
MAIL = "mailto:umang@visorvolt.ai?subject=Show%20us%20a%20checkpoint"
CTA = "Show us a checkpoint"
VIDEO_CTA = "Watch the 2-minute video"
LINKEDIN = "https://www.linkedin.com/company/visorvolt/"
ZEBRA_TM = ("ZEBRA and the stylized Zebra head are trademarks of Zebra Technologies Corp., "
            "registered in many jurisdictions worldwide. All other trademarks are the property of their respective owners.")
FOOT_NOTE = "Healthfields results are from an ongoing deployment and are development-stage evidence."
VIDEO_MP4 = "assets/v3/video/visorvolt-checkpoints-site.mp4"
VIDEO_POSTER = "assets/v3/video/visorvolt-checkpoints-site-poster.webp"
TRANSCRIPT = "transcript/"

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
        self.depth = path.count("/")
        self.preview = preview
    def url(self, target):
        """target is site-relative: '', 'partners/', '#video', 'assets/x.webp'."""
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
    </svg>"""



NAV = [
    ("Checkpoints", "checkpoints/", []),
    ("How it works", "how-it-works/", []),
    ("Proof", "proof/", [("Healthfields case study", "case-studies/healthfields/"), ("Research", "proof/#research"), ("News", "news/")]),
    ("Partners", "partners/", [("Prolifics", "partners/prolifics/"), ("Zebra", "partners/zebra/")]),
    ("Company", "company/", []),
]

def nav(ctx, current=""):
    items = []
    for name, target, sub in NAV:
        cur = ' aria-current="page"' if current == target else ""
        if sub:
            subs = "".join(f'<a href="{ctx.url(t)}">{n}</a>' for n, t in sub)
            items.append(f'<div class="nav-item has-sub"><a href="{ctx.url(target)}"{cur}>{name}</a><div class="nav-sub">{subs}</div></div>')
        else:
            items.append(f'<div class="nav-item"><a href="{ctx.url(target)}"{cur}>{name}</a></div>')
    return f"""<nav class="site-nav" aria-label="Main">
  <a class="nav-logo" href="{ctx.url('')}" aria-label="VisorVolt home">
    {LOGO_SVG}
  </a>
  <button class="nav-hamburger" id="nav-hamburger" aria-label="Menu" aria-expanded="false" aria-controls="nav-links" type="button">
    <span></span><span></span><span></span>
  </button>
  <div class="nav-links" id="nav-links">
    {"".join(items)}
    <a href="{MAIL}" class="nav-cta">{CTA}</a>
  </div>
</nav>"""

def footer(ctx, zebra_logo=False):
    groups = [
        ("Product", [("Checkpoints", "checkpoints/"), ("How it works", "how-it-works/"), ("Runs with no internet", "no-internet/"), ("Proof", "proof/")]),
        ("Customers and news", [("Healthfields case study", "case-studies/healthfields/"), ("All case studies", "case-studies/"), ("News", "news/")]),
        ("Partners", [("Prolifics", "partners/prolifics/"), ("Zebra Technologies Registered ISV", "partners/zebra/")]),
        ("Company", [("About VisorVolt and investors", "company/#investors"), ("LinkedIn", LINKEDIN), ("umang@visorvolt.ai", "mailto:umang@visorvolt.ai")]),
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
  <div class="footer-copy">&copy; 2026 VisorVolt Inc. &nbsp;&middot;&nbsp; Allerton Street, Redwood City, CA 94063 &nbsp;&middot;&nbsp; umang@visorvolt.ai</div>
  <p class="footer-note">{FOOT_NOTE}</p>{tm}
</footer>"""

def video_dialog(ctx):
    return f"""<dialog class="vdlg" id="vdlg" aria-label="VisorVolt in two minutes">
  <video controls playsinline preload="none" data-src="{ctx.url(VIDEO_MP4)}" data-poster="{ctx.url(VIDEO_POSTER)}" aria-label="VisorVolt in two minutes. Captions are burned into the picture."></video>
  <div class="vdlg-bar"><a class="text-link" href="{ctx.url(TRANSCRIPT)}">Read the transcript</a><button type="button" class="vdlg-close" data-close>Close</button></div>
</dialog>"""

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
    "description": "VisorVolt turns any camera checkpoint, in any industry, into a count or a check that a person audits. "
                   "It is built for each site, runs on the site with no internet, and improves every month.",
    "address": {"@type": "PostalAddress", "streetAddress": "Allerton Street", "addressLocality": "Redwood City",
                "addressRegion": "CA", "postalCode": "94063", "addressCountry": "US"},
    "founder": {"@type": "Person", "name": "Umang Sharma", "jobTitle": "Founder and CEO",
                "sameAs": ["https://www.linkedin.com/in/umang-sharma-datascience"]},
    "sameAs": [LINKEDIN],
}
PROLIFICS = {"@type": "Organization", "name": "Prolifics", "url": "https://prolifics.ai/", "sameAs": ["https://prolifics.ai/"]}
ZEBRA = {"@type": "Organization", "name": "Zebra Technologies", "url": "https://www.zebra.com/"}
HEALTHFIELDS = {"@type": "Organization", "name": "Healthfields", "url": "https://healthfields.in/",
                "sameAs": ["https://www.linkedin.com/showcase/health-fields", "https://www.facebook.com/healthfieldsorganic/",
                           "https://www.instagram.com/health.fields/", "https://x.com/Health_Fields"]}
VIDEO_LD = {"@type": "VideoObject", "name": "VisorVolt: any checkpoint, any production line",
            "description": "Real Healthfields footage of a vehicle gate, a dock, people crossing a line, a packing line and dispatch, counted and audited, with every count kept with its clip. Captions are burned in.",
            "thumbnailUrl": SITE + VIDEO_POSTER, "uploadDate": "2026-11-24", "duration": "PT2M13S",
            "contentUrl": SITE + VIDEO_MP4, "publisher": {"@id": SITE + "#org"}}

def ld_script(nodes):
    data = {"@context": "https://schema.org", "@graph": nodes}
    return '<script type="application/ld+json">\n' + json.dumps(data, indent=1, ensure_ascii=False) + "\n</script>"

def head(ctx, p):
    url = SITE + p["path"]
    og = SITE + p["og"]
    t = html.escape(p["title"], quote=True)
    d = html.escape(p["desc"], quote=True)
    pre = p.get("preload", "")
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{t}</title>
<meta name="description" content="{d}">
<meta name="theme-color" content="#0E1520">
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
{pre}<link rel="stylesheet" href="{ctx.url('css/site.css')}">
{ld_script(p['ld'])}
</head>
"""

def render(p, preview):
    ctx = Ctx(p["path"], preview)
    C.Counter.n = 0
    body = expand(p["body"], ctx)
    home = p.get("layout") == "home"
    if home:
        main = f'<main id="main">\n{body}\n</main>'
    else:
        crumbs = crumbs_html(ctx, p["trail"]) if p.get("trail") else ""
        main = f'<main id="main" class="page">\n<div class="wrap">\n{crumbs}\n{body}\n</div>\n</main>'
    return (head(ctx, p) + f'<body class="{"home" if home else "subpage"}">\n<a class="skip" href="#main">Skip to content</a>\n'
            + nav(ctx, p.get("nav", "")) + "\n" + main + "\n" + footer(ctx, p.get("zebra_logo", False)) + "\n"
            + video_dialog(ctx)
            + f'\n<script src="{ctx.url("js/site.js")}" defer></script>\n'
            + '<script data-goatcounter="https://umangai.goatcounter.com/count" async src="https://gc.zgo.at/count.js"></script>\n</body>\n</html>\n')

def page_body(name):
    with open(os.path.join(B, "pages", name)) as f:
        return f.read()

# ---------------------------------------------------------------- Healthfields blocks

def hf_tiles(which=("packing", "cartons", "trucks")):
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
        rows.append(f'<li class="log-entry"><time class="log-date" datetime="{e["date"]}">{nice(e["date"])}</time>'
                    f'<div class="log-body">{"".join(parts)}</div></li>')
    return '<ol class="log" reversed>' + "".join(rows) + "</ol>"

def hf_logo(ctx, big=False):
    base = "assets/case-studies/healthfields/healthfields-logo"
    h = 104 if big else 68
    w = round(h * 1218 / 703)
    return (f'<span class="logo-plate logo-plate--hf{" logo-plate--hf-lg" if big else ""}"><picture>'
            f'<source type="image/webp" srcset="{ctx.url(base + "-240.webp")} 240w, {ctx.url(base + "-480.webp")} 480w" sizes="{w}px">'
            f'<img src="{ctx.url(base + "-480.jpg")}" srcset="{ctx.url(base + "-240.jpg")} 240w, {ctx.url(base + "-480.jpg")} 480w" '
            f'sizes="{w}px" width="{w}" height="{h}" alt="Healthfields"></picture></span>')

def hf_quote():
    q = HF.get("quote")
    if not q or not q.get("approved"):
        return ""
    return (f'<figure class="quote"><blockquote><p>{q["text"]}</p></blockquote>'
            f'<figcaption>{q["name"]}, {q["title"]}, Healthfields</figcaption></figure>')

KIND = {"prolifics": "Partnership", "zebra": "Partnership", "healthfields": "Customer"}

def news_list(ctx):
    rows = []
    for n in NEWS:
        rows.append(f'<li class="news-item"><time datetime="{n["date"]}">{nice(n["date"])}</time>'
                    f'<h2><a href="{ctx.url(n["path"])}">{n["headline"]}</a></h2><p>{n["summary"]}</p></li>')
    return '<ol class="news-list">' + "".join(rows) + "</ol>"

# ---------------------------------------------------------------- macros

def macro(m, ctx):
    kind, arg = m.group(1), m.group(2)
    parts = arg.split("|")
    if kind == "url":
        return ctx.url(arg)
    if kind == "clip":
        return C.clip(ctx, parts[0], alt=parts[1] if len(parts) > 1 and parts[1] else None, ar=parts[2] if len(parts) > 2 else None)
    if kind == "illus":
        return C.illus(ctx, parts[0], parts[1] if len(parts) > 1 else None)
    if kind == "still":
        return C.still(ctx, parts[0], parts[1], ar=parts[2] if len(parts) > 2 else "16/9")
    if kind == "count":
        return COUNTS[parts[0]](ctx)
    raise KeyError(kind)

def expand(body, ctx):
    if callable(body):
        body = body(ctx)
    body = body.replace("{{hf_tiles}}", hf_tiles()).replace("{{hf_log}}", hf_log())
    body = body.replace("{{hf_logo}}", hf_logo(ctx, big=True)).replace("{{hf_logo_sm}}", hf_logo(ctx)).replace("{{hf_quote}}", hf_quote())
    body = body.replace("{{hf_last}}", f'<time datetime="{LAST}">{nice(LAST)}</time>')
    body = body.replace("{{hf_since}}", HF["live_since"]).replace("{{faq}}", faq_html(FAQ_NOINT)).replace("{{faq_how}}", faq_html(FAQ_HOW))
    body = body.replace("{{news_list}}", news_list(ctx)).replace("{{zebra_tm}}", ZEBRA_TM)
    body = body.replace("{{mail}}", MAIL).replace("{{cta}}", CTA).replace("{{video_cta}}", VIDEO_CTA)
    body = body.replace("{{cta_btn}}", f'<a class="btn btn-primary" href="{MAIL}">{CTA}</a>')
    body = body.replace("{{vid_btn}}", f'<a class="btn btn-outline" href="{ctx.url("#video")}" data-open-video>{VIDEO_CTA}</a>')
    body = body.replace("{{cta_band}}", cta_band(ctx))
    body = body.replace("{{prolifics_plate}}", f'<span class="logo-plate"><img src="{ctx.url("assets/partners/prolifics-wordmark.png")}" alt="Prolifics" width="214" height="32"></span>')
    body = body.replace("{{zebra_mark}}", f'<span class="zebra-mark"><img src="{ctx.url("assets/partners/zebra-logo-white.svg")}" alt="Zebra Technologies" width="150" height="46"></span>')
    body = body.replace("{{zebra_mark_lg}}", f'<span class="zebra-mark zebra-mark--lg"><img src="{ctx.url("assets/partners/zebra-logo-white.svg")}" alt="Zebra Technologies" width="150" height="46"></span>')
    for n in NEWS:
        body = body.replace("{{date:%s}}" % n["about"], nice(n["date"])).replace("{{iso:%s}}" % n["about"], n["date"])
    body = body.replace("{{date:packing}}", "25 November 2026")
    return re.sub(r"\{\{(url|clip|illus|still|count):([^}]*)\}\}", lambda m: macro(m, ctx), body)

def cta_band(ctx):
    return (f'<section class="page-cta"><h2>Your checkpoint, built for your site.</h2><div class="btns">'
            f'<a class="btn btn-primary" href="{MAIL}">{CTA}</a>'
            f'<a class="btn btn-outline" href="{ctx.url("#video")}" data-open-video>{VIDEO_CTA}</a></div></section>')

# repeatable "count with its clip" rows, referenced from page templates
COUNTS = {
    "gate": lambda ctx: C.countrow(
        ctx, "gate-vehicle-plate",
        [("Checkpoint", "Vehicle gate"), ("Direction", "In"), ("Item", "Truck"), ("Plate", "UP16RT9643", "mono"),
         ("Time", "11:03:46", "mono"), ("Clip", "@clip")],
        caption="A real log row from the Healthfields gate. Every row works this way.",
        alt="A truck arrives at the gate and the vehicle log shows IN at 11:03:46."),
}

# ---------------------------------------------------------------- FAQ

FAQ_NOINT = [
    ("Does counting need an internet connection?",
     "No. Detection, counting, tracking, the review queue and the nightly reports all run on a computer on your site. If the connection drops, nothing stops."),
    ("How does the model improve without the internet?",
     "Retraining happens in our cloud, by agreement, or in your own cloud account if your images cannot leave it. The new model comes back as a signed file. Your computer checks the signature before installing it, and a person approves every promotion."),
    ("What leaves the site?",
     "Only what you agree to, such as the frames we pick for labelling. Live video and counts stay on your network."),
    ("Can it run on an air-gapped network?",
     "Yes. Nothing on site needs to reach the internet. Updates cross the gap as a signed file, in whatever way your security team approves."),
    ("Does it work with the cameras we already have?",
     "Usually, yes. At Healthfields it runs on the existing CCTV cameras. Tell us the camera and what you want counted, and we will tell you what to expect before you buy."),
    ("What hardware does it need?",
     "One GPU computer on site. At Healthfields, one such computer runs five services and four nightly reports."),
]
FAQ_HOW = [
    ("Do you need new cameras?", "Usually not. Healthfields runs on its existing CCTV cameras. Tell us the camera and what you want counted, and we will say what to expect before you buy."),
    ("What is a checkpoint?", "A fixed place where something has to be counted, logged or checked."),
    ("Who audits the counts?", "A person counts a random sample and compares it with the camera."),
    ("Does it need the internet?", "No. Counting, tracking and review run on a computer on your site."),
    ("What if the checkpoint is not on your list?", "Show us. We build for your site and are not limited to a fixed menu of models."),
]

def faq_ld(faq, path):
    return {"@type": "FAQPage", "@id": SITE + path + "#faq",
            "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}

def faq_html(faq):
    return '<div class="faq">' + "".join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q, a in faq) + "</div>"

# ---------------------------------------------------------------- pages

OGP = "assets/v3/og/"

def pages():
    P = []
    def add(**k):
        P.append(k)

    add(path="", layout="home", nav="", zebra_logo=True, body=home_body,
        title="VisorVolt: Any Checkpoint, Any Production Line, Counted and Audited",
        desc="VisorVolt builds a camera count or check for any checkpoint on your site. A person audits a sample, every count has its clip, and it runs with no internet.",
        og=OGP + "og-gate.jpg", og_alt="A truck at a vehicle gate with its number plate read and the time logged.",
        preload=('<link rel="preload" as="image" href="assets/v3/hero/hero-gate-exit-1280.webp" '
                 'imagesrcset="assets/v3/hero/hero-gate-exit-720.webp 720w, assets/v3/hero/hero-gate-exit-1280.webp 1280w" imagesizes="100vw" fetchpriority="high">\n'),
        ld=[ORG_FULL, {"@type": "WebSite", "@id": SITE + "#site", "url": SITE, "name": "VisorVolt", "publisher": {"@id": SITE + "#org"}}, VIDEO_LD])

    add(path="checkpoints/", nav="checkpoints/", body=checkpoints_body,
        title="Checkpoints: Gate, Dock, Line, Flows and Dispatch Counted | VisorVolt",
        desc="The checkpoints VisorVolt builds: vehicle gate, dock, people line, flows inside, packing line, dispatch and rule checks. Each with its count and the clip behind it.",
        og=OGP + "og-gate.jpg", og_alt="A vehicle gate where a truck's number plate is read and logged.",
        trail=[("Checkpoints", "checkpoints/")],
        ld=[ORG_REF, {"@type": "CollectionPage", "@id": SITE + "checkpoints/", "url": SITE + "checkpoints/", "name": "VisorVolt checkpoints", "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Checkpoints", "checkpoints/")])])

    add(path="transcript/", nav="", body=transcript_body,
        title="Transcript of the VisorVolt 2-Minute Video | VisorVolt",
        desc="The narration of the VisorVolt video: vehicle gate, dock, people line, flows inside, packing line and dispatch, counted and audited, each count kept with its clip.",
        og=OGP + "og-gate.jpg", og_alt="A truck at a vehicle gate with its number plate read and the time logged.",
        trail=[("Transcript", "transcript/")],
        ld=[ORG_REF, crumbs_ld([("Transcript", "transcript/")])])

    add(path="how-it-works/", nav="how-it-works/", body=page_body("how-it-works.html"),
        title="How VisorVolt Works: Built for Your Site, Audited, Better Every Month",
        desc="How a checkpoint goes live: we build it from your own footage, it runs on your site with no internet, a person audits a sample, and it improves every month.",
        og=OGP + "og-packing.jpg", og_alt="A packing line with a carton counter overlay.",
        trail=[("How it works", "how-it-works/")],
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "how-it-works/", "url": SITE + "how-it-works/", "name": "How VisorVolt works", "publisher": {"@id": SITE + "#org"}},
            faq_ld(FAQ_HOW, "how-it-works/"), crumbs_ld([("How it works", "how-it-works/")])])

    add(path="proof/", nav="proof/", body=page_body("proof.html"),
        title="Proof: Healthfields Counts v a Person, and 39 Datasets Tested | VisorVolt",
        desc="Dated results: 141 v 141 on a packing line over 38 sampled windows, 102 v 103 at dispatch, and a median 89% of a fully labelled model across 39 datasets.",
        og=OGP + "og-packing.jpg", og_alt="A packing line where cartons are counted.",
        trail=[("Proof", "proof/")],
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "proof/", "url": SITE + "proof/", "name": "VisorVolt proof", "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Proof", "proof/")])])

    add(path="company/", nav="company/", body=page_body("company.html"),
        title="About VisorVolt and Investors: Audited Camera Checkpoints",
        desc="VisorVolt turns any camera checkpoint into an audited count or check. Founder, what exists today, the market and the model in plain words, and how to reach us.",
        og=OGP + "og-company.jpg", og_alt="VisorVolt: audited camera checkpoints.",
        trail=[("Company", "company/")],
        ld=[ORG_FULL, {"@type": "AboutPage", "@id": SITE + "company/", "url": SITE + "company/", "name": "About VisorVolt and investors", "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Company", "company/")])])

    add(path="partners/", nav="partners/", zebra_logo=True, body=page_body("partners.html"),
        title="Partners | VisorVolt",
        desc="VisorVolt is delivered with Prolifics, a global systems integrator, and is a Zebra Technologies Registered ISV in North America and Asia-Pacific.",
        og="assets/og/partners.png", og_alt="VisorVolt partners: Prolifics and Zebra Technologies.",
        trail=[("Partners", "partners/")],
        ld=[ORG_REF, {"@type": "CollectionPage", "@id": SITE + "partners/", "url": SITE + "partners/", "name": "VisorVolt partners",
                      "about": [PROLIFICS, ZEBRA], "publisher": {"@id": SITE + "#org"}}, crumbs_ld([("Partners", "partners/")])])

    add(path="partners/prolifics/", nav="partners/", body=page_body("prolifics.html"),
        title="Prolifics and VisorVolt: Camera Checkpoints, Delivered by a Global SI",
        desc="Prolifics, a global systems integrator with 2,000+ experts and 150+ Fortune 1000 clients, delivers VisorVolt checkpoints to its clients in every industry.",
        og="assets/og/prolifics.png", og_alt="VisorVolt and Prolifics.",
        trail=[("Partners", "partners/"), ("Prolifics", "partners/prolifics/")],
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "partners/prolifics/", "url": SITE + "partners/prolifics/", "name": "Prolifics and VisorVolt",
                      "about": PROLIFICS, "publisher": {"@id": SITE + "#org"}}, crumbs_ld([("Partners", "partners/"), ("Prolifics", "partners/prolifics/")])])

    add(path="partners/zebra/", nav="partners/", zebra_logo=True, body=page_body("zebra.html"),
        title="VisorVolt Is a Zebra Technologies Registered ISV | Camera Checkpoints",
        desc="VisorVolt is a Registered ISV in Zebra Technologies' PartnerConnect program, in North America and Asia-Pacific, adding camera counts to sites that run on Zebra.",
        og="assets/og/zebra.png", og_alt="VisorVolt is a Zebra Technologies Registered ISV.",
        trail=[("Partners", "partners/"), ("Zebra Technologies", "partners/zebra/")],
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "partners/zebra/", "url": SITE + "partners/zebra/", "name": "VisorVolt, Zebra Technologies Registered ISV",
                      "about": ZEBRA, "publisher": {"@id": SITE + "#org"}}, crumbs_ld([("Partners", "partners/"), ("Zebra Technologies", "partners/zebra/")])])

    add(path="case-studies/", nav="proof/", body=page_body("case-studies.html"),
        title="Case studies | VisorVolt",
        desc="How VisorVolt runs at a customer site: counting on the cameras already there, with no internet. Case study: Healthfields, an ongoing deployment.",
        og=OGP + "og-healthfields.jpg", og_alt="VisorVolt case studies.",
        trail=[("Case studies", "case-studies/")],
        ld=[ORG_REF, {"@type": "CollectionPage", "@id": SITE + "case-studies/", "url": SITE + "case-studies/", "name": "VisorVolt case studies", "publisher": {"@id": SITE + "#org"}},
            crumbs_ld([("Case studies", "case-studies/")])])

    hf_path = "case-studies/healthfields/"
    add(path=hf_path, nav="proof/", ogtype="article", body=page_body("healthfields.html"),
        title="Healthfields Case Study: Cartons Counted v a Person | VisorVolt",
        desc="Healthfields counts cartons at dispatch and on a packing line on its existing cameras, with no internet. Dated results v a person, and a live progress log.",
        og=OGP + "og-healthfields.jpg", og_alt="Healthfields and VisorVolt.",
        trail=[("Case studies", "case-studies/"), ("Healthfields", hf_path)],
        ld=[ORG_REF, {"@type": "Article", "@id": SITE + hf_path + "#article", "url": SITE + hf_path, "mainEntityOfPage": SITE + hf_path,
                      "headline": "Healthfields counts cartons on the cameras it already had", "image": [SITE + OGP + "og-healthfields.jpg"],
                      "datePublished": HF["published"], "dateModified": LAST, "author": {"@id": SITE + "#org"}, "publisher": {"@id": SITE + "#org"},
                      "about": HEALTHFIELDS}, crumbs_ld([("Case studies", "case-studies/"), ("Healthfields", hf_path)])])

    add(path="no-internet/", nav="how-it-works/", body=page_body("no-internet.html"),
        title="Camera AI That Runs With No Internet | VisorVolt",
        desc="VisorVolt detects, counts and reviews on a computer on your site. Your video stays on your network. Updates arrive as a signed file that a person approves.",
        og="assets/og/no-internet.png", og_alt="VisorVolt runs on a computer on your site with no internet.",
        trail=[("How it works", "how-it-works/"), ("Runs with no internet", "no-internet/")],
        ld=[ORG_REF, {"@type": "WebPage", "@id": SITE + "no-internet/", "url": SITE + "no-internet/", "name": "Camera AI that runs with no internet", "publisher": {"@id": SITE + "#org"}},
            faq_ld(FAQ_NOINT, "no-internet/"), crumbs_ld([("How it works", "how-it-works/"), ("Runs with no internet", "no-internet/")])])

    add(path="news/", nav="proof/", body=page_body("news.html"),
        title="News | VisorVolt",
        desc="VisorVolt news: the Prolifics partnership, Zebra Technologies Registered ISV, and the Healthfields results measured against a person.",
        og="assets/og/news.png", og_alt="VisorVolt news.", trail=[("News", "news/")],
        ld=[ORG_REF, {"@type": "CollectionPage", "@id": SITE + "news/", "url": SITE + "news/", "name": "VisorVolt news", "publisher": {"@id": SITE + "#org"},
                      "hasPart": [{"@type": "NewsArticle", "headline": n["headline"], "url": SITE + n["path"], "datePublished": n["date"]} for n in NEWS]},
            crumbs_ld([("News", "news/")])])

    for n in NEWS:
        about = {"prolifics": PROLIFICS, "zebra": ZEBRA, "healthfields": HEALTHFIELDS}[n["about"]]
        add(path=n["path"], nav="proof/", ogtype="article", title=n["title"], desc=n["desc"], og=n["og"], og_alt=n["headline"],
            trail=[("News", "news/"), (n["crumb"], n["path"])], body=page_body(n["body"]),
            ld=[ORG_REF, {"@type": "NewsArticle", "@id": SITE + n["path"] + "#article", "url": SITE + n["path"], "mainEntityOfPage": SITE + n["path"],
                          "headline": n["headline"], "image": [SITE + n["og"]], "datePublished": n["date"], "dateModified": n.get("modified", n["date"]),
                          "author": {"@id": SITE + "#org"}, "publisher": {"@id": SITE + "#org"}, "about": about},
                crumbs_ld([("News", "news/"), (n["crumb"], n["path"])])])
    return P

# ---------------------------------------------------------------- home

CP_TILES = [
    ("gate", "Vehicle gate", "The truck is read by number plate and stamped with the time. A car is logged as a car.",
     "factory gates, quarries, construction sites, ports, cold stores, campuses.", "gate-vehicle-plate", None),
    ("dock", "Dock", "When a truck docks and when it leaves the dock, with the time of each.",
     "any site with loading bays.", "dock-in-out", None),
    ("turnaround", "Gate to gate", "One visit from the plate read on the way in to the plate read on the way out. In the clip: about 2 hours 16 minutes.",
     None, "gate-to-gate-turnaround", None),
    ("people", "People crossing a line", "Each person who crosses is detected and logged with the time.",
     "entrances, restricted areas, shift changes.", "people-line", None),
    ("flows", "Flows inside the site", "A loaded pallet followed from the dock to the store.",
     "factories, warehouses, cold stores, any place goods change rooms.", "pallet-dock-to-store", None),
    ("line", "Production line", "A running count of cartons at the packing line.",
     "any line where finished goods leave one point.", "packing-running-count", None),
    ("dispatch", "Dispatch", "Cartons counted live as they are loaded onto the truck.", None, None, "still-dock-truck"),
    ("rules", "Rules, such as protective gear", "The same checkpoint can apply a rule: full gear passes, a missing item is flagged.",
     None, "ppe-illustration", None),
]
STILL_ALT = {"still-dock-truck": "A truck at a loading dock during dispatch."}

def home_body(ctx):
    u = ctx.url
    tiles = []
    for anchor, title, sentence, where, clip_slug, still_name in CP_TILES:
        if clip_slug == "ppe-illustration":
            media = C.clip(ctx, clip_slug, badge="Illustration / demo", ar="960/416", label="protective gear demonstration")
        elif clip_slug:
            media = C.clip(ctx, clip_slug, ar="960/416", label=title.lower() + " clip")
        else:
            media = C.still(ctx, still_name, STILL_ALT[still_name], ar="960/416", sizes="(max-width:600px) 100vw, 300px")
        w = f'<p class="cp-where"><b>Where it shows up:</b> {where}</p>' if where else ""
        demo = '<p class="cp-where"><b>Illustration / demo, not a client result.</b></p>' if clip_slug == "ppe-illustration" else ""
        tiles.append(f'<article class="cp-tile">{media}<div class="cp-body"><h3><a href="{u("checkpoints/#" + anchor)}">{title}</a></h3>'
                     f'<p>{sentence}</p>{w}{demo}</div></article>')
    tiles.append(f'<article class="cp-tile cp-tile--cta"><h3>Not on the list? Show us your checkpoint.</h3>'
                 f'<a class="btn btn-primary" href="{MAIL}">{CTA}</a></article>')
    illus_cards = "".join(C.illus(ctx, s) for s in ("retail-receiving-door", "packing-line-pharma", "cold-chain-dock", "produce-shed-belt", "hospital-linen-door"))
    why = [
        ("The counts are audited.", "A person checks a random sample against the system."),
        ("Built for your site.", "Every checkpoint is defined from your own footage."),
        ("Runs on your site, and gets better every month.", "A person approves every update."),
        ("Any use case, any checkpoint.", "Not a fixed menu of models."),
        ("Starts from the cameras you already have.", "We tell you before you buy what to expect from yours."),
        ("Needs no internet.", "Your video stays on site."),
        ("Every count comes with its clip.", ""),
    ]
    why_html = "".join(f"<li><b>{a}</b>{f'<span>{b}</span>' if b else ''}</li>" for a, b in why)
    factory = C.illus(ctx, "factory-line-illustration")
    hero_alt = "A vehicle gate: a truck leaves, its number plate is read, and people are detected crossing."
    pb = "assets/v3/hero/hero-gate-exit"
    return f"""<section class="hero" aria-labelledby="h1">
  <div class="hero-media" role="img" aria-label="{hero_alt}">
    <img src="{u(pb + '-1280.webp')}" srcset="{u(pb + '-720.webp')} 720w, {u(pb + '-1280.webp')} 1280w" sizes="100vw" width="1280" height="718" alt="" fetchpriority="high" decoding="async">
    <video id="hero-video" muted loop playsinline preload="none" width="1280" height="718" aria-hidden="true"><source src="{u(pb + '.webm')}" type="video/webm"><source src="{u(pb + '.mp4')}" type="video/mp4"></video>
  </div>
  <div class="hero-inner">
    <p class="eyebrow">Cameras that count and check</p>
    <h1 id="h1">Any checkpoint. Any production line. VisorVolt builds it for your site.</h1>
    <p class="hero-sub">A camera at a gate, a dock, a line or a door becomes a count or a check that a person audits, with the clip behind every row.</p>
    <p class="hero-proof"><b>Dated proof</b>On 18 and 19 November 2026, a packing line was counted by camera at 141 cartons and by a person at 141, over 38 sampled windows on two days the system had never seen.</p>
    <p class="small">Healthfields, an ongoing deployment. Development-stage results, updated as we go.</p>
    <div class="btns"><a class="btn btn-primary" href="{MAIL}">{CTA}</a><a class="btn btn-outline" href="{u('#video')}" data-open-video>{VIDEO_CTA}</a></div>
    <p class="hero-links"><a class="text-link" href="{u('checkpoints/')}">See the checkpoints &rarr;</a></p>
  </div>
  <button type="button" class="hero-ctl" id="hero-ctl" data-label="background video" aria-pressed="false" aria-label="Pause background video">{C.PAUSE_PLAY}<span>Pause video</span></button>
</section>

<div class="trust"><ul>
  <li><span><strong>Audited:</strong> a person checks a random sample against the system.</span></li>
  <li><span>Runs on your site, <strong>with no internet needed.</strong></span></li>
  <li><span>Your video <strong>stays on site.</strong></span></li>
  <li><span>Every count comes <strong>with its clip.</strong></span></li>
  <li><span>Built for your site, and <strong>better every month.</strong></span></li>
</ul></div>

<section class="sec" id="checkpoints" aria-labelledby="cp-h">
  <div class="wrap">
    <p class="eyebrow">Checkpoints</p>
    <h2 id="cp-h">A checkpoint is any place where something has to be counted, logged or checked.</h2>
    <p class="sec-lede">Pick the place. We build the count or the check for it, from your own footage. The examples below are different checkpoints, not different products.</p>
    <div class="cp-grid">{"".join(tiles)}</div>
    <p class="sec-foot"><a class="text-link" href="{u('checkpoints/')}">See every checkpoint with its example &rarr;</a></p>
    <p class="small" style="margin-top:14px">Real footage is from Healthfields, with faces blurred. The protective-gear clip is a generated demonstration.</p>
  </div>
</section>

<section class="sec sec--alt" id="other-sites" aria-labelledby="os-h">
  <div class="wrap">
    <p class="eyebrow">Other kinds of site</p>
    <h2 id="os-h">The same checkpoint, in other kinds of site.</h2>
    <p class="sec-lede">These five pictures are generated illustrations, not customers. They show where the same gate, door and line checkpoints exist.</p>
    <div class="carousel" role="region" aria-label="Illustrations of checkpoints in other kinds of site" tabindex="0">{illus_cards}</div>
  </div>
</section>

<section class="sec" id="how" aria-labelledby="how-h">
  <div class="wrap">
    <p class="eyebrow">How it works</p>
    <h2 id="how-h">Built for your site, then audited.</h2>
    <ol class="how4">
      <li><h3>Show us the checkpoint.</h3><p>Send a few minutes of footage from one camera, or tell us what you want counted or checked.</p></li>
      <li><h3>We build it for your site.</h3><p>We pick about 40 images from your own footage and label them ourselves. There is no labelling project on your side.</p></li>
      <li><h3>It runs on your site.</h3><p>Counting and review happen on a computer on your site, with no internet needed. Every row is kept with its clip.</p></li>
      <li><h3>A person audits it, and it improves every month.</h3><p>A person counts a random sample and compares it with the camera. Misses feed the next version, and a person approves every change.</p></li>
    </ol>
    <p class="sec-foot"><a class="text-link" href="{u('how-it-works/')}">How it works in detail &rarr;</a></p>
  </div>
</section>

<section class="sec sec--dark" id="video" aria-labelledby="vid-h">
  <div class="wrap">
    <p class="eyebrow">Video</p>
    <h2 id="vid-h">Watch the 2-minute video.</h2>
    <p class="sec-lede">Real Healthfields footage and one labelled demonstration. Captions are on the picture.</p>
    <div class="vid" data-vid>
      <video playsinline preload="none" poster="{u(VIDEO_POSTER)}" width="1280" height="720" aria-label="VisorVolt in two minutes. Captions are burned into the picture."><source src="{u(VIDEO_MP4)}" type="video/mp4"></video>
      <button type="button" class="vid-play" aria-label="Play the 2-minute video"><span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 3l16 9-16 9z"/></svg></span></button>
    </div>
    <div class="vid-links"><a class="text-link" href="{u(TRANSCRIPT)}">Read the transcript</a></div>
  </div>
</section>

<section class="sec sec--alt" id="every-count" aria-labelledby="ec-h">
  <div class="wrap">
    <p class="eyebrow">Every count, with its clip</p>
    <h2 id="ec-h">Every count is kept apart, and every row has its clip.</h2>
    <p class="sec-lede">Counts are never added into one total. Each is kept by checkpoint, by door, by in or out, by item and by truck. Click a row and you see the clip it came from.</p>
    {COUNTS["gate"](ctx)}
  </div>
</section>

<section class="sec" id="why" aria-labelledby="why-h">
  <div class="wrap">
    <p class="eyebrow">Why VisorVolt</p>
    <h2 id="why-h">Seven reasons you can check.</h2>
    <div class="why">
      <ol>{why_html}</ol>
      <div class="why-side">{factory}</div>
    </div>
  </div>
</section>

<section class="sec sec--alt" id="proof" aria-labelledby="pr-h">
  <div class="wrap">
    <p class="eyebrow">Proof</p>
    <h2 id="pr-h">Measured against a person, on days the system had never seen.</h2>
    <div class="pcards">
      <article class="pcard">{C.still(ctx, "still-dock-truck", "A truck at a loading dock where cartons are counted at dispatch.", sizes="(max-width:960px) 100vw, 380px")}
        <div class="pcard-body"><span class="k">Dispatch</span><span class="big">102 v 103</span>
        <p>Healthfields, 12 October 2026. The camera counted 102 cartons loaded at the dock. A person counting each carton counted 103.</p>
        <a class="text-link" href="{u('case-studies/healthfields/')}">Read the case study &rarr;</a></div></article>
      <article class="pcard">{C.still(ctx, "still-packing-line", "A packing line where cartons are counted as they pass the sealer.", sizes="(max-width:960px) 100vw, 380px")}
        <div class="pcard-body"><span class="k">Packing line</span><span class="big">141 v 141</span>
        <p>Healthfields, 18 and 19 November 2026. The camera counted 141 cartons over 38 sampled windows. A person counted 141. 23 of the 38 windows matched exactly.</p>
        <p class="small">Packing line: 141 counted by camera v 141 by a person over 38 sampled windows on two unseen days. 95% range about 7% either way.</p></div></article>
      <article class="pcard"><div class="pcard-body" style="padding-top:28px"><span class="k">Research</span><span class="big">89%</span>
        <p>Forty labelled images reach a median of about 89% of a fully hand-labelled model, across 39 public datasets.</p>
        <a class="text-link" href="{u('proof/#research')}">How we tested it &rarr;</a></div></article>
    </div>
    <p class="small" style="margin-top:18px">Healthfields is an ongoing deployment. These are development-stage results, not final figures.</p>
  </div>
</section>

<section class="sec" id="research" aria-labelledby="re-h">
  <div class="wrap">
    <p class="eyebrow">Research</p>
    <h2 id="re-h">39 datasets. None of them ours. None of them failed.</h2>
    <p class="sec-lede" style="margin-bottom:20px">We built a model from 40 images on each of 39 public datasets we did not choose. The pass mark was set before we ran: under 55% of a fully labelled model counts as a failure. Zero of 39 hit it, with no per-domain tuning. The median was 89% of a fully hand-labelled model. For each site we pick the 40, so you do not run a labelling project.</p>
    <p class="sec-lede" style="margin-bottom:0">On frames with none of the target objects, the single 40-image model made 11.5 false detections per 100 frames, against 104.8 for the three separate single-object models it replaces, roughly 9 times fewer.</p>
    <div class="tiles"><div class="tile"><div class="tile-fig">89%</div><div class="tile-label">Median</div><p class="tile-def">Of a fully hand-labelled model, from 40 images.</p></div>
      <div class="tile"><div class="tile-fig">39</div><div class="tile-label">Public datasets</div><p class="tile-def">None of them chosen by us.</p></div>
      <div class="tile"><div class="tile-fig">0 of 39</div><div class="tile-label">Below the pass mark</div><p class="tile-def">The 55% pass mark was set before the run.</p></div></div>
    <p class="small">Public benchmark results. They show the method works across many kinds of image; they are not customer results.</p>
  </div>
</section>

<section class="sec sec--alt" id="partners" aria-labelledby="pa-h">
  <div class="wrap">
    <p class="eyebrow">Partners</p>
    <h2 id="pa-h">Delivered with partners.</h2>
    <div class="pstrip">
      <div class="pcell"><span class="logo-plate"><img src="{u('assets/partners/prolifics-wordmark.png')}" alt="Prolifics" width="214" height="32"></span>
        <p>Prolifics: a global systems integrator with 2,000+ experts, 150+ Fortune 1000 clients, 47+ years and 10 locations. Delivers VisorVolt to its clients in every industry.</p>
        <a class="text-link" href="{u('partners/prolifics/')}">Prolifics and VisorVolt &rarr;</a></div>
      <div class="pcell"><span class="zebra-mark"><img src="{u('assets/partners/zebra-logo-white.svg')}" alt="Zebra Technologies" width="150" height="46"></span>
        <p>Zebra Technologies Registered ISV, North America and Asia-Pacific.</p>
        <a class="text-link" href="{u('partners/zebra/')}">VisorVolt and Zebra &rarr;</a></div>
    </div>
  </div>
</section>

<section class="sec" id="company" aria-labelledby="co-h">
  <div class="wrap">
    <div class="teaser">
      <img src="{u('assets/v3/founder-480.webp')}" width="140" height="140" alt="Umang Sharma, Founder and CEO of VisorVolt." loading="lazy" decoding="async">
      <div>
        <h2 id="co-h">One person built this, and it is already running at a customer.</h2>
        <p class="sec-lede" style="margin-bottom:24px">VisorVolt is founded by Umang Sharma, formerly Lead Applied Scientist at TomTom. Today it has a customer under contract, a signed systems integrator agreement, Zebra Registered ISV status and published research. Investors: we would like to talk.</p>
        <div class="btns"><a class="btn btn-primary" href="{u('company/#investors')}">Read about the company and investors</a><a class="btn btn-outline" href="mailto:umang@visorvolt.ai">Write to umang@visorvolt.ai</a></div>
      </div>
    </div>
  </div>
</section>

<section class="sec cta-band" id="contact" aria-labelledby="ct-h">
  <div class="wrap">
    <h2 id="ct-h">Show us a checkpoint.</h2>
    <p>Send a few minutes of footage from one camera, or tell us what you want counted or checked. We will tell you what to expect before you buy.</p>
    <div class="btns"><a class="btn btn-primary" href="{MAIL}">{CTA}</a><a class="btn btn-outline" href="{u('#video')}" data-open-video>{VIDEO_CTA}</a></div>
  </div>
</section>"""

def transcript_body(ctx):
    with open(os.path.join(ROOT, "assets/v3/video/transcript.txt")) as f:
        txt = " ".join(f.read().split())
    paras = "".join(f"<p>{html.escape(x.strip())}.</p>" for x in txt.split(". ") if x.strip().rstrip("."))
    return (f'<header class="page-head"><h1>Transcript of the 2-minute video</h1>'
            f'<p class="page-lede">The narration, for reading or for screen readers. The video also has captions on the picture.</p>'
            f'<p><a class="btn btn-outline" href="{ctx.url("#video")}" data-open-video>{VIDEO_CTA}</a></p></header>{paras}')

# ---------------------------------------------------------------- checkpoints page

def cp_block(ctx, anchor, title, counts, count, where, media, caption=None, extra=""):
    pid = C.uid("cb")
    first_id = None
    rows = [("What it counts", counts), ("The count", count), ("Where else", where)]
    dl = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in rows)
    if media and media[0] == "clip":
        dl += f'<div><dt>Clip</dt><dd><button type="button" class="crow-play" data-play="{pid}">Play the clip</button></dd></div>'
    m = ""
    if media:
        kind = media[0]
        if kind == "clip":
            m += C.clip(ctx, media[1], pid=pid, alt=media[2] if len(media) > 2 else None)
            if len(media) > 3:
                m += C.clip(ctx, media[3], alt=media[4])
        elif kind == "still":
            m += C.still(ctx, media[1], media[2], sizes="(max-width:900px) 100vw, 560px")
    if caption:
        m += f'<p class="cap">{caption}</p>'
    return (f'<section class="cp-block" id="{anchor}"><div><h2>{title}</h2><dl class="crow-dl">{dl}</dl>{extra}'
            f'<p style="margin-top:18px"><a class="btn btn-primary" href="{MAIL}">{CTA}</a></p></div><div class="cp-media">{m}</div></section>')

def checkpoints_body(ctx):
    u = ctx.url
    b = []
    b.append(cp_block(ctx, "gate", "Vehicle gate",
        "Each vehicle that enters or leaves. The number plate is read and the time is stamped. A car is logged as a car, not as a truck.",
        "A truck arrives and the log shows IN at 11:03:46.",
        "Factory and warehouse gates, quarries and mines, construction sites, ports, cold stores, campuses.",
        ("clip", "gate-vehicle-plate", "A truck arrives at the gate. Its plate is read and the vehicle log shows IN at 11:03:46.", "gate-car-vs-truck",
         "A car passes the gate and is logged as a car, with no truck logged. The plate shown is a placeholder."),
        "Real footage from the Healthfields gate. The number plate on the car is a placeholder."))
    b.append(cp_block(ctx, "dock", "Dock", "When a truck docks and when it leaves the dock, with the time of each.",
        "Docks, time noted. Leaves the dock, time noted.",
        "Any site with loading bays: distribution, food and drink, pharma stores, retail receiving.",
        ("clip", "dock-in-out", "A truck at a dock, then leaving the dock, with log lines for each time."), "Real footage from Healthfields."))
    b.append(cp_block(ctx, "turnaround", "Gate to gate", "One visit from the plate read on the way in to the plate read on the way out.",
        "About 2 hours 16 minutes in the clip. Every turnaround is on record.",
        "Any site where waiting time costs money: ports, plants, quarries.",
        ("clip", "gate-to-gate-turnaround", "A truck exits through the gate, its plate read again, and the log shows a gate-to-gate time of 2 hours 16 minutes."),
        "Real footage from Healthfields."))
    b.append(cp_block(ctx, "people", "People crossing a line", "Each person who crosses a line, detected and logged with the time.",
        "Detections per crossing. Faces are blurred in everything we publish.",
        "Entrances, restricted zones, shift changes, site access points.",
        ("clip", "people-line", "People detected crossing a checkpoint line, with faces blurred."), "Real footage from Healthfields. Faces blurred."))
    b.append(cp_block(ctx, "flows", "Flows inside the site", "Goods moving between rooms: a loaded pallet followed from the dock to the store.",
        "One pallet, tracked from the dock camera to the store camera.",
        "Factories, warehouses, cold stores, kitchens, workshops.",
        ("clip", "pallet-dock-to-store", "A loaded pallet tracked from a dock camera to a store camera."), "Real footage from Healthfields."))
    b.append(cp_block(ctx, "line", "Production line", "A running count of cartons at the end of a packing line.",
        "141 cartons counted by camera and 141 by a person, over 38 sampled windows on two unseen days, 18 and 19 November 2026. Healthfields is ongoing, so this is development-stage evidence.",
        "Any line where finished goods leave one point: food, drink, consumer goods, parts, parcels.",
        ("clip", "packing-running-count", "A packing line carton counter going from 0 to 1 as a carton passes the turntable."),
        "Real footage from Healthfields.",
        extra=f'<p style="margin-top:14px"><a class="text-link" href="{u("case-studies/healthfields/#measured")}">See how it was measured &rarr;</a></p>'))
    b.append(cp_block(ctx, "dispatch", "Dispatch", "Cartons counted live as they are loaded onto the truck.",
        "On a day the model had never seen, the camera counted 102 cartons and a person counting each carton counted 103 (12 October 2026).",
        "Distribution centres, factories, cold chain, e-commerce fulfilment.",
        ("still", "still-dock-truck", "A truck at a loading dock during dispatch."), "Real image from Healthfields."))
    # every count kept apart: the same real row as the home page
    b.append(f'<section class="cp-block" id="kept-apart"><div><h2>Every count kept apart</h2>'
             f'<p>Counts are never netted into one number. Each is kept by checkpoint, by door, by in or out, by item and by truck, and every row comes from a clip.</p>'
             f'<p class="small">Example row (real): Vehicle gate | In | Truck | 11:03:46 | clip.</p></div>'
             f'<div class="cp-media">{COUNTS["gate"](ctx)}</div></section>')
    # rules: labelled demo
    pid = C.uid("cb")
    b.append(f'<section class="cp-block" id="rules"><div><p class="demo-label">Illustration / demo. Not a client result.</p><h2>Rules, such as protective gear</h2>'
             f'<p>The same checkpoint can apply a rule. Full gear passes. One item missing is flagged as partial. No gear is flagged. Each person is checked as they cross the line.</p>'
             f'<p>This is a generated demonstration of how a rule check would look. We have not measured accuracy for protective-gear checks and we are not claiming any.</p></div>'
             f'<div class="cp-media">{C.clip(ctx, "ppe-illustration", badge="Illustration / demo", pid=pid, label="protective gear demonstration")}'
             f'<p class="cap">Generated demonstration. The on-frame labels read DEMO FOOTAGE AI-GENERATED and DEMO NOT A CLIENT RESULT.</p></div></section>')
    illus_all = "".join(C.illus(ctx, s, t) for s, t in [
        ("construction-gate-illustration", "A mixer truck enters through a temporary site gate. The vehicle gate log works the same way: plate, time, in or out."),
        ("factory-line-illustration", "Cartons on a conveyor beside a robotic arm. A line count works the same way: one running count at the point where goods leave."),
        ("retail-receiving-door", None), ("packing-line-pharma", None), ("cold-chain-dock", None), ("produce-shed-belt", None), ("hospital-linen-door", None)])
    return f"""<header class="page-head">
  <h1>Checkpoints</h1>
  <p class="page-lede">A checkpoint is a fixed place where something has to be counted, logged or checked. Gate, dock, line, door. VisorVolt builds the count or the check for your site, a person audits a sample, and every row keeps its clip. The checkpoints below are examples, not a menu. If yours is not here, show us.</p>
  <p style="margin-top:22px"><a class="btn btn-primary" href="{MAIL}">{CTA}</a></p>
</header>

<section class="page-sec" aria-labelledby="kinds-h">
  <h2 id="kinds-h">Count it, log it, or check it.</h2>
  <div class="kinds">
    <div class="kind"><h3>Count</h3><p>How many passed this line? Cartons at a packing line, pallets from dock to store, cartons loaded at dispatch. Healthfields measures these against a person.</p></div>
    <div class="kind"><h3>Log</h3><p>Which vehicle or unit passed, and when? A truck's number plate read and stamped at the gate, dock times, gate-to-gate time. Matched to your own record where you have one.</p></div>
    <div class="kind"><h3>Check</h3><p>Is this present, in place, or following a rule? A second lane that we run in pilots. <a href="#check">See the end of this page.</a></p></div>
  </div>
</section>

<div class="page-sec" id="list">{"".join(b)}</div>

<section class="page-sec" id="industries" aria-labelledby="ind-h">
  <h2 id="ind-h">The same checkpoint, in other kinds of site.</h2>
  <p>These pictures are generated illustrations, not customers. They show where the same gate, door and line checkpoints exist.</p>
  <div class="illus-grid" style="margin-top:22px">{illus_all}</div>
</section>

<section class="page-sec" aria-labelledby="q4-h">
  <h2 id="q4-h">Four questions we ask before we take one on.</h2>
  <ol class="q4">
    <li>Is it a fixed place where we can see it?</li>
    <li>Is it something two careful people would count or judge the same way?</li>
    <li>Is there a record to compare with, such as a delivery note, a scan, a slip or a plate?</li>
    <li>Does money or a decision already depend on the answer?</li>
  </ol>
  <p style="margin-top:16px">If the answer to any of these is no, we will say so before you buy.</p>
</section>

<section class="page-sec" id="check" aria-labelledby="chk-h">
  <h2 id="chk-h">Check: is it there, is it in place?</h2>
  <p>Some checkpoints ask a yes or no question about a photo or a fixed view: is this part present, is this bay occupied. We run this lane in pilots, and we say so plainly. A truck-at-bay trigger has been running at Healthfields since October 2026.</p>
  <p>In a pilot with one of the world's largest telecom tower companies, on 74 towers the system had never seen, it flagged 42 of 45 photos with a bolt or rust fault and cleared 33 of 41 clean photos.</p>
</section>

{cta_band(ctx)}"""

# ---------------------------------------------------------------- output

def build(preview_dir=None):
    out = {}
    for p in pages():
        for preview in ([False, True] if preview_dir else [False]):
            out[(p["path"], preview)] = render(p, preview)
    for (path, preview), text in out.items():
        if preview:
            continue
        dst = os.path.join(ROOT, path, "index.html")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        with open(dst, "w") as f:
            f.write(text)
    write_sitemap()
    write_robots()
    write_404()
    if preview_dir:
        write_preview(preview_dir, out)
    print(f"built {len(pages())} pages; case study last updated {LAST}")

def write_sitemap():
    newest = max([LAST] + [n["date"] for n in NEWS])
    urls = []
    for p in pages():
        mod = newest if p["path"] == "" else "2026-11-25"
        if p["path"].startswith("case-studies"):
            mod = LAST
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
             og=OGP + "og-gate.jpg", og_alt="VisorVolt", ld=[ORG_REF], trail=None,
             body='<h1>That page is not here.</h1>\n<p class="page-lede">It may have moved. These are the pages people look for most.</p>\n'
                  '<ul class="link-list" style="margin-top:20px"><li><a href="/">Home</a></li><li><a href="/checkpoints/">Checkpoints</a></li>'
                  '<li><a href="/case-studies/healthfields/">Healthfields case study</a></li>'
                  '<li><a href="/partners/">Partners</a></li><li><a href="/news/">News</a></li></ul>')
    text = render(p, False)
    # 404.html is served from whatever URL was missed, so its links must be root-absolute.
    text = re.sub(r'(href|src|srcset|data-src|data-poster)="(\.\./)+', r'\1="/', text)
    text = re.sub(r'(href|src|data-src|data-poster)="(assets/|css/|js/|favicon|icon_)', r'\1="/\2', text)
    text = text.replace('<link rel="canonical" href="https://visorvolt.ai/404/">', '<meta name="robots" content="noindex">')
    with open(os.path.join(ROOT, "404.html"), "w") as f:
        f.write(text)

def write_preview(dst, out):
    """A copy that works from a file listing or any static host: every folder link ends in index.html."""
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
    for d in ("css", "js"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(dst, d))
    for f in ("favicon.svg", "favicon_32.png", "icon_192.png", "favicon.ico"):
        shutil.copy(os.path.join(ROOT, f), dst)
    for d in ("assets/v3", "assets/fonts", "assets/partners", "assets/case-studies", "assets/og"):
        shutil.copytree(os.path.join(ROOT, d), os.path.join(dst, d))
    print("preview written to", dst)

if __name__ == "__main__":
    prev = sys.argv[sys.argv.index("--preview") + 1] if "--preview" in sys.argv else None
    build(prev)
    import subprocess
    sys.exit(subprocess.call([sys.executable, os.path.join(B, "check.py")]))
