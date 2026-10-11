"""Build self-contained SVG artwork with Space Grotesk and Inter outlines."""
from functools import lru_cache
import hashlib
from html import escape
import json
from pathlib import Path
from urllib.request import urlopen

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ASSETS.mkdir(exist_ok=True)
BG = "#0d141e"
FG = "#f1f4ed"
MUTED = "#a6b9bd"
MINT = "#99e4cb"
VIOLET = "#c2b6f7"
DISPLAY = "Space Grotesk"
FONT = "Inter"
# Small labels share the same body typeface: exactly two font families.
MONO = FONT
FONTS = Path(__file__).resolve().parent / "fonts"


@lru_cache(maxsize=2)
def load_font(family):
    manifest = json.loads((FONTS / "manifest.json").read_text(encoding="utf-8"))
    entry = manifest["families"][family]
    path = FONTS / entry["filename"]
    if not path.exists():
        with urlopen(entry["url"], timeout=60) as response:
            data = response.read()
        if hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError("Downloaded font does not match its pinned SHA-256")
        path.write_bytes(data)
    if hashlib.sha256(path.read_bytes()).hexdigest() != entry["sha256"]:
        raise ValueError("Font does not match its pinned SHA-256")
    return TTFont(path)


@lru_cache(maxsize=16)
def glyph_set(family, weight):
    return load_font(family).getGlyphSet(location={"wght": weight, "opsz": 14})


def text(x, y, value, size=20, color=FG, weight=400, font=None, spacing=None):
    family = font or (DISPLAY if size >= 29 else FONT)
    source_font = load_font(family)
    glyphs = glyph_set(family, weight)
    mapping = source_font.getBestCmap()
    scale = size / source_font["head"].unitsPerEm
    advance = 0
    parts = []
    for character in value:
        name = mapping.get(ord(character))
        if name is None:
            raise ValueError(f"Missing glyph in {family}: {character!r}")
        glyph = glyphs[name]
        pen = SVGPathPen(glyphs, ntos=lambda number: format(number, ".3f"))
        glyph.draw(pen)
        if commands := pen.getCommands():
            parts.append(f'<path transform="translate({x+advance:.3f} {y}) scale({scale:.6f} {-scale:.6f})" d="{commands}"/>')
        advance += glyph.width * scale + (spacing or 0)
    return f'<g fill="{color}" data-typeface="{family}" aria-label="{escape(value, quote=True)}">' + "".join(parts) + "</g>"


def line(x1, y1, x2, y2, color="#253642", width=1, opacity=1):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}" opacity="{opacity}"/>'


def svg(name, width, height, label, body):
    defs = '<defs><linearGradient id="bg" x2="1" y2="1"><stop stop-color="#0d141e"/><stop offset="1" stop-color="#14272b"/></linearGradient><radialGradient id="glow"><stop stop-color="#65b99f" stop-opacity=".17"/><stop offset="1" stop-color="#65b99f" stop-opacity="0"/></radialGradient></defs>'
    credits = '<metadata>Typography: Space Grotesk and Inter, SIL Open Font License 1.1. Sources, pinned hashes and licenses: tools/fonts/. Text is outlined for consistent rendering.</metadata>'
    source = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">{escape(label)}</title>{credits}{defs}{body}</svg>\n'
    (ASSETS / name).write_text(source, encoding="utf-8")


def panel(width, height, radius=24):
    return f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="{radius}" fill="url(#bg)" stroke="#2b3a43"/>'


def pill(x, y, width, label, accent=MINT):
    return f'<rect x="{x}" y="{y}" width="{width}" height="28" rx="14" fill="{accent}" fill-opacity=".09" stroke="{accent}" stroke-opacity=".25"/>' + text(x+13, y+19, label, 12, accent, 600, MONO)


def arrow(x, y, color=MINT):
    return f'<path d="M{x} {y+16}l16-16m-13 0h13v13" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'


