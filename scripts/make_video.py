"""Build the 2-3 minute narrated demo video for CleanRoute Astana."""

import asyncio
import math
import os
import subprocess
import wave

import edge_tts
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
DEMO = os.path.join(ROOT, "demo")
VOICE_DIR = os.path.join(DEMO, "voice")
PREVIEW_DIR = os.path.join(DEMO, "preview")
OUT = os.path.join(DEMO, "demo_video.mp4")

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 15
W, H = 1280, 720
VOICE = "en-US-AndrewNeural"
RATE = "+6%"

BG = (20, 42, 74)
PANEL = (30, 56, 92)
PANEL_DARK = (24, 47, 79)
BORDER = (50, 82, 120)
WHITE = (246, 249, 252)
TEXT = (222, 232, 244)
MUTED = (160, 180, 203)
GOLD = (242, 169, 59)
TEAL = (63, 193, 176)
RED = (224, 90, 79)
GREEN = (95, 191, 119)
TERM_BG = (9, 17, 29)
TERM_TEXT = (201, 216, 234)

FONT_DIR = "C:/Windows/Fonts/"
def font(size, kind="regular"):
    names = {
        "regular": "segoeui.ttf",
        "bold": "segoeuib.ttf",
        "semi": "seguisb.ttf",
        "light": "segoeuil.ttf",
        "mono": "consola.ttf",
        "mono_bold": "consolab.ttf",
    }
    return ImageFont.truetype(FONT_DIR + names[kind], size)


