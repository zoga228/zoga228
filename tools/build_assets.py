"""Build self-contained SVG artwork with Space Grotesk and Inter outlines."""
from functools import lru_cache
import hashlib
from html import escape
import json
from pathlib import Path
import re
from urllib.request import urlopen

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.ttLib import TTFont

ASSETS = Path(__file__).resolve().parents[1] / "assets"
ASSETS.mkdir(exist_ok=True)
BG = "#111b20"
FG = "#f5f2e9"
MUTED = "#aab7b6"
MINT = "#75d3b5"
AMBER = "#e8b66c"
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


def outline_diagram_labels(markup):
    pattern = re.compile(r'<text x="([\d.]+)" y="([\d.]+)" fill="([^"]+)" font-family="[^"]+" font-size="([\d.]+)">(.*?)</text>')
    return pattern.sub(lambda match: text(float(match[1]), float(match[2]), match[5], float(match[4]), match[3], 500, FONT), markup)


def line(x1, y1, x2, y2, color="#253642", width=1, opacity=1):
    return f'<path d="M{x1} {y1}L{x2} {y2}" fill="none" stroke="{color}" stroke-width="{width}" opacity="{opacity}"/>'


def svg(name, width, height, label, body):
    credits = '<metadata>Typography: Space Grotesk and Inter, SIL Open Font License 1.1. Sources, pinned hashes and licenses: tools/fonts/. Text is outlined for consistent rendering.</metadata>'
    source = f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title"><title id="title">{escape(label)}</title>{credits}{body}</svg>\n'
    (ASSETS / name).write_text(source, encoding="utf-8")


def panel(width, height, radius=24):
    return f'<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="{radius}" fill="{BG}" stroke="#33464a"/>'


def pill(x, y, width, label, accent=MINT):
    return f'<rect x="{x}" y="{y}" width="{width}" height="28" rx="14" fill="{accent}" fill-opacity=".09" stroke="{accent}" stroke-opacity=".25"/>' + text(x+13, y+19, label, 12, accent, 600, MONO)


def arrow(x, y, color=MINT):
    return f'<path d="M{x} {y+16}l16-16m-13 0h13v13" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'