def header():
    b = panel(1200, 400)
    b += '<ellipse cx="952" cy="185" rx="340" ry="260" fill="url(#glow)"/>'
    for x in range(716, 1200, 40):
        b += line(x, 24, x, 334, opacity=.35)
    for y in range(54, 334, 40):
        b += line(716, y, 1176, y, opacity=.35)
    b += '<rect x="48" y="40" width="36" height="36" rx="10" fill="#99e4cb"/>'
    b += text(58, 65, "Z", 23, BG, 700, font=DISPLAY)
    b += text(101, 64, "ZOGA228 / ML PORTFOLIO", 14, MUTED, font=MONO, spacing=1)
    b += text(48, 164, "Zangar.", 84, FG, 700, spacing=-3)
    b += text(51, 224, "Building models.", 34, FG, 500, font=DISPLAY)
    b += text(51, 267, "Questioning results.", 34, MINT, 500, font=DISPLAY)
    b += text(52, 307, "Language models · Reliable evaluation · AI prototypes", 18, MUTED)
    # A stylized decoder: a conceptual illustration, not an empirical chart.
    layers = [[(800, y) for y in (135, 185, 235)], [(882, y) for y in (110, 160, 210, 260)], [(964, y) for y in (110, 160, 210, 260)], [(1046, y) for y in (135, 185, 235)]]
    for a, z in zip(layers, layers[1:]):
        for i, (x, y) in enumerate(a):
            for j, (xx, yy) in enumerate(z):
                b += line(x, y, xx, yy, MINT, 1.2, .12 if i != j else .45)
    for k, layer in enumerate(layers):
        for i, (x, y) in enumerate(layer):
            c = VIOLET if k == 2 else MINT
            b += f'<circle cx="{x}" cy="{y}" r="10" fill="#11262b" stroke="{c}" stroke-opacity=".55"/>'
            b += f'<circle cx="{x}" cy="{y}" r="3" fill="{c}"/>'
    b += text(795, 91, "INPUT", 11, MUTED, font=MONO, spacing=2)
    b += text(1012, 91, "OUTPUT", 11, MUTED, font=MONO, spacing=2)
    b += '<rect x="836" y="283" width="222" height="37" rx="9" fill="#0d171f" stroke="#365048"/>'
    b += text(852, 307, "635,776 parameters", 16, MINT, font=MONO)
    b += line(48, 347, 1152, 347)
    b += text(50, 377, "IMPLEMENT  /  MEASURE  /  UNDERSTAND", 13, MUTED, font=MONO, spacing=1)
    b += text(887, 377, "CODE + OPEN WEIGHTS", 13, MINT, font=MONO)
    svg("header.svg", 1200, 400, "Zangar. Building models. Questioning results. Language models, reliable evaluation and AI prototypes.", b)


def model():
    b = panel(1200, 318)
    b += text(36, 43, "01 / LANGUAGE MODELING", 13, MINT, font=MONO, spacing=1)
    b += arrow(1136, 30)
    b += text(36, 96, "Causal LM Lab", 38, FG, 700, spacing=-.7)
    b += text(37, 136, "A byte-level Transformer, trained from scratch.", 21, MUTED)
    b += text(37, 165, "RoPE ablation. Bigram baseline. Causal-mask tests.", 19, MUTED)
    b += pill(36, 192, 108, "PYTORCH") + pill(154, 192, 150, "OPEN WEIGHTS")
    b += text(37, 280, "635,776", 31, MINT, 600)
    b += text(184, 280, "parameters", 17, MUTED)
    b += text(360, 280, "2.487", 31, MINT, 600)
    b += text(458, 280, "test bits/byte", 17, MUTED)
    b += line(651, 36, 651, 282)
    b += text(691, 57, "HELD-OUT TEST · LOWER IS BETTER", 12, MUTED, font=MONO)
    for y, label, value, c in [(106, "Bigram", 3.6243, "#617c81"), (164, "No RoPE", 2.8659, VIOLET), (222, "RoPE", 2.4870, MINT)]:
        b += text(692, y, label, 16, MUTED)
        b += f'<rect x="795" y="{y-17}" width="{value/4*260:.2f}" height="22" rx="4" fill="{c}"/>'
        b += text(1070, y, f"{value:.3f}", 17, c, 600, MONO)
    b += text(693, 279, "Tiny Shakespeare · matched 3,000-step runs · seed 42", 13, MUTED)
    svg("causal-lm.svg", 1200, 318, "Causal LM Lab: 635,776 parameters trained from scratch. Test bits per byte: RoPE 2.487, no RoPE 2.866, bigram 3.624. One seed on Tiny Shakespeare.", b)


