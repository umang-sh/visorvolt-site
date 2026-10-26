#!/usr/bin/env python3
"""Claims and hygiene checks for every published page. Exit code 1 on any failure.

Rules come from the claims registry (memory: visorvolt-website-gtm) and the 2026-10-26 redesign brief.
"""
import html, json, os, re, sys
from html.parser import HTMLParser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP = {"demo.html", "_probe_grid.html"}          # demo.html is left alone on purpose

BANNED = [  # (pattern, why)
    (r"—|&mdash;|&#8212;|&#x2014;", "em dash"),
    (r"(?i)\bzero labels\b|\bno labels\b|you never label|0 customer labels|zero retraining|zero-shot", "banned label claim"),
    (r"\b8[67](?:\.\d)?%", "86%/87% retired: quote 89%, the audited median across 39 datasets"),
    (r"[−-]4%|&minus;4%", "withdrawn -4% register claim"),
    (r"\+2%|0\.98\s*(?:x|&times;|×)", "superseded +2% / 0.98x claims"),
    (r"\b0\.8[1-8]\s*(?:x|&times;|×)", "whole-truck ratio"),
    (r"\bROI\b", "no ROI figure exists"),
    (r"(?i)\bclaude\b|chatgpt|\bLLMs?\b|\bGPT\b|large language model", "never name what the agent is built on"),
    (r"(?i)model-agnostic|no model of our own", "never model-agnostic"),
    (r"(?i)LAE-DINO|RF-DETR|V-JEPA|OWLv2|DINOv2|Grounding DINO|\bSAM ?3\b|\bQwen|\bYOLO", "internal model name"),
    (r"(?i)\bch(?:annel)?\s?\d{1,2}\b", "camera channel number: use the camera name"),
    (r"(?i)labell?ing is (?:our|the) moat", "labelling is never the moat"),
]
GUARDRAILS_HOME = ["we pick the 40", "None of them failed", "55%", "104.8"]

class Text(HTMLParser):
    BLOCK = {"p", "li", "h1", "h2", "h3", "h4", "dd", "dt", "figcaption", "summary", "td", "th", "blockquote", "title", "a"}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks, self.cur, self.skip = [], [], 0
        self.imgs, self.links, self.h1, self.ld, self._ld = [], [], 0, [], None
    def handle_starttag(self, tag, a):
        a = dict(a)
        if tag in ("script", "style"):
            self.skip += 1
            if tag == "script" and a.get("type") == "application/ld+json":
                self._ld = []
        if tag == "img":
            self.imgs.append(a)
        if tag in ("a", "link") and a.get("href"):
            self.links.append(a["href"])
        for k in ("src", "srcset"):
            if tag in ("img", "source", "script") and a.get(k):
                self.links += [u.strip().split(" ")[0] for u in a[k].split(",")]
        if tag == "h1":
            self.h1 += 1
        if tag in self.BLOCK:
            self.flush()
    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
            if self._ld is not None:
                self.ld.append("".join(self._ld)); self._ld = None
        if tag in self.BLOCK:
            self.flush()
    def handle_data(self, d):
        if self._ld is not None:
            self._ld.append(d)
        if not self.skip:
            self.cur.append(d)
    def flush(self):
        t = " ".join("".join(self.cur).split())
        if t:
            self.blocks.append(t)
        self.cur = []

def pages():
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if not d.startswith((".", "_")) and d != "assets"]
        for f in fn:
            if f.endswith(".html") and f not in SKIP:
                yield os.path.relpath(os.path.join(dp, f), ROOT)

def main():
    fails, titles, descs = [], {}, {}
    for rel in sorted(pages()):
        raw = open(os.path.join(ROOT, rel)).read()
        t = Text(); t.feed(raw); t.flush()
        text = "\n".join(t.blocks)
        visible_raw = re.sub(r"<script\b[^>]*>.*?</script>", "", raw, flags=re.S)
        for pat, why in BANNED:
            for m in re.finditer(pat, text + "\n" + visible_raw):
                ctx = (text + "\n" + visible_raw)[max(0, m.start() - 50):m.end() + 50].replace("\n", " ")
                fails.append(f"{rel}: {why}: ...{ctx}...")
                break
        # 89% must never sit beside a dataset count other than 39
        for m in re.finditer(r"89%[^.]{0,120}?(\d+) (?:public )?datasets|(\d+) (?:public )?datasets[^.]{0,120}?89%", text):
            n = m.group(1) or m.group(2)
            if n != "39":
                fails.append(f"{rel}: 89% paired with {n} datasets")
        # Prolifics before Zebra wherever both appear in one block
        for b in t.blocks:
            if "Prolifics" in b and "Zebra" in b and b.index("Zebra") < b.index("Prolifics"):
                fails.append(f"{rel}: Zebra before Prolifics in: {b[:120]}")
        # Zebra logo pages must carry the trademark sentence
        if "zebra-logo" in raw and "registered in many jurisdictions worldwide" not in raw:
            fails.append(f"{rel}: Zebra logo without the trademark attribution sentence")
        # hygiene
        title = re.search(r"<title>(.*?)</title>", raw, re.S)
        desc = re.search(r'<meta name="description" content="([^"]*)"', raw)
        if rel != "404.html":
            if t.h1 != 1:
                fails.append(f"{rel}: {t.h1} h1 elements")
            if not title or not desc:
                fails.append(f"{rel}: missing title or description")
            else:
                titles.setdefault(title.group(1), []).append(rel)
                descs.setdefault(desc.group(1), []).append(rel)
                if len(html.unescape(desc.group(1))) > 165:
                    fails.append(f"{rel}: description {len(desc.group(1))} chars")
            if 'rel="canonical"' not in raw:
                fails.append(f"{rel}: no canonical")
        for img in t.imgs:
            if "alt" not in img:
                fails.append(f"{rel}: img without alt: {img.get('src')}")
        for blob in t.ld:
            try:
                json.loads(blob)
            except ValueError as e:
                fails.append(f"{rel}: JSON-LD does not parse: {e}")
        # internal links and assets resolve
        base = os.path.dirname(os.path.join(ROOT, rel))
        for u in t.links:
            if re.match(r"^(https?:|mailto:|tel:|#|data:|//)", u) or not u:
                continue
            path = u.split("#")[0].split("?")[0]
            target = os.path.join(ROOT, path.lstrip("/")) if path.startswith("/") else os.path.normpath(os.path.join(base, path))
            if path.endswith("/") or os.path.isdir(target):
                target = os.path.join(target, "index.html")
            if not os.path.exists(target):
                fails.append(f"{rel}: broken link {u}")
        if rel == "index.html":
            for g in GUARDRAILS_HOME:
                if g not in text:
                    fails.append(f"index.html: guardrail missing: {g!r}")
    for d, (label) in ((titles, "title"), (descs, "description")):
        for k, v in d.items():
            if len(v) > 1:
                fails.append(f"duplicate {label} on {v}")
    for f in fails:
        print("FAIL", f)
    print(f"check: {len(fails)} failure(s) across {len(list(pages()))} pages")
    return 1 if fails else 0

if __name__ == "__main__":
    sys.exit(main())