def header():
    b = panel(1200, 400)
    b += '<rect x="48" y="40" width="36" height="36" rx="10" fill="#75d3b5"/>'
    b += text(58, 65, "Z", 23, BG, 700, font=DISPLAY)
    b += text(101, 64, "ZOGA228 / ML PORTFOLIO", 14, MUTED, font=MONO, spacing=1)
    b += text(48, 164, "Zangar.", 84, FG, 700, spacing=-3)
    b += text(51, 224, "Building models.", 34, FG, 500, font=DISPLAY)
    b += text(51, 267, "Questioning results.", 34, MINT, 500, font=DISPLAY)
    b += text(52, 307, "Language models  /  Reliable evaluation  /  AI prototypes", 16, MUTED)

    # A model-specific flow replaces decorative neural-network imagery.
    b += text(730, 63, "BYTE-LEVEL DECODER  /  ONE TRAINING RUN", 11, MUTED, font=MONO, spacing=.6)
    b += '<rect x="728" y="88" width="84" height="130" rx="12" fill="#18262a" stroke="#3e5853"/>'
    b += text(741, 111, "UTF-8", 11, MINT, 600, MONO)
    for i, token in enumerate(("52", "4F", "4D", "45")):
        x = 738 + i*17
        b += f'<rect x="{x}" y="132" width="15" height="23" rx="3" fill="#23383a"/>'
        b += text(x+2, 147, token, 8, FG, 500, MONO)
    b += text(738, 183, "byte IDs", 10, MUTED)

    b += arrow(817, 145, MINT)
    b += '<rect x="840" y="88" width="91" height="130" rx="12" fill="#18262a" stroke="#3e5853"/>'
    b += text(853, 111, "Embedding", 11, FG, 500)
    b += line(853, 128, 916, 128, MINT, 1, .45)
    b += text(853, 151, "+ RoPE", 12, MINT, 600)
    b += '<path d="M853 176c8-10 14 10 22 0s14 10 22 0 12 8 18 0" fill="none" stroke="#75d3b5" stroke-width="1.6"/>'
    b += text(853, 202, "128 positions", 9, MUTED, font=MONO)

    b += arrow(936, 145, MINT)
    b += '<rect x="959" y="88" width="105" height="130" rx="12" fill="#18262a" stroke="#3e5853"/>'
    b += text(972, 111, "Decoder x3", 12, FG, 600)
    for i, label in enumerate(("Norm", "Attention", "SwiGLU")):
        y = 125 + i*27
        b += f'<rect x="971" y="{y}" width="81" height="21" rx="5" fill="#213438"/>'
        b += text(980, y+15, label, 10, MINT if i == 1 else MUTED, 500)
    b += text(972, 209, "causal mask", 9, MUTED, font=MONO)

    b += arrow(1068, 145, MINT)
    b += '<rect x="1090" y="88" width="84" height="130" rx="12" fill="#18262a" stroke="#3e5853"/>'
    b += text(1101, 111, "Next byte", 10, FG, 500)
    for i, (height, color) in enumerate(((25, "#405c57"), (43, "#537b6d"), (65, AMBER), (36, "#405c57"))):
        x = 1100 + i*16
        b += f'<rect x="{x}" y="{192-height}" width="10" height="{height}" rx="2" fill="{color}"/>'
    b += text(1100, 207, "logits", 9, MUTED, font=MONO)
    b += text(730, 254, "635,776 parameters", 14, MINT, 600)
    b += text(931, 254, "128-byte context", 14, MUTED)
    b += text(730, 291, "RoPE ablation  /  bigram baseline  /  causal-mask tests", 12, MUTED)
    b += line(48, 347, 1152, 347)
    b += text(50, 377, "IMPLEMENT  /  MEASURE  /  UNDERSTAND", 13, MUTED, font=MONO, spacing=1)
    b += text(887, 377, "CODE + OPEN WEIGHTS", 13, MINT, font=MONO)
    svg("header.svg", 1200, 400, "Byte-level Transformer project: UTF-8 byte IDs pass through embeddings with RoPE, three causal decoder blocks and next-byte logits. 635,776 parameters and a 128-byte context.", b)


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
    b += text(691, 57, "HELD-OUT TEST  /  LOWER IS BETTER", 12, MUTED, font=MONO)
    for tick, x in zip((0, 1, 2, 3, 4), (795, 860, 925, 990, 1055)):
        b += line(x, 76, x, 246, "#344448", .8, .8)
        b += text(x-3, 265, str(tick), 10, MUTED, font=MONO)
    for y, label, value, c in [(106, "Bigram", 3.6243, "#617c81"), (164, "No RoPE", 2.8659, AMBER), (222, "RoPE", 2.4870, MINT)]:
        b += text(692, y, label, 16, MUTED)
        b += f'<rect x="795" y="{y-17}" width="{value/4*260:.2f}" height="22" rx="4" fill="{c}"/>'
        b += text(1070, y, f"{value:.3f}", 17, c, 600, MONO)
    b += text(693, 295, "Tiny Shakespeare  /  matched 3,000-step runs  /  seed 42", 12, MUTED)
    svg("causal-lm.svg", 1200, 318, "Causal LM Lab: 635,776 parameters trained from scratch. Test bits per byte: RoPE 2.487, no RoPE 2.866, bigram 3.624. One seed on Tiny Shakespeare.", b)