def validation():
    b = panel(1200, 318)
    b += text(36, 43, "02 / RELIABLE EVALUATION", 13, VIOLET, font=MONO, spacing=1)
    b += arrow(1136, 30, VIOLET)
    b += text(36, 96, "Validation Stress Lab", 38, FG, 700, spacing=-.7)
    b += text(37, 136, "What survives a better validation protocol?", 21, MUTED)
    b += text(37, 165, "Group leakage. Shortcuts. Calibration. Conformal coverage.", 19, MUTED)
    b += pill(36, 192, 162, "SCIKIT-LEARN", VIOLET) + pill(208, 192, 130, "NOTEBOOKS", VIOLET)
    b += text(37, 280, "4", 31, VIOLET, 600)
    b += text(66, 280, "controlled experiments", 17, MUTED)
    b += text(367, 280, "+ MRI transfer study", 17, MUTED)
    b += line(651, 36, 651, 282)
    b += text(692, 57, "GROUP IDENTITY · SYNTHETIC BENCHMARK", 12, MUTED, font=MONO)
    for y, label, value, c in [(114, "Random split", .922, VIOLET), (186, "Unseen groups", .506, MINT)]:
        b += text(692, y, label, 16, MUTED)
        b += f'<rect x="839" y="{y-17}" width="{value*205:.2f}" height="22" rx="4" fill="{c}"/>'
        b += text(1070, y, f"{value:.3f}", 17, c, 600, MONO)
    b += text(693, 235, "Same model. A different question.", 20, FG, 500)
    b += text(693, 279, "Mean AUC over five seeds · full results in the report", 13, MUTED)
    svg("validation.svg", 1200, 318, "Validation Stress Lab. Four controlled synthetic experiments and an MRI transfer study. Group identity benchmark: mean random-split AUC 0.922 versus unseen-group AUC 0.506 over five seeds.", b)


def project(name, number, title, subtitle, detail, tags, icon):
    b = panel(580, 220, 18)
    b += text(27, 36, f"{number} / AI & PRODUCT PROTOTYPES", 11, MUTED, font=MONO, spacing=.5)
    b += arrow(524, 24)
    b += text(27, 83, title, 29, FG, 600)
    b += text(28, 118, subtitle, 17, MUTED)
    b += text(28, 145, detail, 17, MUTED)
    b += pill(27, 173, 250, tags)
    b += icon
    svg(name, 580, 220, f"{title}. {subtitle} {detail}", b)


def buttons():
    for name, label, width, accent in [("huggingface.svg", "Hugging Face / weights", 258, MINT), ("kaggle.svg", "Kaggle / notebooks", 235, VIOLET), ("repositories.svg", "GitHub / repositories", 251, FG)]:
        b = f'<rect x=".5" y=".5" width="{width-1}" height="43" rx="10" fill="{BG}" stroke="#34454e"/>'
        b += f'<circle cx="18" cy="22" r="3" fill="{accent}"/>'
        b += text(31, 28, label, 15, accent, 500)
        b += arrow(width-27, 14, accent)
        svg(name, width, 44, label, b)


def stack():
    b = panel(1200, 93, 16)
    b += text(28, 31, "WORKING TOOLKIT", 11, MUTED, font=MONO, spacing=1.5)
    x = 28
    for label, width, c in [("Python", 158, MINT), ("PyTorch", 175, VIOLET), ("NumPy", 165, MINT), ("pandas", 165, VIOLET), ("scikit-learn", 231, MINT), ("Jupyter", 175, VIOLET)]:
        b += f'<circle cx="{x+4}" cy="58" r="3" fill="{c}"/>'
        b += text(x+16, 64, label, 19, FG, 500)
        x += width
    svg("toolkit.svg", 1200, 93, "Working toolkit: Python, PyTorch, NumPy, pandas, scikit-learn, Jupyter.", b)


def footer():
    b = '<path d="M0 14H437M763 14H1200" stroke="#3a4d53"/>'
    b += text(464, 19, "BUILD. TEST. LEARN. REPEAT.", 14, MUTED, font=MONO, spacing=1)
    svg("footer.svg", 1200, 30, "Build. Test. Learn. Repeat.", b)