def wrap(draw, text, fnt, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split()
        if not words:
            lines.append("")
            continue
        line = words[0]
        for word in words[1:]:
            probe = line + " " + word
            if draw.textlength(probe, font=fnt) <= max_width:
                line = probe
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


def draw_lines(draw, xy, lines, fnt, fill, line_height):
    x, y = xy
    for line in lines:
        draw.text((x, y), line, font=fnt, fill=fill)
        y += line_height
    return y


def panel(draw, box, fill=PANEL, outline=BORDER, radius=14, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def kicker(draw, text):
    draw.text((72, 50), text, font=font(15, "semi"), fill=GOLD)


def heading(draw, text, max_width=1140, size=40):
    fnt = font(size, "semi")
    lines = wrap(draw, text, fnt, max_width)
    draw_lines(draw, (72, 80), lines, fnt, WHITE, int(size * 1.22))
    return 80 + int(size * 1.22) * len(lines)


def footer(draw, page):
    draw.text((72, 690), "CleanRoute Astana  ·  AI Fundamentals — Final Project",
              font=font(12), fill=(130, 152, 178))
    label = f"{page} / 9"
    tw = draw.textlength(label, font=font(12))
    draw.text((1208 - tw, 690), label, font=font(12), fill=(130, 152, 178))


def map_plot():
    im = Image.open(os.path.join(ASSETS, "fig_map.png")).convert("RGB")
    return im.crop((60, 65, 1170, 1145))


def figure_card(draw, box, path, caption=None):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    draw.rounded_rectangle(box, radius=14, fill=(247, 250, 253), outline=BORDER, width=2)
    pad = 18
    cap_h = 26 if caption else 0
    im = path.copy() if isinstance(path, Image.Image) else Image.open(path).convert("RGB")
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.thumbnail((w - 2 * pad, h - 2 * pad - cap_h), Image.LANCZOS)
    return im, (x0 + (w - im.width) // 2, y0 + pad + (h - 2 * pad - cap_h - im.height) // 2)


def paste_figure(canvas, box, path, caption=None):
    draw = ImageDraw.Draw(canvas)
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    im, pos = figure_card(draw, box, path, caption)
    canvas.paste(im, pos)
    if caption:
        cf = font(13)
        tw = draw.textlength(caption, font=cf)
        draw.text((x0 + (w - tw) // 2, y1 - 30), caption, font=cf, fill=(70, 88, 109))


def stat_card(draw, box, label, value, sub=None, accent=WHITE, value_size=36):
    x0, y0, x1, y1 = box
    w = x1 - x0
    panel(draw, box)
    draw.text((x0 + 22, y0 + 14), label, font=font(12, "semi"), fill=MUTED)
    draw.text((x0 + 22, y0 + 32), value, font=font(value_size, "semi"), fill=accent)
    if sub:
        fnt = font(14)
        lines = wrap(draw, sub, fnt, w - 44)
        draw_lines(draw, (x0 + 22, y0 + 32 + value_size + 12), lines, fnt, MUTED, 19)


def title_slide():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    panel(draw, (688, 48, 1248, 672), fill=(247, 250, 253), outline=BORDER, width=2, radius=16)
    im = map_plot()
    im.thumbnail((532, 560), Image.LANCZOS)
    canvas.paste(im, (688 + (560 - im.width) // 2, 64 + (560 - im.height) // 2))
    caption = "6×6 toy map  ·  weights 1–5  ·  one fenced depot"
    cf = font(13)
    draw.text((688 + (560 - draw.textlength(caption, font=cf)) // 2, 640),
              caption, font=cf, fill=(70, 88, 109))

    draw.text((72, 64), "QAIRU UNIVERSITY  ·  AI FUNDAMENTALS", font=font(15, "semi"), fill=GOLD)
    draw.text((72, 132), "CleanRoute", font=font(76, "semi"), fill=WHITE)
    draw.text((72, 216), "Astana", font=font(76, "semi"), fill=WHITE)
    sub = "A mini air-quality adviser that decides when to leave and which way to walk."
    draw_lines(draw, (72, 342), wrap(draw, sub, font(22), 500), font(22), TEXT, 32)

    chips = ["Bayes", "A* search", "MDP", "HMM"]
    x = 72
    for label in chips:
        fnt = font(16, "semi")
        tw = draw.textlength(label, font=fnt)
        draw.rounded_rectangle((x, 462, x + tw + 36, 500), radius=10, fill=PANEL, outline=BORDER, width=1)
        draw.text((x + 18, 481), label, font=fnt, fill=(206, 220, 237), anchor="lm")
        x += tw + 46

    draw.text((72, 588), "Ibragim Mukash", font=font(18, "semi"), fill=WHITE)
    draw.text((72, 616), "Final Project  ·  23 November 2026  ·  Qairu University",
              font=font(14), fill=MUTED)
    return canvas


def problem_slide():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    kicker(draw, "THE PROBLEM")
    heading(draw, "Two questions on a winter evening")
    body = ("In the coal-heating season a temperature inversion traps particulates. "
            "Air quality changes hour to hour and block to block — a single AQI number is not enough.")
    draw_lines(draw, (72, 172), wrap(draw, body, font(20), 540), font(20), MUTED, 30)

    for i, (q, sub) in enumerate([("Leave now — or wait?", "the decision problem"),
                                   ("Which way to walk?", "the routing problem")]):
        y = 292 + i * 112
        panel(draw, (72, y, 72 + 540, y + 96))
        draw.text((98, y + 28), q, font=font(27, "semi"), fill=WHITE)
        draw.text((98, y + 64), sub, font=font(14), fill=MUTED)

    stat_card(draw, (680, 158, 1208, 298), "PRIOR BEFORE ANY READING", "30%",
              "hazardous air, P(H) = 3/10", GOLD, 46)
    stat_card(draw, (680, 314, 1208, 454), "CHEAP SENSOR", "85% / 20%",
              "alarm hit rate / false-alarm rate", WHITE, 40)
    stat_card(draw, (680, 470, 1208, 610), "TOY MAP", "6 × 6",
              "blocks, pollution weights 1–5, one fenced depot", TEAL, 46)

    draw.text((72, 620), "Every input is small, hypothetical and declared — no dataset, no trained model.",
              font=font(16), fill=TEXT)
    footer(draw, 2)
    return canvas


def bayes_slide():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    kicker(draw, "STEP 1  ·  BAYESIAN INFERENCE")
    heading(draw, "A noisy alarm becomes a belief")

    panel(draw, (72, 158, 612, 318))
    draw.text((96, 176), "P(H | e) = P(e | H) · P(H) / P(e)", font=font(20, "mono_bold"), fill=WHITE)
    draw.text((96, 216), "P(alarm | H) = 17/20 = 0.85", font=font(16, "mono"), fill=MUTED)
    draw.text((96, 244), "P(alarm | A) = 1/5 = 0.20", font=font(16, "mono"), fill=MUTED)
    draw.text((96, 272), "prior P(H) = 3/10 = 0.30", font=font(16, "mono"), fill=MUTED)

    panel(draw, (72, 342, 612, 648))
    draw.text((96, 362), "Belief P(H) after one reading", font=font(15, "semi"), fill=MUTED)
    rows = [("prior", 30.0, (159, 176, 200), "30.0%"),
            ("after alarm", 64.6, GOLD, "64.6%"),
            ("after calm", 7.4, TEAL, "7.4%")]
    for i, (label, value, color, text) in enumerate(rows):
        y = 408 + i * 72
        draw.text((96, y), label, font=font(16), fill=TEXT, anchor="lm")
        track_x, track_w = 236, 280
        draw.rounded_rectangle((track_x, y - 12, track_x + track_w, y + 12), radius=8, fill=(38, 68, 106))
        bar_w = max(10, int(track_w * value / 100))
        draw.rounded_rectangle((track_x, y - 12, track_x + bar_w, y + 12), radius=8, fill=color)
        draw.text((track_x + track_w + 14, y), text, font=font(19, "semi"), fill=color, anchor="lm")

    stat_card(draw, (648, 158, 1208, 328), "AFTER 'ALARM'", "64.6%",
              "P(H) = 51/79 — the alarm makes hazardous air twice as likely", GOLD, 54)
    stat_card(draw, (648, 346, 1208, 516), "AFTER 'CALM'", "7.4%",
              "P(H) = 9/121 — the same model, the opposite direction", TEAL, 54)

    panel(draw, (648, 534, 1208, 648))
    draw.text((672, 552), "LIKELIHOOD RATIO  × 4.25", font=font(20, "semi"), fill=WHITE)
    note = ("One reading is worth more than four-to-one evidence, so Bayes updates the prior "
            "instead of trusting the raw alarm.")
    draw_lines(draw, (672, 586), wrap(draw, note, font(14), 500), font(14), MUTED, 20)
    footer(draw, 3)
    return canvas


def search_slide():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    kicker(draw, "STEP 2  ·  SEARCH — BFS / UCS / A*")
    heading(draw, "The shortest way is not the cleanest")

    paste_figure(canvas, (72, 158, 632, 648), map_plot(),
                 "red = BFS, 8 steps  ·  green = A*, 12 steps")

    draw.text((668, 158), "algorithm", font=font(12, "semi"), fill=MUTED)
    for x, label in [(838, "steps"), (938, "dose"), (1032, "nodes")]:
        draw.text((x, 158), label, font=font(12, "semi"), fill=MUTED)
    rows = [("BFS", "fewest steps", "8", "19", "27", False),
            ("UCS", "Dijkstra", "12", "14", "21", False),
            ("A*", "optimal + heuristic", "12", "14", "16", True)]
    for i, (name, sub, steps, dose, nodes, hi) in enumerate(rows):
        y = 182 + i * 94
        box = (668, y, 1208, y + 86)
        panel(draw, box, fill=PANEL if not hi else (30, 66, 96),
              outline=TEAL if hi else BORDER, width=3 if hi else 2)
        draw.text((690, y + 22), name, font=font(24, "semi"), fill=WHITE)
        draw.text((690, y + 54), sub, font=font(13), fill=TEAL if hi else MUTED)
        for x, value in [(838, steps), (938, dose), (1032, nodes)]:
            draw.text((x, y + 30), value, font=font(24, "semi"), fill=WHITE)

    draw.text((668, 476), "−26.3%", font=font(44, "semi"), fill=TEAL)
    draw.text((668, 528), "inhaled dose vs the shortest route", font=font(15), fill=MUTED)
    draw.text((938, 476), "+4", font=font(44, "semi"), fill=GOLD)
    draw.text((938, 528), "extra steps for that cleaner air", font=font(15), fill=MUTED)
    note = ("A* keeps the UCS optimum, expands 16 nodes instead of 21, "
            "and proves optimality with an admissible Manhattan heuristic.")
    draw_lines(draw, (668, 576), wrap(draw, note, font(15), 540), font(15), TEXT, 21)
    footer(draw, 4)
    return canvas


def mdp_slide():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    kicker(draw, "STEP 3  ·  MARKOV DECISION PROCESS")
    heading(draw, "Belief and dose choose the action")

    paste_figure(canvas, (56, 158, 744, 640), os.path.join(ASSETS, "fig_decision_threshold.png"),
                 "expected reward of Go and Wait vs P(H)  ·  crossings = p*")

    panel(draw, (824, 158, 1208, 292))
    draw.text((846, 172), "ONE-STEP REWARD", font=font(12, "semi"), fill=MUTED)
    draw.text((846, 196), "R(s,Go) = 12 − 0.02·C(s)·W", font=font(16, "mono_bold"), fill=WHITE)
    draw.text((846, 226), "R(s,Wait) = −4 (A), −6 (H)", font=font(15, "mono"), fill=MUTED)
    draw.text((846, 256), "C(A) = 15,  C(H) = 75", font=font(15, "mono"), fill=MUTED)

    stat_card(draw, (824, 306, 1208, 424), "SHORT ROUTE  ·  W = 19", "p* = 49.5%",
              "at P(H) = 64.6%  →  Wait", GOLD, 34)
    stat_card(draw, (824, 438, 1208, 556), "CLEAN ROUTE  ·  W = 14", "p* = 79.7%",
              "at P(H) = 64.6%  →  Go", TEAL, 34)

    panel(draw, (824, 570, 1208, 640))
    draw.text((846, 580), "VALUE ITERATION  ·  V(A) +6.30 → +7.80",
              font=font(15, "semi"), fill=WHITE)
    draw.text((846, 606), "same policy  ·  35 iterations  ·  γ = 0.9",
              font=font(14), fill=MUTED)
    footer(draw, 5)
    return canvas


def hmm_slide():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    kicker(draw, "STEP 4  ·  HMM / VITERBI / FORWARD")
    heading(draw, "A sequence sharpens the belief")

    paste_figure(canvas, (56, 158, 744, 640), os.path.join(ASSETS, "fig_belief_evolution.png"),
                 "filtered P(H) after the prior and each reading  ·  thresholds marked")

    panel(draw, (824, 158, 1208, 292))
    draw.text((846, 172), "THREE HOURLY READINGS", font=font(12, "semi"), fill=MUTED)
    x = 846
    for i, label in enumerate(["alarm", "alarm", "calm"]):
        fnt = font(16, "semi")
        tw = draw.textlength(label, font=fnt)
        draw.rounded_rectangle((x, 204, x + tw + 28, 244), radius=9,
                               fill=PANEL_DARK, outline=BORDER, width=1)
        draw.text((x + 14, 224), label, font=fnt, fill=WHITE, anchor="lm")
        x += tw + 28
        if i < 2:
            draw.text((x + 8, 224), "→", font=font(18), fill=GOLD, anchor="lm")
            x += 34

    stat_card(draw, (824, 306, 1208, 414), "VITERBI  ·  MOST LIKELY HIDDEN STATES", "H · H · A",
              "two hazardous hours, then acceptable", WHITE, 36)
    stat_card(draw, (824, 428, 1208, 560), "FORWARD FILTERING  ·  P(H)", "64.6 → 80.6 → 18.1%",
              "after 1, 2 and 3 readings", TEAL, 26)

    note = "The third, calm reading drops the belief below both decision thresholds."
    draw_lines(draw, (824, 584), wrap(draw, note, font(17, "semi"), 384), font(17, "semi"), GOLD, 24)
    footer(draw, 6)
    return canvas


def final_slide():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    kicker(draw, "THE INTEGRATED ANSWER")
    heading(draw, "Leave now — and take the park belt")

    panel(draw, (72, 158, 1208, 398), fill=(26, 58, 90), outline=TEAL, width=3)
    draw.text((104, 182), "GO", font=font(62, "semi"), fill=GOLD)
    draw.text((238, 200), "leave now, walk for one hour", font=font(34, "semi"), fill=WHITE)
    draw.text((104, 268), "12-step route through the park belt  ·  the cleanest way to the goal",
              font=font(20), fill=TEXT)
    draw.text((104, 318), "dose 14  ·  −26.3% vs the shortest route", font=font(17), fill=TEAL)
    draw.text((520, 318), "P(H) = 18.1%  <  p* = 79.7%", font=font(17), fill=WHITE)
    draw.text((880, 318), "margin +9.115", font=font(17), fill=GOLD)

    items = [
        ("1  ·  BAYES", "P(H) = 64.6%", "after the alarm"),
        ("2  ·  SEARCH", "W = 14", "A* route, 12 steps"),
        ("3  ·  MDP", "Go", "64.6% < 79.7%"),
        ("4  ·  HMM", "P(H) = 18.1%", "after three readings"),
    ]
    x = 72
    for i, (label, value, sub) in enumerate(items):
        panel(draw, (x, 440, x + 250, 590))
        draw.text((x + 20, 456), label, font=font(12, "semi"), fill=GOLD)
        draw.text((x + 20, 484), value, font=font(25, "semi"), fill=WHITE)
        draw.text((x + 20, 526), sub, font=font(14), fill=MUTED)
        if i < 3:
            ax = x + 266
            draw.polygon([(ax, 504), (ax + 14, 514), (ax, 524)], fill=TEAL)
        x += 295

    draw.text((72, 620), "One directed pipeline: the reading feeds Bayes, the map feeds A*, both feed the MDP,",
              font=font(16), fill=TEXT)
    draw.text((72, 644), "and the sequence updates the belief — every number is printed by the code and pinned by tests.",
              font=font(16), fill=TEXT)
    footer(draw, 7)
    return canvas


TERMINAL_LINES = [
    ("$ python -m airoute", "prompt"),
    ("", "normal"),
    ("PART 1  ·  BAYESIAN INFERENCE", "section"),
    ("  prior P(H) = 3/10 = 30.0%", "normal"),
    ("  P(alarm|H) = 85%   P(alarm|A) = 20%", "normal"),
    ("OUTPUT  alarm: P(H) = 51/79 = 64.6%", "output"),
    ("OUTPUT  calm : P(H) = 9/121 = 7.4%", "output"),
    ("", "normal"),
    ("PART 2  ·  BFS / UCS / A*", "section"),
    ("  BFS      8 steps   dose 19   27 nodes", "normal"),
    ("  UCS     12 steps   dose 14   21 nodes", "normal"),
    ("  A*      12 steps   dose 14   16 nodes", "normal"),
    ("OUTPUT  dose -26.3% for +4 steps", "output"),
    ("", "normal"),
    ("PART 3  ·  MARKOV DECISION PROCESS", "section"),
    ("  W=19   p* = 103/208 = 49.5%  -> Wait", "normal"),
    ("  W=14   p* =  59/74  = 79.7%  -> Go", "normal"),
    ("  value iteration V(A)=+7.80  V(H)=-6.94  35 it", "normal"),
    ("", "normal"),
    ("PART 4  ·  HMM / VITERBI / FORWARD", "section"),
    ("  readings ['alarm', 'alarm', 'calm']", "normal"),
    ("  Viterbi -> ['H', 'H', 'A']", "normal"),
    ("  forward P(H): 64.6% -> 80.6% -> 18.1%", "normal"),
    ("", "normal"),
    ("FINAL RECOMMENDATION", "section"),
    ("  Go now, 12-step route through the park belt", "output"),
    ("  P(H) = 18.1% < p* = 79.7%", "output"),
    ("  margin Q(Go) - Q(Wait) = +9.115", "output"),
    ("", "normal"),
    ("$ python -m pytest tests -q", "prompt"),
    ("..........................  [100%]", "normal"),
    ("26 passed in 0.06s", "pass"),
]

TERM_BOX = (56, 158, 780, 648)
TERM_TEXT_X = 78
TERM_TEXT_Y = 210
TERM_LINE_H = 21
TERM_MAX_LINES = 20


def terminal_base():
    canvas = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(canvas)
    kicker(draw, "TESTED AND REPRODUCIBLE")
    heading(draw, "One command, 26 exact checks")

    draw.rounded_rectangle(TERM_BOX, radius=14, fill=TERM_BG, outline=BORDER, width=2)
    draw.rectangle((TERM_BOX[0] + 2, TERM_BOX[1] + 2, TERM_BOX[2] - 2, TERM_BOX[1] + 36), fill=(17, 30, 49))
    for i, color in enumerate([RED, GOLD, GREEN]):
        cx = TERM_BOX[0] + 22 + i * 20
        draw.ellipse((cx, TERM_BOX[1] + 15, cx + 10, TERM_BOX[1] + 25), fill=color)
    draw.text((TERM_BOX[0] + 92, TERM_BOX[1] + 20), "python -m airoute  ·  excerpt",
              font=font(12), fill=MUTED, anchor="lm")

    stat_card(draw, (868, 158, 1208, 258), "TESTS", "26 / 26", "pass in 0.06 s", GREEN, 32)
    stat_card(draw, (868, 266, 1208, 366), "EXACT ARITHMETIC", "100%", "pinned as fractions.Fraction", WHITE, 32)
    stat_card(draw, (868, 374, 1208, 474), "FIGURES", "7", "generated by the code", TEAL, 32)
    stat_card(draw, (868, 482, 1208, 582), "SENSITIVITY SWEEPS", "2", "prior and sensor model", GOLD, 32)

    deliver = "Report  ·  7-slide deck  ·  demo video  ·  declarations"
    draw_lines(draw, (868, 596), wrap(draw, deliver, font(13), 340), font(13), TEXT, 18)
    draw.text((56, 662), "Excerpt from results/demo_output.txt — all values printed by the application.",
              font=font(12), fill=(130, 152, 178))
    footer(draw, 8)
    return canvas


def render_terminal(base, elapsed, duration):
    canvas = base.copy()
    draw = ImageDraw.Draw(canvas)
    start = 0.45
    n = len(TERMINAL_LINES)
    step = max(0.18, (duration - start - 0.8) / n)
    visible = max(0, min(n, int((elapsed - start) / step) + 1))
    if visible <= 0:
        return canvas
    first = max(0, visible - TERM_MAX_LINES)
    fnt = font(14, "mono")
    fnt_b = font(14, "mono_bold")
    colors = {"prompt": TEAL, "section": GOLD, "normal": TERM_TEXT,
              "output": WHITE, "pass": GREEN}
    y = TERM_TEXT_Y
    for i in range(first, visible):
        text, kind = TERMINAL_LINES[i]
        if text:
            draw.text((TERM_TEXT_X, y), text, font=fnt_b if kind in ("output", "pass") else fnt,
                      fill=colors[kind])
        y += TERM_LINE_H
    if int(elapsed * 2) % 2 == 0:
        last_text = TERMINAL_LINES[visible - 1][0]
        cw = draw.textlength(last_text, font=fnt_b)
        draw.rectangle((TERM_TEXT_X + cw + 4, y - TERM_LINE_H + 3,
                        TERM_TEXT_X + cw + 12, y - 2), fill=TEAL)
    return canvas


def closing_slide():
    canvas = Image.new("RGB", (W, H), BG)
    im = map_plot()
    scaled_w = 640
    scaled_h = round(im.height * scaled_w / im.width)
    im = im.resize((scaled_w, scaled_h), Image.LANCZOS)
    im = Image.blend(im, Image.new("RGB", im.size, BG), 0.82)
    canvas.paste(im, (640, (H - scaled_h) // 2))
    draw = ImageDraw.Draw(canvas)
    draw.text((72, 64), "FINAL PROJECT  ·  QAIRU UNIVERSITY", font=font(15, "semi"), fill=GOLD)
    draw.text((72, 150), "Four", font=font(68, "semi"), fill=WHITE)
    draw.text((72, 226), "algorithms.", font=font(68, "semi"), fill=WHITE)
    draw.text((72, 302), "One decision.", font=font(68, "semi"), fill=TEAL)
    draw.text((72, 412), "CleanRoute Astana — thank you. Questions?", font=font(22), fill=TEXT)
    draw.text((72, 588), "Ibragim Mukash", font=font(18, "semi"), fill=WHITE)
    draw.text((72, 616), "23 November 2026", font=font(14), fill=MUTED)
    return canvas


SEGMENTS = [
    {"id": "s1", "build": title_slide, "lead": 0.6, "tail": 0.6, "hold": 0.5, "terminal": False,
     "text": "CleanRoute Astana: a mini air-quality adviser that decides when to leave and which way to walk. "
             "Final project for AI Fundamentals, by Ibrageem Mukash."},
    {"id": "s2", "build": problem_slide, "lead": 0.35, "tail": 0.5, "hold": 0.0, "terminal": False,
     "text": "On a winter evening in Astana, a temperature inversion traps particulate matter near the ground. "
             "Air quality changes hour to hour and block to block, so a city-wide AQI cannot answer the two questions "
             "that matter: go out now, or wait? And which way to walk? Every input is small and declared."},
    {"id": "s3", "build": bayes_slide, "lead": 0.35, "tail": 0.5, "hold": 0.0, "terminal": False,
     "text": "First, Bayesian inference. Before any reading, the chance of hazardous air is thirty percent. The sensor "
             "alarms in eighty-five percent of hazardous hours, but also in twenty percent of clean ones. An alarm "
             "raises the belief to sixty-four point six percent; a calm reading drops it to seven point four. The "
             "likelihood ratio is four point two five — one signal becomes a calibrated belief."},
    {"id": "s4", "build": search_slide, "lead": 0.35, "tail": 0.5, "hold": 0.0, "terminal": False,
     "text": "Second, search. Each of the thirty-six blocks carries a pollution weight, so a route costs the sum of its "
             "blocks. Breadth-first search finds eight steps but a dose of nineteen. Uniform-cost search and A-star find "
             "the minimum-exposure route: twelve steps, dose fourteen. A-star proves optimality while expanding sixteen "
             "nodes instead of twenty-one, and the cleaner detour cuts the dose by twenty-six point three percent."},
    {"id": "s5", "build": mdp_slide, "lead": 0.35, "tail": 0.5, "hold": 0.0, "terminal": False,
     "text": "Third, a Markov decision process. Going now earns twelve minus zero point zero two times concentration "
             "times route weight; waiting costs four to six points. For the short route, go is optimal only below a hazard "
             "belief of forty-nine point five percent, so the alarm says wait. For the clean route the threshold is "
             "seventy-nine point seven, so the same belief says go. Value iteration agrees."},
    {"id": "s6", "build": hmm_slide, "lead": 0.35, "tail": 0.5, "hold": 0.0, "terminal": False,
     "text": "Fourth, a hidden Markov model. Two alarms push the belief to eighty point six percent, but the third, calm "
             "reading, combined with the transition model, pulls it to eighteen point one, below every threshold. Viterbi "
             "recovers high, high, acceptable; forward filtering tracks the full distribution."},
    {"id": "s7", "build": final_slide, "lead": 0.35, "tail": 0.5, "hold": 0.6, "terminal": False,
     "text": "The integrated answer: leave now and walk the twelve-step route through the park belt. It adds four steps "
             "but cuts the dose by twenty-six percent. With belief eighteen point one against a threshold of "
             "seventy-nine point seven, the margin is plus nine point one one five."},
    {"id": "s8", "build": terminal_base, "lead": 0.35, "tail": 0.55, "hold": 2.2, "terminal": True,
     "text": "The package ships twenty-six automated tests that pin every hand-derived value, and all twenty-six pass. "
             "The console reproduces the whole trace, and every figure is generated by the code."},
    {"id": "s9", "build": closing_slide, "lead": 0.35, "tail": 0.5, "hold": 1.8, "terminal": False,
     "text": "CleanRoute Astana: four algorithms, one decision. Thank you for watching."},
]


def run(cmd):
    subprocess.run(cmd, check=True, capture_output=True)


async def synth_text(text, path):
    for attempt in range(5):
        try:
            await edge_tts.Communicate(text, VOICE, rate=RATE).save(path)
            if os.path.getsize(path) > 0:
                return
        except Exception:
            pass
        if os.path.exists(path):
            os.remove(path)
        await asyncio.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"TTS returned no audio for {path}")


async def synth_all():
    os.makedirs(VOICE_DIR, exist_ok=True)
    for seg in SEGMENTS:
        mp3 = os.path.join(VOICE_DIR, seg["id"] + ".mp3")
        if os.path.exists(mp3) and os.path.getsize(mp3) > 0:
            continue
        await synth_text(seg["text"], mp3)


def decode_all():
    for seg in SEGMENTS:
        mp3 = os.path.join(VOICE_DIR, seg["id"] + ".mp3")
        wav = os.path.join(VOICE_DIR, seg["id"] + ".wav")
        run([FFMPEG, "-y", "-i", mp3, "-ac", "1", "-ar", "24000", "-sample_fmt", "s16", wav])
        with wave.open(wav) as wf:
            seg["audio"] = wf.getnframes() / wf.getframerate()
        seg["dur"] = seg["lead"] + seg["audio"] + seg["tail"] + seg["hold"]
        seg["frames"] = max(1, round(seg["dur"] * FPS))
        seg["dur"] = seg["frames"] / FPS


def build_audio(total_samples):
    rate = 24000
    mix = bytearray(total_samples * 2)
    cursor = 0.0
    for seg in SEGMENTS:
        wav_path = os.path.join(VOICE_DIR, seg["id"] + ".wav")
        with wave.open(wav_path) as wf:
            data = wf.readframes(wf.getnframes())
        offset = int((cursor + seg["lead"]) * rate)
        start = offset * 2
        mix[start:start + len(data)] = data
        cursor += seg["dur"]
    out = os.path.join(VOICE_DIR, "narration.wav")
    with wave.open(out, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(bytes(mix))
    return out


def kb_frame(big, t, direction):
    bw, bh = big.size
    s = 1.0 - 0.05 * t if direction > 0 else 0.95 + 0.05 * t
    cw, ch = int(W * s + (bw - W)), int(H * s + (bh - H))
    x = (bw - cw) // 2
    y = (bh - ch) // 2
    return big.crop((x, y, x + cw, y + ch)).resize((W, H), Image.LANCZOS)


def render_frames(audio_path, out_path):
    total_frames = sum(seg["frames"] for seg in SEGMENTS)
    total_dur = total_frames / FPS
    cmd = [FFMPEG, "-y", "-f", "image2pipe", "-vcodec", "mjpeg", "-framerate", str(FPS),
           "-i", "-", "-i", audio_path, "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "160k",
           "-shortest", "-movflags", "+faststart", out_path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE)
    navy = Image.new("RGB", (W, H), BG)
    done = 0
    boundaries = []
    for idx, seg in enumerate(SEGMENTS):
        base = seg["build"]()
        big = base.resize((int(W * 1.05), int(H * 1.05)), Image.LANCZOS)
        direction = 1 if idx % 2 == 0 else -1
        boundaries.append((seg["id"], done / FPS, seg["dur"]))
        for k in range(seg["frames"]):
            t = k / max(1, seg["frames"] - 1)
            if seg["terminal"]:
                canvas = render_terminal(base, k / FPS, seg["dur"])
                canvas = kb_frame(canvas.resize((int(W * 1.05), int(H * 1.05)), Image.LANCZOS),
                                  t, direction)
            else:
                canvas = kb_frame(big, t, direction)
            time = (done + k) / FPS
            fade = 1.0
            if idx == 0 and k < 0.6 * FPS:
                fade = k / (0.6 * FPS)
            elif idx == len(SEGMENTS) - 1 and (seg["frames"] - 1 - k) < 0.9 * FPS:
                fade = max(0.0, (seg["frames"] - 1 - k) / (0.9 * FPS))
            if fade < 1.0:
                canvas = Image.blend(navy, canvas, fade)
            buf = __import__("io").BytesIO()
            canvas.save(buf, "JPEG", quality=90)
            proc.stdin.write(buf.getvalue())
            done += 1
        print(f"  {seg['id']}: {seg['dur']:.2f}s  ({seg['audio']:.2f}s narration)")
    proc.stdin.close()
    err = proc.stderr.read().decode("utf-8", "replace")
    proc.wait()
    if proc.returncode != 0:
        print(err[-3000:])
        raise SystemExit("ffmpeg failed")
    return total_dur, boundaries


def previews(boundaries, total_dur):
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    marks = []
    for sid, start, dur in boundaries:
        marks.append((sid, start + dur * 0.6))
    for sid, t in marks:
        path = os.path.join(PREVIEW_DIR, f"{sid}.png")
        run([FFMPEG, "-y", "-ss", f"{t:.2f}", "-i", OUT, "-frames:v", "1", path])


def main():
    print("synth narration")
    asyncio.run(synth_all())
    decode_all()
    total = sum(seg["frames"] for seg in SEGMENTS) / FPS
    speech = sum(seg["audio"] for seg in SEGMENTS)
    print(f"speech {speech:.1f}s  video {total:.1f}s")
    audio_path = build_audio(sum(seg["frames"] for seg in SEGMENTS) * 24000 // FPS)
    print("render")
    total_dur, boundaries = render_frames(audio_path, OUT)
    print(f"wrote {OUT}  {total_dur:.2f}s")
    previews(boundaries, total_dur)


if __name__ == "__main__":
    main()