def validation():
    b = panel(1200, 318)
    b += text(36, 43, "02 / RELIABLE EVALUATION", 13, AMBER, font=MONO, spacing=1)
    b += arrow(1136, 30, AMBER)
    b += text(36, 96, "Validation Stress Lab", 38, FG, 700, spacing=-.7)
    b += text(37, 136, "What survives a better validation protocol?", 21, MUTED)
    b += text(37, 165, "Group leakage. Shortcuts. Calibration. Conformal coverage.", 19, MUTED)
    b += pill(36, 192, 162, "SCIKIT-LEARN", AMBER) + pill(208, 192, 130, "NOTEBOOKS", AMBER)
    b += text(37, 280, "4", 31, AMBER, 600)
    b += text(66, 280, "controlled experiments", 17, MUTED)
    b += text(367, 280, "+ MRI transfer study", 17, MUTED)
    b += line(651, 36, 651, 282)
    b += text(692, 57, "GROUP IDENTITY  /  SYNTHETIC BENCHMARK", 12, MUTED, font=MONO)
    for tick, x in zip((0, .5, 1), (839, 941, 1044)):
        b += line(x, 87, x, 205, "#344448", .8, .8)
        b += text(x-5, 223, f"{tick:.1f}", 10, MUTED, font=MONO)
    for y, label, value, c in [(114, "Random split", .922, AMBER), (186, "Unseen groups", .506, MINT)]:
        b += text(692, y, label, 16, MUTED)
        b += f'<rect x="839" y="{y-17}" width="{value*205:.2f}" height="22" rx="4" fill="{c}"/>'
        b += text(1070, y, f"{value:.3f}", 17, c, 600, MONO)
    b += text(693, 235, "Same model. A different question.", 20, FG, 500)
    b += text(693, 279, "Mean AUC over five seeds  /  full results in the report", 13, MUTED)
    svg("validation.svg", 1200, 318, "Validation Stress Lab. Four controlled synthetic experiments and an MRI transfer study. Group identity benchmark: mean random-split AUC 0.922 versus unseen-group AUC 0.506 over five seeds.", b)


def project(name, number, title, subtitle, detail, tags, icon):
    b = panel(1200, 224, 20)
    b += text(32, 37, f"{number} / ENGINEERING PROJECT", 12, MUTED, font=MONO, spacing=.8)
    b += arrow(1136, 23, AMBER)
    b += text(32, 91, title, 34, FG, 600)
    b += text(33, 126, subtitle, 18, MUTED)
    b += text(33, 154, detail, 16, MUTED)
    b += pill(32, 174, 250, tags, AMBER)
    b += line(640, 30, 640, 194, "#33464a")
    b += outline_diagram_labels(icon)
    svg(name, 1200, 224, f"{title}. {subtitle} {detail}", b)


def samuraidoku():
    b = '<rect x=".5" y=".5" width="1199" height="239" rx="20" fill="#f1e7d4" stroke="#c5b99f"/>'
    ink, coral, gold = "#26374a", "#bf6554", "#bd9455"
    b += text(32, 37, "05 / SOFTWARE ENGINEERING", 12, "#65706f", font=MONO, spacing=.8)
    b += arrow(1136, 23, coral)
    b += text(32, 91, "Samuraidoku", 36, ink, 700)
    b += text(33, 126, "A full-stack Sudoku product prototype.", 19, "#56636a")
    b += text(33, 157, "Puzzle generator + solver  /  guided technique practice  /  room-code duels", 15, "#56636a")
    b += f'<rect x="32" y="178" width="112" height="27" rx="13.5" fill="{ink}"/><rect x="151" y="178" width="132" height="27" rx="13.5" fill="{ink}"/><rect x="292" y="178" width="116" height="27" rx="13.5" fill="{ink}"/>'
    b += text(45, 196, "NEXT.JS 14", 11, "#f1e7d4", 600, MONO)
    b += text(164, 196, "TYPESCRIPT", 11, "#f1e7d4", 600, MONO)
    b += text(305, 196, "SUPABASE", 11, "#f1e7d4", 600, MONO)
    # A real 9x9 board with restrained 3x3 separators, givens and one active cell.
    x0, y0, size, cell = 776, 35, 180, 20
    b += f'<rect x="{x0}" y="{y0}" width="{size}" height="{size}" fill="#fbf7ef" stroke="{ink}" stroke-width="1.5"/>'
    digits = (("5", "", "", "6", "", "", "", "9", ""), ("", "7", "", "", "9", "5", "", "", "8"), ("", "", "8", "", "", "", "", "6", ""), ("8", "", "", "", "6", "", "", "", "3"), ("4", "", "6", "8", "", "3", "7", "", "1"), ("7", "", "", "", "2", "", "", "", "6"), ("", "6", "", "", "", "", "2", "", ""), ("2", "", "", "4", "1", "", "", "3", ""), ("", "4", "", "", "", "9", "", "", "5"))
    for i in range(1, 9):
        w = 1.7 if i % 3 == 0 else .55
        c = ink if i % 3 == 0 else "#c9c1b3"
        b += line(x0+i*cell, y0, x0+i*cell, y0+size, c, w)
        b += line(x0, y0+i*cell, x0+size, y0+i*cell, c, w)
    b += f'<rect x="{x0+4*cell}" y="{y0+2*cell}" width="{cell}" height="{cell}" fill="{coral}" fill-opacity=".17"/>'
    for r, row in enumerate(digits):
        for c, value in enumerate(row):
            if value:
                b += text(x0+c*cell+6, y0+r*cell+15, value, 11, ink, 600, MONO)
    b += f'<rect x="{x0+4*cell}" y="{y0+2*cell}" width="{cell}" height="{cell}" fill="none" stroke="{coral}" stroke-width="1.5"/>'
    b += text(982, 64, "9 × 9", 15, ink, 600, MONO)
    b += text(982, 91, "Generate", 13, "#56636a")
    b += text(982, 112, "Solve", 13, "#56636a")
    b += text(982, 133, "Practice", 13, "#56636a")
    b += f'<circle cx="989" cy="157" r="4" fill="{gold}"/>'
    b += text(1001, 162, "Learn by solving", 12, "#56636a")
    svg("samuraidoku.svg", 1200, 240, "Samuraidoku, a Next.js 14 and TypeScript full-stack Sudoku product prototype with a puzzle generator, solver, guided technique practice and room-code duels.", b)