def mobile():
    b = panel(600, 342)
    b += text(28, 40, "ZOGA228 / ML PORTFOLIO", 13, MUTED, font=MONO, spacing=1)
    b += text(26, 122, "Zangar.", 64, FG, 700, spacing=-2)
    b += text(28, 178, "Building models.", 29, FG, 500)
    b += text(28, 218, "Questioning results.", 29, MINT, 500)
    b += text(28, 261, "Language models · Reliable evaluation", 19, MUTED)
    b += line(28, 287, 572, 287)
    b += text(28, 317, "IMPLEMENT / MEASURE / UNDERSTAND", 14, MINT, font=MONO)
    svg("header-mobile.svg", 600, 342, "Zangar. Building models. Questioning results.", b)

    b = panel(600, 300)
    b += text(28, 37, "01 / LANGUAGE MODELING", 13, MINT, font=MONO)
    b += arrow(552, 24)
    b += text(28, 88, "Causal LM Lab", 37, FG, 700)
    b += text(28, 129, "A byte-level Transformer trained from scratch.", 20, MUTED)
    b += text(28, 159, "RoPE ablation · bigram baseline · causal tests", 19, MUTED)
    b += line(28, 187, 572, 187)
    b += text(28, 235, "635,776", 31, MINT, 600)
    b += text(28, 262, "parameters", 18, MUTED)
    b += text(326, 235, "2.487", 31, MINT, 600)
    b += text(326, 262, "test bits/byte · seed 42", 18, MUTED)
    svg("causal-lm-mobile.svg", 600, 300, "Causal LM Lab: 635,776 parameters trained from scratch. Held-out test 2.487 bits/byte on Tiny Shakespeare, seed 42.", b)

    b = panel(600, 300)
    b += text(28, 37, "02 / RELIABLE EVALUATION", 13, VIOLET, font=MONO)
    b += arrow(552, 24, VIOLET)
    b += text(28, 88, "Validation Stress Lab", 34, FG, 700)
    b += text(28, 130, "Four controlled synthetic experiments", 21, MUTED)
    b += text(28, 160, "plus an MRI transfer study.", 21, MUTED)
    b += line(28, 187, 572, 187)
    b += text(28, 235, "0.922", 31, VIOLET, 600)
    b += text(28, 262, "Random-split mean AUC", 18, MUTED)
    b += text(326, 235, "0.506", 31, MINT, 600)
    b += text(326, 262, "Unseen-group mean AUC", 18, MUTED)
    svg("validation-mobile.svg", 600, 300, "Synthetic group identity benchmark, mean AUC over five seeds: random split 0.922, unseen groups 0.506.", b)

    b = panel(600, 139, 16)
    b += text(28, 30, "WORKING TOOLKIT", 12, MUTED, font=MONO, spacing=1)
    for x, y, label in [(28, 68, "Python"), (206, 68, "PyTorch"), (398, 68, "NumPy"), (28, 109, "pandas"), (206, 109, "scikit-learn"), (398, 109, "Jupyter")]:
        b += text(x, y, label, 22, FG, 500)
    svg("toolkit-mobile.svg", 600, 139, "Python, PyTorch, NumPy, pandas, scikit-learn, Jupyter.", b)


if __name__ == "__main__":
    header()
    model()
    validation()
    project("halyk.svg", "03", "Halyk AI Challenge", "Finance calculations with traceable evidence.", "Deterministic arithmetic + optional semantic review.", "PRIVATE CHALLENGE DATA", '<path d="M460 92h64m-64 15h48m-48 15h37" stroke="#99e4cb" stroke-opacity=".3" stroke-width="3"/>')
    project("guardian.svg", "04", "GuardianVoice", "An accessibility and safety interface prototype.", "Voice activation, maps and AI service integration.", "INTERFACE PROTOTYPE", '<path d="M471 96v12a16 16 0 0 0 32 0V96m-16 28v13m-10 0h20" fill="none" stroke="#c2b6f7" stroke-opacity=".4" stroke-width="2"/><rect x="480" y="84" width="14" height="30" rx="7" fill="none" stroke="#c2b6f7" stroke-opacity=".4" stroke-width="2"/>')
    buttons()
    stack()
    footer()
    mobile()
    print(f"Built {len(list(ASSETS.glob('*.svg')))} SVG assets")
