"""Reusable page components for the v3 site: looping clips, still images, the count-with-its-clip row, illustrations."""
import html

PAUSE_PLAY = ('<svg viewBox="0 0 12 12" aria-hidden="true"><rect class="i-pause" x="2" y="1.5" width="2.6" height="9" rx=".6"/>'
              '<rect class="i-pause" x="7.4" y="1.5" width="2.6" height="9" rx=".6"/><path class="i-play" d="M3 1.5v9l7.5-4.5z"/></svg>')

# real Healthfields clips (960 wide) and their default alt text
CLIPS = {
    "gate-vehicle-plate": (960, 416, "A truck arrives at a gate. Its number plate is read and the entry time is logged."),
    "gate-car-vs-truck": (960, 416, "A car passes the gate and is logged as a car, with no truck logged. The plate shown is a placeholder."),
    "dock-in-out": (960, 416, "A truck at a dock, then leaving the dock, with log lines showing each time."),
    "gate-to-gate-turnaround": (960, 416, "A truck leaving through the gate, its plate read again, and a log line showing a gate-to-gate time of 2 hours 16 minutes."),
    "people-line": (960, 538, "People detected crossing a checkpoint line, with faces blurred."),
    "pallet-dock-to-store": (960, 416, "A loaded pallet tracked from a dock camera to a store camera."),
    "packing-running-count": (960, 416, "A packing line carton counter going from 0 to 1 as a carton passes the turntable."),
    "ppe-illustration": (960, 416, "AI-generated demonstration: a person with a hard hat and vest passes, a person missing an item is flagged. Illustration, not a client result."),
}
# generated industry illustrations: slug -> (alt, caption)
ILLUS = {
    "retail-receiving-door": ("Illustration: a back-of-store receiving door where staff wheel a roll cage of boxes out. Generated image.",
                              "a receiving door in retail, counted in and out"),
    "packing-line-pharma": ("Illustration: a packing line with white cartons on a conveyor and gloved hands. Generated image.",
                            "a packing line, every carton counted"),
    "cold-chain-dock": ("Illustration: a cold-chain dock door with mist and a worker moving a pallet. Generated image.",
                        "a cold-chain dock door, pallet in and out"),
    "produce-shed-belt": ("Illustration: a produce shed belt carrying crates of tomatoes, hands only. Generated image.",
                          "a produce shed belt, crates counted"),
    "hospital-linen-door": ("Illustration: a hospital doorway with a linen cart pushed through by staff seen from behind. Generated image.",
                            "a hospital linen doorway"),
    "construction-gate-illustration": ("Illustration: a concrete mixer truck passing through a temporary construction site gate in dust. Generated image.",
                                       "a mixer truck enters through a temporary site gate"),
    "factory-line-illustration": ("Illustration: a robotic arm and cartons on a factory conveyor with a worker seen from behind. Generated image.",
                                  "a robotic arm and cartons on a factory conveyor"),
}


class Counter:
    n = 0


def uid(prefix):
    Counter.n += 1
    return f"{prefix}-{Counter.n}"


def clip(ctx, slug, alt=None, kind="clips", badge=None, ar=None, cover=None, label=None, pid=None):
    """A looping clip. The poster is a lazy image; the video is created visible only when scrolled into view."""
    if kind == "clips":
        w, h, dalt = CLIPS[slug]
    else:
        w, h, dalt = 960, 540, ILLUS[slug][0]
    alt = alt or dalt
    base = f"assets/v3/{kind}/{slug}"
    a = html.escape(alt, quote=True)
    pid = pid or uid("clip")
    badge_html = f'<span class="badge-illus">{badge}</span>' if badge else ""
    style = f' style="aspect-ratio:{ar or f"{w}/{h}"}"'
    lab = html.escape(label or "clip", quote=True)
    return (f'<div class="clipbox" id="{pid}" data-clip{style}>{badge_html}'
            f'<img src="{ctx.url(base + ".webp")}" width="{w}" height="{h}" alt="{a}" loading="lazy" decoding="async">'
            f'<video muted loop playsinline preload="none" width="{w}" height="{h}" aria-hidden="true" hidden>'
            f'<source src="{ctx.url(base + ".webm")}" type="video/webm"><source src="{ctx.url(base + ".mp4")}" type="video/mp4"></video>'
            f'<button type="button" class="clip-ctl" data-label="{lab}" aria-pressed="true" aria-label="Play {lab}" hidden>{PAUSE_PLAY}</button></div>')


def still(ctx, name, alt, ar="16/9", sizes="(max-width:900px) 100vw, 600px", cls="", eager=False):
    base = f"assets/v3/stills/{name}"
    a = html.escape(alt, quote=True)
    return (f'<div class="clipbox {cls}" style="aspect-ratio:{ar}"><img src="{ctx.url(base + "-800.webp")}" '
            f'srcset="{ctx.url(base + "-800.webp")} 800w, {ctx.url(base + "-1200.webp")} 1200w" sizes="{sizes}" '
            f'width="800" height="449" alt="{a}" {"" if eager else "loading=\"lazy\" "}decoding="async"></div>')


def illus(ctx, slug, long_caption=None):
    alt, cap = ILLUS[slug]
    text = long_caption or (cap[0].upper() + cap[1:] + ".")
    box = clip(ctx, slug, kind="illustrations", badge="Illustration", label="illustration, " + cap)
    return (f'<figure class="illus-card">{box}<figcaption><b>Illustration.</b> {text} '
            f'Generated image, not a customer.</figcaption></figure>')


def countrow(ctx, slug, fields, caption=None, alt=None, extra_cls=""):
    """The repeatable 'count with its clip' component: a real clip beside the log row it produced."""
    pid = uid("cr")
    rows = []
    for k, v, *rest in fields:
        mono = " class=\"mono\"" if rest and rest[0] == "mono" else ""
        if v == "@clip":
            v = f'<button type="button" class="crow-play" data-play="{pid}">Play the clip</button>'
        rows.append(f"<div><dt>{k}</dt><dd{mono}>{v}</dd></div>")
    w, h, _ = CLIPS[slug]
    box = clip(ctx, slug, alt=alt, pid=pid)
    cap = f'<p class="cap">{caption}</p>' if caption else ""
    return f'<div class="countrow {extra_cls}">{box}<dl class="crow-dl">{"".join(rows)}</dl>{cap}</div>'