def buttons():
    for name, label, width, accent in [("huggingface.svg", "Hugging Face / weights", 258, MINT), ("kaggle.svg", "Kaggle / notebooks", 235, AMBER), ("linkedin.svg", "LinkedIn / connect", 204, MINT), ("repositories.svg", "GitHub / repositories", 251, FG)]:
        b = f'<rect x=".5" y=".5" width="{width-1}" height="43" rx="10" fill="{BG}" stroke="#34454e"/>'
        b += f'<circle cx="18" cy="22" r="3" fill="{accent}"/>'
        b += text(31, 28, label, 15, accent, 500)
        b += arrow(width-27, 14, accent)
        svg(name, width, 44, label, b)


def stack():
    b = panel(1200, 93, 16)
    b += text(28, 31, "WORKING TOOLKIT", 11, MUTED, font=MONO, spacing=1.5)
    x = 28
    for label, width, c in [("Python", 158, MINT), ("PyTorch", 175, AMBER), ("NumPy", 165, MINT), ("pandas", 165, AMBER), ("scikit-learn", 231, MINT), ("Jupyter", 175, AMBER)]:
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
    b += text(28, 261, "Language models  /  Reliable evaluation", 19, MUTED)
    b += line(28, 287, 572, 287)
    b += text(28, 317, "IMPLEMENT / MEASURE / UNDERSTAND", 14, MINT, font=MONO)
    svg("header-mobile.svg", 600, 342, "Zangar. Building models. Questioning results.", b)

    b = panel(600, 300)
    b += text(28, 37, "01 / LANGUAGE MODELING", 13, MINT, font=MONO)
    b += arrow(552, 24)
    b += text(28, 88, "Causal LM Lab", 37, FG, 700)
    b += text(28, 129, "A byte-level Transformer trained from scratch.", 20, MUTED)
    b += text(28, 159, "RoPE ablation  /  bigram baseline  /  causal tests", 19, MUTED)
    b += line(28, 187, 572, 187)
    b += text(28, 235, "635,776", 31, MINT, 600)
    b += text(28, 262, "parameters", 18, MUTED)
    b += text(326, 235, "2.487", 31, MINT, 600)
    b += text(326, 262, "test bits/byte  /  seed 42", 18, MUTED)
    svg("causal-lm-mobile.svg", 600, 300, "Causal LM Lab: 635,776 parameters trained from scratch. Held-out test 2.487 bits/byte on Tiny Shakespeare, seed 42.", b)

    b = panel(600, 300)
    b += text(28, 37, "02 / RELIABLE EVALUATION", 13, AMBER, font=MONO)
    b += arrow(552, 24, AMBER)
    b += text(28, 88, "Validation Stress Lab", 34, FG, 700)
    b += text(28, 130, "Four controlled synthetic experiments", 21, MUTED)
    b += text(28, 160, "plus an MRI transfer study.", 21, MUTED)
    b += line(28, 187, 572, 187)
    b += text(28, 235, "0.922", 31, AMBER, 600)
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
    project("halyk.svg", "03", "Halyk AI Challenge", "Covenant review grounded in contract text and ledger evidence.", "French Macaronies  /  official rank 16  /  score 89.3358.", "DECIMAL + GPT-5.6-TERRA", '<rect x="672" y="59" width="112" height="112" rx="8" fill="#18262a" stroke="#53645e"/><path d="M694 85h64m-64 13h48m-48 13h56m-56 13h36" stroke="#aab7b6" stroke-width="2"/><text x="694" y="155" fill="#75d3b5" font-family="monospace" font-size="10">CLAUSE 04</text><path d="M793 115h35" stroke="#e8b66c" stroke-width="2"/><path d="M820 108l8 7-8 7" fill="none" stroke="#e8b66c" stroke-width="2"/><rect x="842" y="67" width="132" height="96" rx="8" fill="#18262a" stroke="#53645e"/><text x="856" y="89" fill="#aab7b6" font-family="sans-serif" font-size="10">LEDGER CHECK</text><path d="M856 101h104m-104 15h72m-72 15h91" stroke="#75d3b5" stroke-width="2"/><path d="M988 115h35" stroke="#e8b66c" stroke-width="2"/><path d="M1015 108l8 7-8 7" fill="none" stroke="#e8b66c" stroke-width="2"/><rect x="1038" y="77" width="126" height="76" rx="10" fill="#1b302e" stroke="#75d3b5"/><text x="1052" y="105" fill="#75d3b5" font-family="sans-serif" font-size="11">DECISION</text><path d="M1053 121h92" stroke="#75d3b5" stroke-width="2"/><text x="1052" y="141" fill="#f5f2e9" font-family="monospace" font-size="10">TRACE + VALUE</text><text x="675" y="198" fill="#aab7b6" font-family="sans-serif" font-size="10">DOCS</text><text x="878" y="198" fill="#aab7b6" font-family="sans-serif" font-size="10">CALCULATION</text><text x="1060" y="198" fill="#aab7b6" font-family="sans-serif" font-size="10">AUDIT TRAIL</text>')
    project("guardian.svg", "04", "GuardianVoice", "Accessibility and safety interface prototype.", "Voice-first flows  /  location map  /  camera and AI service integrations.", "PROTOTYPE · NOT FIELD-VALIDATED", '<rect x="684" y="55" width="72" height="112" rx="12" fill="#18262a" stroke="#53645e"/><rect x="710" y="67" width="20" height="38" rx="10" fill="none" stroke="#75d3b5" stroke-width="2"/><path d="M701 94v7a19 19 0 0 0 38 0v-7m-19 27v13m-10 0h20" fill="none" stroke="#75d3b5" stroke-width="2"/><path d="M765 111h34m-7-7 7 7-7 7" fill="none" stroke="#e8b66c" stroke-width="2"/><rect x="812" y="55" width="152" height="112" rx="10" fill="#18262a" stroke="#53645e"/><path d="M826 140l30-43 24 23 19-29 50 49" fill="#243e3a" stroke="#75d3b5" stroke-width="2"/><path d="M860 106c-7 0-12 5-12 12 0 10 12 22 12 22s12-12 12-22c0-7-5-12-12-12z" fill="#e8b66c"/><circle cx="860" cy="118" r="3" fill="#111b20"/><path d="M977 111h34m-7-7 7 7-7 7" fill="none" stroke="#e8b66c" stroke-width="2"/><rect x="1024" y="72" width="132" height="76" rx="10" fill="#1b302e" stroke="#75d3b5"/><text x="1040" y="102" fill="#75d3b5" font-family="sans-serif" font-size="11">USER CONTROL</text><text x="1040" y="124" fill="#f5f2e9" font-family="sans-serif" font-size="10">VOICE · MAP · CAMERA</text><text x="697" y="193" fill="#aab7b6" font-family="sans-serif" font-size="10">VOICE</text><text x="860" y="193" fill="#aab7b6" font-family="sans-serif" font-size="10">LOCATION CONTEXT</text><text x="1052" y="193" fill="#aab7b6" font-family="sans-serif" font-size="10">INTERFACE</text>')
    samuraidoku()
    buttons()
    stack()
    footer()
    mobile()
    print(f"Built {len(list(ASSETS.glob('*.svg')))} SVG assets")
