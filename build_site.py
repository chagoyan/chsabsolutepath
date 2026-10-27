#!/usr/bin/env python3
"""Builds the images, PDF, pages, index and site map for the CHSAbsolutePath practice site.

Run with:  python3 build_site.py
If the Netlify address changes, edit DOMAIN below and run it again.
Needs Google Chrome and the Pillow library (pip3 install pillow)."""
import html
import math
import os
import random
import signal
import subprocess
import tempfile
import time

from PIL import Image, ImageChops

SITE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "CHSAbsolutePath")
ROOT_NAME = "CHSAbsolutePath"
DOMAIN = "https://chsabsolutepath.netlify.app/"
WORK = tempfile.mkdtemp(prefix="chs_build_")  # scratch files and the Chrome profile go here
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
MONO = "Menlo, Consolas, monospace"


def out(rel):
    path = os.path.join(SITE, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def chrome(args, url, result, scale=1):
    """Run headless Chrome until `result` is written. Chrome here writes the file but doesn't exit, so we stop it."""
    if os.path.exists(result):
        os.remove(result)
    proc = subprocess.Popen(
        [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
         "--no-default-browser-check", f"--user-data-dir={WORK}/profile",
         f"--force-device-scale-factor={scale}", *args, url],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    try:
        last = -1
        for _ in range(240):
            time.sleep(0.25)
            size = os.path.getsize(result) if os.path.exists(result) else -1
            if size > 0 and size == last:
                return
            last = size
        raise SystemExit(f"Chrome did not write {result}")
    finally:
        os.killpg(proc.pid, signal.SIGKILL)
        proc.wait()


def screenshot(page_html, name, w, h, transparent=False, scale=1):
    page = os.path.join(WORK, name + ".html")
    png = os.path.join(WORK, name + ".png")
    with open(page, "w") as f:
        f.write(page_html)
    args = [f"--window-size={w},{h}", f"--screenshot={png}"]
    if transparent:
        args.append("--default-background-color=00000000")
    chrome(args, "file://" + page, png, scale)
    im = Image.open(png)
    im.load()
    if im.size != (w * scale, h * scale):
        raise SystemExit(f"{name}: expected {(w * scale, h * scale)}, got {im.size}")
    return im


def svg_page(svg):
    return ('<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:transparent}'
            'svg{display:block}</style>' + svg)


def render_svg(svg, name, w, h, transparent=False):
    return screenshot(svg_page(svg), name, w, h, transparent)


# ---------- shared drawing pieces ----------

def stars(w, h, n, seed, twinkle=None):
    r = random.Random(seed)
    dots = []
    for _ in range(n):
        x, y = r.uniform(0, w), r.uniform(0, h)
        size = r.choice([0.8, 1, 1.2, 1.5, 2])
        if twinkle is None:
            op = r.uniform(0.3, 0.9)
        else:
            phase = r.random()
            op = 0.2 + 0.7 * (0.5 + 0.5 * math.sin(2 * math.pi * (twinkle + phase)))
        dots.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{size}" fill="#fff" opacity="{op:.2f}"/>')
    return "".join(dots)


def caption(text, cx, cy, size=18):
    w = len(text) * size * 0.61 + 30
    h = size + 16
    return (f'<rect x="{cx - w / 2:.1f}" y="{cy - h / 2:.1f}" width="{w:.1f}" height="{h}" rx="{h / 2}" '
            f'fill="#0b1024" fill-opacity=".75" stroke="#f59e0b" stroke-opacity=".8" stroke-width="1.5"/>'
            f'<text x="{cx}" y="{cy + 1}" text-anchor="middle" dominant-baseline="middle" '
            f'font-family="{MONO}" font-size="{size}" fill="#fde68a">{html.escape(text)}</text>')


def rover_body(stripe="#f59e0b", eye="#2dd4bf"):
    wheels = "".join(
        f'<circle cx="{x}" cy="100" r="12" fill="#334155"/><circle cx="{x}" cy="100" r="4.5" fill="#94a3b8"/>'
        for x in (30, 64, 98))
    return (
        '<line x1="40" y1="62" x2="32" y2="36" stroke="#94a3b8" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="32" cy="33" r="4.5" fill="{stripe}"/>'
        '<rect x="84" y="32" width="6" height="30" rx="2" fill="#94a3b8"/>'
        '<rect x="72" y="16" width="32" height="18" rx="5" fill="#e2e8f0" stroke="#334155" stroke-width="3"/>'
        f'<circle cx="95" cy="25" r="4.5" fill="{eye}"/>'
        '<rect x="16" y="58" width="96" height="28" rx="6" fill="#e2e8f0"/>'
        f'<rect x="16" y="70" width="96" height="7" fill="{stripe}"/>'
        '<rect x="16" y="58" width="96" height="28" rx="6" fill="none" stroke="#334155" stroke-width="3"/>'
        '<path d="M30 86v6M64 86v6M98 86v6" stroke="#334155" stroke-width="4"/>' + wheels)


def rover(x, y, s=1, **kw):
    return f'<g transform="translate({x} {y}) scale({s})">{rover_body(**kw)}</g>'


STAR_POINTS = "50,6 61.2,36.6 93.8,37.8 68.1,57.9 77,89.2 50,71 23,89.2 31.9,57.9 6.2,37.8 38.8,36.6"


def svg(w, h, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<defs>{defs}</defs>{body}</svg>')


# ---------- icons ----------

def build_icons():
    with open(out("Assets/Icons/rover.svg"), "w") as f:
        f.write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">\n'
                f'  <title>rover.svg</title>\n  {rover_body()}\n</svg>\n')

    fav = svg(256, 256,
              '<rect x="8" y="8" width="240" height="240" rx="56" fill="#0b1024"/>'
              f'<g transform="translate(28 30) scale(2)"><polygon points="{STAR_POINTS}" fill="#fbbf24" '
              'stroke="#d97706" stroke-width="5" stroke-linejoin="round"/></g>')
    im = render_svg(fav, "favicon", 256, 256, transparent=True)
    im.save(out("favicon.ico"), sizes=[(16, 16), (32, 32), (48, 48), (64, 64)])


# ---------- pictures ----------

def build_cat():
    defs = ('<radialGradient id="bg" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#2a1f5c"/>'
            '<stop offset="1" stop-color="#0b1024"/></radialGradient>')
    whiskers = ('<path d="M240 350 L165 333 M240 362 L163 368 M360 350 L435 333 M360 362 L437 368" '
                'stroke="#fff7ed" stroke-width="4" stroke-linecap="round"/>')
    body = (
        '<rect width="600" height="600" fill="url(#bg)"/>' + stars(600, 600, 90, 1) +
        '<path d="M110 600 C125 470 475 470 490 600 Z" fill="#e2e8f0"/>'
        '<rect x="262" y="520" width="76" height="30" rx="6" fill="#f59e0b"/>'
        '<path d="M188 262 L210 128 L292 212 Z" fill="#f59e0b"/><path d="M412 262 L390 128 L308 212 Z" fill="#f59e0b"/>'
        '<path d="M208 228 L218 160 L262 208 Z" fill="#f9a8d4"/><path d="M392 228 L382 160 L338 208 Z" fill="#f9a8d4"/>'
        '<ellipse cx="300" cy="300" rx="138" ry="122" fill="#f59e0b"/>'
        '<path d="M300 186v34M268 192l8 30M332 192l-8 30" stroke="#d97706" stroke-width="10" stroke-linecap="round"/>'
        '<ellipse cx="248" cy="288" rx="31" ry="35" fill="#fff"/><ellipse cx="352" cy="288" rx="31" ry="35" fill="#fff"/>'
        '<circle cx="254" cy="295" r="17" fill="#0f172a"/><circle cx="358" cy="295" r="17" fill="#0f172a"/>'
        '<circle cx="260" cy="287" r="6" fill="#fff"/><circle cx="364" cy="287" r="6" fill="#fff"/>'
        '<ellipse cx="300" cy="352" rx="58" ry="40" fill="#fde68a"/>'
        '<path d="M285 334h30l-15 17z" fill="#f472b6" stroke-linejoin="round"/>'
        '<path d="M300 351q-12 20-27 8M300 351q12 20 27 8" stroke="#7c2d12" stroke-width="5" fill="none" stroke-linecap="round"/>'
        + whiskers +
        '<circle cx="300" cy="300" r="206" fill="#93c5fd" fill-opacity=".12" stroke="#cbd5e1" stroke-width="16"/>'
        '<path d="M160 230 A155 155 0 0 1 250 136" stroke="#fff" stroke-opacity=".55" stroke-width="14" fill="none" stroke-linecap="round"/>'
        + caption("Images/cat.png", 300, 566))
    render_svg(svg(600, 600, body, defs), "cat", 600, 600).convert("RGB").save(out("Images/cat.png"), optimize=True)


def build_planet():
    defs = ('<linearGradient id="pg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#5eead4"/>'
            '<stop offset=".55" stop-color="#7c3aed"/><stop offset="1" stop-color="#312e81"/></linearGradient>'
            '<radialGradient id="shade" cx="35%" cy="30%" r="75%"><stop offset=".55" stop-color="#000" stop-opacity="0"/>'
            '<stop offset="1" stop-color="#000" stop-opacity=".45"/></radialGradient>'
            '<clipPath id="ball"><circle cx="300" cy="285" r="150"/></clipPath>'
            '<clipPath id="front"><rect x="-200" y="285" width="1000" height="600"/></clipPath>')
    ring = ('<ellipse cx="300" cy="285" rx="255" ry="62" fill="none" stroke="#fbbf24" stroke-width="18" opacity=".95"/>'
            '<ellipse cx="300" cy="285" rx="222" ry="49" fill="none" stroke="#fde68a" stroke-width="6" opacity=".8"/>')
    sparkle = lambda x, y, s: (f'<path d="M{x} {y - s}L{x + s * .25} {y - s * .25}L{x + s} {y}L{x + s * .25} {y + s * .25}'
                               f'L{x} {y + s}L{x - s * .25} {y + s * .25}L{x - s} {y}L{x - s * .25} {y - s * .25}Z" fill="#fde68a"/>')
    body = (
        sparkle(90, 90, 18) + sparkle(520, 70, 12) + sparkle(540, 470, 16) + sparkle(70, 430, 10) +
        '<g transform="rotate(-18 300 285)">' + ring +
        '<circle cx="300" cy="285" r="150" fill="url(#pg)"/>'
        '<g clip-path="url(#ball)"><rect x="100" y="205" width="400" height="22" fill="#fff" opacity=".28"/>'
        '<rect x="100" y="262" width="400" height="12" fill="#1e1b4b" opacity=".35"/>'
        '<rect x="100" y="318" width="400" height="30" fill="#fff" opacity=".18"/>'
        '<circle cx="300" cy="285" r="150" fill="url(#shade)"/></g>'
        '<g clip-path="url(#front)">' + ring + '</g></g>'
        + caption("Images/planet.png", 300, 562))
    render_svg(svg(600, 600, body, defs), "planet", 600, 600, transparent=True).save(out("Images/planet.png"), optimize=True)


def build_banner():
    defs = ('<linearGradient id="sky" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0b1024"/>'
            '<stop offset=".5" stop-color="#2a1f5c"/><stop offset="1" stop-color="#0b1024"/></linearGradient>'
            '<radialGradient id="n1"><stop offset="0" stop-color="#f472b6" stop-opacity=".5"/><stop offset="1" stop-color="#f472b6" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="n2"><stop offset="0" stop-color="#2dd4bf" stop-opacity=".4"/><stop offset="1" stop-color="#2dd4bf" stop-opacity="0"/></radialGradient>')
    body = (
        '<rect width="1200" height="400" fill="url(#sky)"/>'
        '<ellipse cx="300" cy="110" rx="340" ry="170" fill="url(#n1)"/>'
        '<ellipse cx="880" cy="300" rx="400" ry="180" fill="url(#n2)"/>' + stars(1200, 400, 170, 2) +
        '<g transform="rotate(-15 1040 110)"><ellipse cx="1040" cy="110" rx="100" ry="22" fill="none" stroke="#fbbf24" stroke-width="7"/>'
        '<circle cx="1040" cy="110" r="56" fill="#7c3aed"/><circle cx="1040" cy="110" r="56" fill="#5eead4" opacity=".35"/>'
        '<path d="M940 110 A100 22 0 0 0 1140 110" fill="none" stroke="#fbbf24" stroke-width="7"/></g>'
        '<path d="M0 340 Q150 300 300 330 T620 330 T940 335 T1200 325 V400 H0 Z" fill="#1e1b4b"/>'
        + rover(110, 238, 0.85) +
        f'<text x="600" y="190" text-anchor="middle" font-family="{MONO}" font-size="62" font-weight="700" '
        f'letter-spacing="3" fill="#fff">{ROOT_NAME}</text>'
        f'<text x="600" y="240" text-anchor="middle" font-family="{MONO}" font-size="22" fill="#fde68a">'
        'files for your web page, live on the internet</text>'
        + caption("Images/banner.jpg", 1050, 370, 16))
    render_svg(svg(1200, 400, body, defs), "banner", 1200, 400).convert("RGB").save(
        out("Images/banner.jpg"), quality=86, optimize=True)


def build_hero():
    defs = ('<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e1b4b"/>'
            '<stop offset=".5" stop-color="#6d28d9"/><stop offset="1" stop-color="#fb923c"/></linearGradient>'
            '<radialGradient id="glow"><stop offset="0" stop-color="#fde68a" stop-opacity=".9"/>'
            '<stop offset="1" stop-color="#fde68a" stop-opacity="0"/></radialGradient>')
    body = (
        '<rect width="1200" height="600" fill="url(#sky)"/>' + stars(1200, 260, 110, 3) +
        '<circle cx="840" cy="330" r="230" fill="url(#glow)"/><circle cx="840" cy="330" r="110" fill="#fde68a"/>'
        '<path d="M0 380 Q200 320 400 370 T800 360 T1200 350 V600 H0 Z" fill="#7c2d12"/>'
        '<path d="M0 450 Q300 390 600 440 T1200 430 V600 H0 Z" fill="#9a3412"/>'
        '<path d="M0 520 Q350 470 700 510 T1200 500 V600 H0 Z" fill="#c2410c"/>'
        '<path d="M0 548 Q160 520 330 512" fill="none" stroke="#7c2d12" stroke-width="5" stroke-dasharray="10 8"/>'
        + rover(318, 330, 1.6) +
        caption("Images/ProductPhotos/hero_image.jpg", 820, 562, 18))
    render_svg(svg(1200, 600, body, defs), "hero", 1200, 600).convert("RGB").save(
        out("Images/ProductPhotos/hero_image.jpg"), quality=86, optimize=True)


def build_team():
    defs = ('<radialGradient id="sky" cx="50%" cy="0%" r="100%"><stop offset="0" stop-color="#2a1f5c"/>'
            '<stop offset="1" stop-color="#0b1024"/></radialGradient>')
    body = (
        '<rect width="900" height="600" fill="url(#sky)"/>' + stars(900, 420, 120, 4) +
        '<circle cx="730" cy="120" r="56" fill="#3b82f6"/>'
        '<path d="M700 92q18-10 30 4t-8 26q-20 6-26-10t4-20zM745 140q16-4 22 10t-12 18q-14 0-16-12t6-16z" fill="#22c55e"/>'
        '<path d="M0 420 Q450 380 900 420 V600 H0 Z" fill="#64748b"/>'
        '<ellipse cx="140" cy="500" rx="60" ry="14" fill="#475569"/><ellipse cx="700" cy="530" rx="80" ry="16" fill="#475569"/>'
        + rover(112, 268, 1.5, stripe="#f59e0b", eye="#2dd4bf")
        + rover(354, 260, 1.5, stripe="#2dd4bf", eye="#f472b6")
        + rover(596, 268, 1.5, stripe="#f472b6", eye="#fbbf24") +
        f'<text x="40" y="70" font-family="{MONO}" font-size="34" font-weight="700" fill="#fff">TEAM PHOTO</text>'
        f'<text x="40" y="104" font-family="{MONO}" font-size="18" fill="#fde68a">the rover crew</text>'
        + caption("Images/ProductPhotos/team_photo.webp", 450, 560, 18))
    render_svg(svg(900, 600, body, defs), "team", 900, 600).convert("RGB").save(
        out("Images/ProductPhotos/team_photo.webp"), quality=85)


def dog_frame(i, n):
    t = i / n
    bob = 8 * math.sin(2 * math.pi * t)
    ear = 8 * math.sin(2 * math.pi * t)
    tongue = 6 * abs(math.sin(2 * math.pi * t))
    head = (
        '<path d="M70 400 C80 318 320 318 330 400 Z" fill="#e2e8f0"/>'
        f'<ellipse cx="116" cy="178" rx="32" ry="64" fill="#6b3e26" transform="rotate({22 + ear} 116 128)"/>'
        f'<ellipse cx="284" cy="178" rx="32" ry="64" fill="#6b3e26" transform="rotate({-22 - ear} 284 128)"/>'
        '<ellipse cx="200" cy="188" rx="92" ry="84" fill="#c08552"/>'
        '<ellipse cx="238" cy="166" rx="30" ry="26" fill="#8b5a3c"/>'
        '<circle cx="165" cy="168" r="13" fill="#1f2937"/><circle cx="235" cy="168" r="13" fill="#1f2937"/>'
        '<circle cx="169" cy="163" r="4" fill="#fff"/><circle cx="239" cy="163" r="4" fill="#fff"/>'
        '<ellipse cx="200" cy="224" rx="52" ry="38" fill="#f5e6d3"/>'
        f'<path d="M189 236h22v{10 + tongue:.1f}a11 11 0 0 1-22 0Z" fill="#f472b6"/>'
        '<ellipse cx="200" cy="206" rx="17" ry="12" fill="#1f2937"/>'
        '<path d="M200 217v12M200 229q-14 12-26 2M200 229q14 12 26 2" stroke="#1f2937" stroke-width="4" '
        'fill="none" stroke-linecap="round"/>'
        '<circle cx="200" cy="188" r="134" fill="#93c5fd" fill-opacity=".1" stroke="#cbd5e1" stroke-width="12"/>'
        '<path d="M98 140 A105 105 0 0 1 160 76" stroke="#fff" stroke-opacity=".5" stroke-width="10" fill="none" stroke-linecap="round"/>'
        '<circle cx="200" cy="339" r="17" fill="#fbbf24" stroke="#b45309" stroke-width="3"/>'
        f'<text x="200" y="340" text-anchor="middle" dominant-baseline="middle" font-family="{MONO}" '
        'font-size="12" font-weight="700" fill="#78350f">404</text>')
    defs = ('<radialGradient id="bg" cx="50%" cy="40%" r="75%"><stop offset="0" stop-color="#3b1d6e"/>'
            '<stop offset="1" stop-color="#0b1024"/></radialGradient>')
    body = ('<rect width="400" height="400" fill="url(#bg)"/>' + stars(400, 400, 55, 5, twinkle=t) +
            f'<g transform="translate(0 {bob:.1f})">{head}</g>' + caption("Images/Pets/my_dog.gif", 200, 384, 13))
    return f'<g transform="translate({i * 400} 0)"><svg width="400" height="400" viewBox="0 0 400 400">' \
           f'<defs>{defs}</defs>{body}</svg></g>'


def build_dog():
    n = 8
    sheet = svg(400 * n, 400, "".join(dog_frame(i, n) for i in range(n)))
    im = render_svg(sheet, "dog", 400 * n, 400).convert("RGB")
    frames = [im.crop((i * 400, 0, (i + 1) * 400, 400)) for i in range(n)]
    palette = frames[0].quantize(colors=200, method=Image.Quantize.MEDIANCUT)
    frames = [f.quantize(palette=palette, dither=Image.Dither.NONE) for f in frames]
    frames[0].save(out("Images/Pets/my_dog.gif"), save_all=True, append_images=frames[1:],
                   duration=110, loop=0, optimize=False)


# ---------- PDF ----------

STUDY_GUIDE_CSS = """
@page { size: letter; margin: 0.55in 0.6in; }
body { font-family: -apple-system, "Helvetica Neue", Arial, sans-serif; color: #0f172a; font-size: 11pt; line-height: 1.4; margin: 0; }
h1 { font-size: 21pt; margin: 0; color: #b45309; }
.sub { color: #475569; margin: 2pt 0 10pt; font-family: Menlo, monospace; font-size: 9.5pt; }
h2 { font-size: 13pt; margin: 14pt 0 6pt; border-bottom: 2px solid #f59e0b; padding-bottom: 2pt; }
code { font-family: Menlo, Consolas, monospace; font-size: 9.5pt; background: #f1f5f9; padding: 0 3pt; border-radius: 3pt; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #cbd5e1; padding: 4pt 6pt; vertical-align: top; text-align: left; }
th { background: #fef3c7; }
.url { font-family: Menlo, Consolas, monospace; font-size: 12.5pt; padding: 9pt 12pt; background: #0b1024; color: #e6e9f2; border-radius: 6pt; }
.r { color: #fbbf24; } .f { color: #5eead4; } .n { color: #f9a8d4; }
.key b { padding: 0 4pt; border-radius: 3pt; color: #0b1024; }
.key .kr { background: #fbbf24; } .key .kf { background: #5eead4; } .key .kn { background: #f9a8d4; }
ul, ol { margin: 4pt 0; padding-left: 18pt; } li { margin: 2pt 0; }
.answers { margin-top: 12pt; font-size: 9pt; color: #64748b; border-top: 1px dashed #cbd5e1; padding-top: 6pt; }
"""


def build_pdf():
    d = DOMAIN
    body = f"""
<h1>Absolute Paths Study Guide</h1>
<p class="sub">{ROOT_NAME} / Docs / study_guide.pdf</p>

<h2>Relative path vs. absolute path</h2>
<table>
<tr><th></th><th>Relative path</th><th>Absolute path (full web address)</th></tr>
<tr><td>Starts from</td><td>The file you are writing in</td><td>The root of a website on the internet</td></tr>
<tr><td>Example</td><td><code>Images/cat.png</code></td><td><code>{d}Images/cat.png</code></td></tr>
<tr><td>Works from</td><td>Pages inside the same site</td><td>Any page, anywhere</td></tr>
<tr><td>Practice it in</td><td>Route 404</td><td>This site</td></tr>
</table>

<h2>The three parts of a full address</h2>
<div class="url"><span class="r">{d}</span><span class="f">Images/Pets/</span><span class="n">my_dog.gif</span></div>
<ul class="key">
<li><b class="kr">Site root</b> <code>https://</code> + the domain + <code>/</code>. It stands for the {ROOT_NAME} folder.</li>
<li><b class="kf">Folders</b> every folder from the root down to the file, each followed by <code>/</code>.</li>
<li><b class="kn">File name</b> the exact name, including its extension.</li>
</ul>

<h2>Build one in three steps</h2>
<ol>
<li>Find the file on the site map.</li>
<li>Start with the site root: <code>{d}</code></li>
<li>Add each folder on the way to the file, then the file name.</li>
</ol>

<h2>Common mistakes</h2>
<table>
<tr><th>Mistake</th><th>Wrong</th><th>Fix</th></tr>
<tr><td>Typing the top folder's name</td><td><code>…app/{ROOT_NAME}/Images/cat.png</code></td><td>The site root already means that folder. Leave it out.</td></tr>
<tr><td>Skipping a folder</td><td><code>…app/my_dog.gif</code></td><td>Name every folder: <code>…app/Images/Pets/my_dog.gif</code></td></tr>
<tr><td>Wrong capitals</td><td><code>…app/images/cat.png</code></td><td>Copy the capitals exactly from the map.</td></tr>
<tr><td>No extension</td><td><code>…app/Images/cat</code></td><td>End with the extension, like <code>.png</code></td></tr>
<tr><td>A path from your computer</td><td><code>C:/Users/…/cat.png</code></td><td>Nobody else can see your computer. Use the web address.</td></tr>
<tr><td>Backslashes</td><td><code>Images\\cat.png</code></td><td>Web addresses use forward slashes: <code>/</code></td></tr>
</table>

<h2>Check yourself</h2>
<ol>
<li>Write the full address for <code>star.svg</code>. It is in Assets, inside Icons.</li>
<li>What is wrong with <code>{d}Styles/Theme.css</code>?</li>
<li>Why does a page on your computer need the full address instead of <code>Images/cat.png</code>?</li>
</ol>
<p class="answers">Answers: (1) {d}Assets/Icons/star.svg &nbsp; (2) The file is theme.css with a lowercase t. &nbsp;
(3) A relative path starts from your page's own folder on your computer, and the file isn't there.</p>
"""
    page = os.path.join(WORK, "study_guide.html")
    with open(page, "w") as f:
        f.write(f'<!doctype html><html><head><meta charset="utf-8"><style>{STUDY_GUIDE_CSS}</style></head><body>{body}</body></html>')
    pdf = out("Docs/study_guide.pdf")
    chrome([f"--print-to-pdf={pdf}", "--no-pdf-header-footer"], "file://" + page, pdf)


# ---------- pages ----------

PAGE_CSS = """
body { margin: 0; background: #0b1024; color: #e6e9f2; font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; line-height: 1.6; }
main { max-width: 760px; margin: 0 auto; padding: 32px 16px 48px; }
.arrived { display: flex; gap: 14px; align-items: center; padding: 14px 16px; border: 1px solid #1f6f66; border-radius: 12px; background: #0f3b3a; }
.arrived img { width: 56px; height: 56px; flex: none; }
.arrived p { margin: 0; }
.url { color: #fde68a; word-break: break-all; }
h1 { color: #f59e0b; margin: 28px 0 8px; }
h2, h3 { color: #fbbf24; margin-bottom: 4px; }
a { color: #2dd4bf; }
code { background: #1e293b; padding: 1px 6px; border-radius: 4px; color: #fde68a; overflow-wrap: anywhere; }
.photo { display: block; max-width: 100%; height: auto; border-radius: 12px; }
.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 16px; margin-top: 16px; }
figure { margin: 0; padding: 10px; background: #111a2e; border: 1px solid #2a3550; border-radius: 12px; }
figure img { width: 100%; height: 150px; object-fit: contain; }
figcaption { margin-top: 8px; font-size: 13px; color: #9aa4bf; overflow-wrap: anywhere; }
.back { display: inline-block; margin-top: 28px; }
"""

GALLERY = [
    ("../Images/banner.jpg", f"{ROOT_NAME} banner with a rover and a ringed planet"),
    ("../Images/cat.png", "An orange cat in a space helmet"),
    ("../Images/planet.png", "A purple ringed planet"),
    ("../Images/Pets/my_dog.gif", "An animated dog in a space helmet"),
    ("../Images/ProductPhotos/hero_image.jpg", "A rover on orange hills at sunrise"),
    ("../Images/ProductPhotos/team_photo.webp", "Three rovers lined up for a team photo"),
    ("../Assets/Icons/star.svg", "A smiling gold star"),
]

PAGES = {
    "about_us.html": ("About us", f"""
<h1>About us</h1>
<p>We're the rover crew. We drive around {ROOT_NAME} and deliver files to any web page that asks for them by their full address.</p>
<img class="photo" src="../Images/ProductPhotos/team_photo.webp" alt="Three rovers lined up for a team photo">
<p>Our motto: <strong>no address, no delivery.</strong></p>"""),

    "blog.html": ("Blog", f"""
<h1>Rover Blog</h1>
<h2>Day 404: The missing folder</h2>
<p>This morning a page asked me for <code>{DOMAIN}planet.png</code>.</p>
<p>I drove to the root and looked around: <code>favicon.ico</code>, <code>index.html</code>, <code>robots.txt</code>, <code>site_map.png</code>. No planet. I came home empty-handed.</p>
<p>The planet lives inside the <code>Images</code> folder, and the page forgot to say so. Ten minutes later it asked for <code>{DOMAIN}Images/planet.png</code>, and I delivered it in under a second.</p>
<p><strong>Lesson:</strong> name every folder on the way to the file.</p>"""),

    "faq.html": ("FAQ", f"""
<h1>FAQ</h1>
<h3>Why does my page need the whole https:// address?</h3>
<p>Your page lives on your computer. These files live on the internet. A short path like <code>Images/cat.png</code> makes the browser look for a folder on your computer.</p>
<h3>Do I type {ROOT_NAME} in the address?</h3>
<p>No. <code>{DOMAIN}</code> already stands for that folder. Start with the folders inside it.</p>
<h3>My image shows a broken icon. Now what?</h3>
<p>Copy the address out of your <code>src</code> and paste it into the browser's address bar. If the file doesn't open there, the address is wrong. Check the site map again.</p>
<h3>Do capital letters matter?</h3>
<p>Yes. Type every folder and file name exactly as the site map shows it.</p>
<h3>Do I need the file extension?</h3>
<p>Yes. <code>cat</code> and <code>cat.png</code> are different names. Always end with the extension.</p>"""),

    "news.html": ("News", """
<h1>News</h1>
<h3>Rover finds favicon.ico</h3>
<p>It was at the root all along, right next to index.html.</p>
<h3>New photos arrive</h3>
<p>Two new pictures landed in the ProductPhotos folder, inside Images.</p>
<h3>Dog spotted in Pets</h3>
<p>Witnesses say it moves. Find my_dog.gif and see for yourself.</p>"""),

    "photo_gallery.html": ("Photo Gallery", """
<h1>Photo Gallery</h1>
<p>This page lives <em>on</em> the site, so it can use short relative paths like <code>../Images/cat.png</code>, just like in Route 404.
Your page in VS Code lives on your computer, so it needs the full address instead.</p>
<div class="gallery">
""" + "\n".join(f'  <figure><img src="{src}" alt="{alt}"><figcaption>{src}</figcaption></figure>' for src, alt in GALLERY) + """
</div>"""),
}


def build_pages():
    for name, (title, body) in PAGES.items():
        with open(out("Pages/" + name), "w") as f:
            f.write(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {ROOT_NAME}</title>
<link rel="icon" href="../favicon.ico">
<style>{PAGE_CSS}</style>
</head>
<body>
<main>
  <div class="arrived">
    <img src="../Assets/Icons/rover.svg" alt="">
    <div>
      <p><strong>You made it to Pages/{name}</strong></p>
      <p>Full address: <span class="url">{DOMAIN}Pages/{name}</span></p>
    </div>
  </div>
{body}
  <a class="back" href="../index.html">← Site map</a>
</main>
</body>
</html>
""")


# ---------- site map (image + index) ----------

def scan(path):
    """Folders first, then files, each alphabetical ignoring case (like the Route 404 trees)."""
    names = [n for n in os.listdir(path) if not n.startswith(".")]
    folders = sorted((n for n in names if os.path.isdir(os.path.join(path, n))), key=str.lower)
    files = sorted((n for n in names if not os.path.isdir(os.path.join(path, n))), key=str.lower)
    return [(n, scan(os.path.join(path, n))) for n in folders] + [(n, None) for n in files]


BADGES = {
    "html": ("#e34c26", "#fff"), "css": ("#663399", "#fff"), "js": ("#f7df1e", "#1a1a1a"),
    "png": ("#0f766e", "#ccfbf1"), "jpg": ("#0f766e", "#ccfbf1"), "gif": ("#0f766e", "#ccfbf1"),
    "webp": ("#0f766e", "#ccfbf1"), "svg": ("#b45309", "#fff"), "pdf": ("#dc2626", "#fff"),
    "txt": ("#475569", "#fff"), "ico": ("#db2777", "#fff"),
}

FOLDER_ICON = ('<svg width="22" height="18" viewBox="0 0 22 18"><path d="M1 3a2 2 0 0 1 2-2h5l2 2.5h9a2 2 0 0 1 2 2V15'
               'a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2z" fill="{c}"/></svg>')

MAP_CSS = """
html, body { margin: 0; background: #070b1a; }
body { width: 760px; box-sizing: border-box; padding: 28px; font-family: Menlo, Consolas, monospace; color: #e6e9f2; }
.panel { background: #131c31; border: 1px solid #2a3550; border-radius: 18px; padding: 22px 26px 26px; }
.head { display: flex; gap: 14px; align-items: center; }
.head img { width: 56px; height: 56px; }
.title { font-size: 25px; font-weight: 700; color: #f8fafc; }
.title span { color: #f59e0b; }
.subtitle { font-size: 14px; color: #9aa4bf; margin-top: 2px; }
.formula { margin: 18px 0 16px; padding: 10px 14px; border: 1px solid #6b4f12; background: #2a2110; border-radius: 10px; color: #fde68a; font-size: 15px; }
.formula b { padding: 1px 6px; border-radius: 4px; color: #0b1024; font-weight: 700; }
.kr { background: #fbbf24; } .kf { background: #5eead4; } .kn { background: #f9a8d4; }
.tree ul { list-style: none; margin: 0 0 0 10px; padding: 0 0 0 20px; border-left: 2px solid #3b4763; }
.tree > ul { margin: 0; padding: 0; border: 0; }
.row { display: flex; align-items: center; gap: 10px; height: 29px; font-size: 16px; white-space: nowrap; }
.chev { width: 12px; color: #94a3b8; font-size: 12px; text-align: center; }
.folder .name { font-weight: 700; color: #f8fafc; }
.file .name { color: #e2e8f0; }
.badge { display: inline-grid; place-items: center; width: 44px; height: 19px; border-radius: 5px; font-size: 10.5px; font-weight: 700; letter-spacing: .04em; flex: none; }
.rootpill { margin-left: 6px; padding: 2px 10px; border-radius: 999px; background: #2a2110; border: 1px solid #f59e0b; color: #fde68a; font-size: 13px; font-weight: 400; }
.example { margin-top: 20px; padding: 14px 16px; border-radius: 12px; background: #0b1024; border: 1px solid #2a3550; }
.label { font-size: 13px; color: #9aa4bf; margin-bottom: 6px; }
.url { font-size: 16px; }
.r { color: #fbbf24; } .f { color: #5eead4; } .n { color: #f9a8d4; }
.rules { margin: 14px 0 0; padding-left: 20px; font-size: 14px; color: #cbd5e1; line-height: 1.6; }
.rules b { color: #fde68a; }
"""


def tree_html(entries):
    rows = []
    for name, kids in entries:
        if kids is None:
            ext = name.rsplit(".", 1)[-1].lower()
            bg, fg = BADGES.get(ext, ("#334155", "#fff"))
            rows.append(f'<li><div class="row file"><span class="chev"></span><span class="badge" '
                        f'style="background:{bg};color:{fg}">{ext.upper()}</span><span class="name">{name}</span></div></li>')
        else:
            rows.append(f'<li><div class="row folder"><span class="chev">▼</span>{FOLDER_ICON.format(c="#fbbf24")}'
                        f'<span class="name">{name}</span></div>{tree_html(kids)}</li>')
    return "<ul>" + "".join(rows) + "</ul>"


def tree_text(entries, prefix=""):
    lines = []
    for i, (name, kids) in enumerate(entries):
        last = i == len(entries) - 1
        lines.append(prefix + ("└── " if last else "├── ") + name + ("/" if kids is not None else ""))
        if kids is not None:
            lines += tree_text(kids, prefix + ("    " if last else "│   "))
    return lines


def build_site_map():
    for name in ("site_map.png", "index.html"):
        open(out(name), "a").close()  # make sure both exist so the map lists them
    entries = scan(SITE)
    with open(out("Assets/Icons/rover.svg")) as f:
        rover_svg = f.read()
    root_row = (f'<div class="row folder"><span class="chev">▼</span>{FOLDER_ICON.format(c="#f59e0b")}'
                f'<span class="name">{ROOT_NAME}/</span><span class="rootpill">= {DOMAIN}</span></div>')
    page = f"""<!doctype html><html><head><meta charset="utf-8"><style>{MAP_CSS}</style></head><body>
<div class="panel">
  <div class="head">{rover_svg.replace('width="128" height="128"', 'width="56" height="56"')}
    <div><div class="title">{ROOT_NAME} <span>Site Map</span></div>
    <div class="subtitle">Every file below has its own address on the web.</div></div></div>
  <div class="formula">Full address = <b class="kr">site root</b> + <b class="kf">folders</b> + <b class="kn">file name</b></div>
  <div class="tree"><ul><li>{root_row}{tree_html(entries)}</li></ul></div>
  <div class="example">
    <div class="label">Example: the rover icon</div>
    <div class="url"><span class="r">{DOMAIN}</span><span class="f">Assets/Icons/</span><span class="n">rover.svg</span></div>
  </div>
  <ul class="rules">
    <li>The site root already means the <b>{ROOT_NAME}</b> folder. Don't type it again.</li>
    <li>Capitals count. Type every name exactly as shown.</li>
  </ul>
</div></body></html>"""
    im = screenshot(page, "site_map", 760, 2400, scale=2).convert("RGB")
    bg = Image.new("RGB", im.size, im.getpixel((2, 2)))
    left, top, right, bottom = ImageChops.difference(im, bg).getbbox()
    pad = 56
    im.crop((0, 0, im.width, min(im.height, bottom + pad))).save(out("site_map.png"), optimize=True)

    alt = (f"Folder map of the {ROOT_NAME} website. The top folder, {ROOT_NAME}, is the site root {DOMAIN}. "
           "A text version is below the picture.")
    text = "\n".join([ROOT_NAME + "/"] + tree_text(entries))
    with open(out("index.html"), "w") as f:
        f.write(f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{ROOT_NAME} · Site Map</title>
<link rel="icon" href="favicon.ico">
<style>
  body {{ margin: 0; background: #070b1a; color: #e6e9f2; font-family: ui-monospace, "SF Mono", Menlo, Consolas, monospace; }}
  main {{ max-width: 760px; margin: 0 auto; padding: 24px 16px 48px; }}
  img {{ display: block; width: 100%; height: auto; }}
  details {{ margin: 16px 28px 0; }}
  summary {{ cursor: pointer; color: #fbbf24; }}
  pre {{ overflow-x: auto; padding: 16px; background: #131c31; border: 1px solid #2a3550; border-radius: 12px; line-height: 1.4; }}
</style>
</head>
<body>
<main>
  <img src="site_map.png" alt="{html.escape(alt)}">
  <details>
    <summary>Text version of the map</summary>
    <pre>{html.escape(text)}</pre>
  </details>
</main>
</body>
</html>
""")


if __name__ == "__main__":
    build_icons()
    build_cat()
    build_planet()
    build_banner()
    build_hero()
    build_team()
    build_dog()
    build_pdf()
    build_pages()
    build_site_map()
    print("done")
