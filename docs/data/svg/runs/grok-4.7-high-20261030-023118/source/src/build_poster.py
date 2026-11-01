#!/usr/bin/env python3
"""Someone is home in there.

A poster for the moment before you harm, dismiss, or pass someone by.
The figure is ordinary and upright — an equal, not a victim. The window
in the chest is a room, not a wound: framed, domestic, lit from within.
"""

import math
import os
import random
import subprocess
import sys

sys.path.insert(0, os.path.dirname(__file__))
from fontpath import load_font, text_path

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = "/System/Library/Fonts/Supplemental"
ROMAN = load_font(os.path.join(FONT_DIR, "Georgia.ttf"))
ITALIC = load_font(os.path.join(FONT_DIR, "Georgia Italic.ttf"))

W, H = 1200, 1600


def svg_text(font, text, size, x, y, fill, anchor="middle", tracking=0, dx=0, opacity=1):
    extra = f'opacity="{opacity:.3f}"' if opacity < 1 else ""
    element, width = text_path(
        font, text, size, x + dx, y, anchor=anchor, fill=fill,
        letter_spacing=tracking, extra=extra,
    )
    return element, width


def building(x, y, w, h, fill, windows, lit):
    """Simple facade. windows is a list of (rx, ry) relative lit or dark."""
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}"/>']
    # slight lighter cornice
    parts.append(
        f'<rect x="{x}" y="{y}" width="{w}" height="3" fill="#243044" opacity="0.7"/>'
    )
    for wx, wy, on in windows:
        if on:
            parts.append(
                f'<rect x="{x+wx}" y="{y+wy}" width="8" height="10" rx="0.5" fill="#ffc98a"/>'
            )
            parts.append(
                f'<rect x="{x+wx}" y="{y+wy}" width="8" height="4" fill="#ffe6c0" opacity="0.85"/>'
            )
        else:
            parts.append(
                f'<rect x="{x+wx}" y="{y+wy}" width="7" height="9" fill="#1c2633" opacity="0.9"/>'
            )
    return "\n".join(parts)


def crowd_figure(cx, feet, h, kind="adult", light=1.0, hood=False):
    """A small person, dark, with a lit room at the chest. Dignity, no caricature."""
    if kind == "child":
        head_r = h * 0.20
        body_w = h * 0.30
    elif kind == "elder":
        head_r = h * 0.155
        body_w = h * 0.34
    else:
        head_r = h * 0.155
        body_w = h * 0.30
    head_cy = feet - h + head_r * 1.05
    if kind == "elder":
        head_cy += h * 0.04  # slight forward stoop, still upright enough to be proud
    shoulder_y = head_cy + head_r * 0.85
    body_top = shoulder_y - head_r * 0.15
    hem = feet
    left = cx - body_w
    right = cx + body_w
    # coat
    coat = (
        f"M {cx:.1f} {body_top:.1f} "
        f"C {left+body_w*0.3:.1f} {body_top:.1f}, {left:.1f} {shoulder_y:.1f}, {left-2:.1f} {shoulder_y+h*0.18:.1f} "
        f"C {left-4:.1f} {shoulder_y+h*0.42:.1f}, {left+2:.1f} {hem-h*0.08:.1f}, {left+body_w*0.35:.1f} {hem:.1f} "
        f"L {right-body_w*0.35:.1f} {hem:.1f} "
        f"C {right-2:.1f} {hem-h*0.08:.1f}, {right+4:.1f} {shoulder_y+h*0.42:.1f}, {right+2:.1f} {shoulder_y+h*0.18:.1f} "
        f"C {right:.1f} {shoulder_y:.1f}, {right-body_w*0.3:.1f} {body_top:.1f}, {cx:.1f} {body_top:.1f} Z"
    )
    head = (
        f'<circle cx="{cx:.1f}" cy="{head_cy:.1f}" r="{head_r:.1f}" fill="#0c121a" '
        f'stroke="#6a7c90" stroke-width="0.7"/>'
    )
    hood_el = ""
    if hood:
        hood_el = (
            f'<path d="M {cx-head_r*0.9:.1f} {head_cy+2:.1f} '
            f'C {cx-head_r:.1f} {head_cy-head_r*1.3:.1f}, {cx+head_r:.1f} {head_cy-head_r*1.3:.1f}, '
            f'{cx+head_r*0.9:.1f} {head_cy+2:.1f} Z" fill="#101722"/>'
        )
    # window
    ww, wh = max(6.5, body_w * 0.55), max(8.0, h * 0.13)
    wx = cx - ww / 2
    wy = shoulder_y + h * 0.10
    win_op = max(0.0, min(1.0, light))
    window = (
        f'<g opacity="{win_op:.3f}">'
        f'<rect x="{wx-0.8:.1f}" y="{wy-0.8:.1f}" width="{ww+1.6:.1f}" height="{wh+2.2:.1f}" fill="#2a2118"/>'
        f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="{wh:.1f}" fill="#ffc27a"/>'
        f'<rect x="{wx:.1f}" y="{wy:.1f}" width="{ww:.1f}" height="{wh*0.45:.1f}" fill="#ffe6c2"/>'
        f'</g>'
    )
    # tiny ground reflection
    ref = (
        f'<ellipse cx="{cx:.1f}" cy="{feet+7:.1f}" rx="{ww:.1f}" ry="3.2" fill="#ffb060" '
        f'opacity="{0.18*light:.3f}"/>'
    )
    return (
        f'<g>'
        f'<path d="{coat}" fill="#0c121a" stroke="#6a7c90" stroke-width="0.8"/>'
        f'{head}{hood_el}{window}{ref}'
        f'</g>'
    )


def cane(x, y, h):
    return (
        f'<path d="M {x:.1f} {y:.1f} L {x+6:.1f} {y+h:.1f}" stroke="#5a6570" stroke-width="1.4" '
        f'stroke-linecap="round" fill="none"/>'
        f'<path d="M {x-3:.1f} {y:.1f} L {x+2:.1f} {y:.1f}" stroke="#5a6570" stroke-width="1.6" '
        f'stroke-linecap="round"/>'
    )


def stars():
    rng = random.Random(11)
    pts = []
    # loose cluster, upper left, and a few scattered — not a uniform field
    for _ in range(26):
        pts.append((rng.uniform(40, 520), rng.uniform(28, 240), rng.uniform(0.4, 1.15), rng.uniform(0.35, 0.9)))
    for _ in range(10):
        pts.append((rng.uniform(760, 1160), rng.uniform(36, 220), rng.uniform(0.35, 0.9), rng.uniform(0.25, 0.7)))
    for _ in range(8):
        pts.append((rng.uniform(80, 1120), rng.uniform(240, 520), rng.uniform(0.3, 0.7), rng.uniform(0.15, 0.4)))
    out = []
    for x, y, r, o in pts:
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#e7eef8" opacity="{o:.2f}"/>')
        if r > 0.95:
            out.append(
                f'<path d="M {x:.1f} {y-3.2:.1f} L {x:.1f} {y+3.2:.1f} M {x-3.2:.1f} {y:.1f} L {x+3.2:.1f} {y:.1f}" '
                f'stroke="#e7eef8" stroke-width="0.4" opacity="{o*0.7:.2f}"/>'
            )
    return "\n".join(out)


def rain(seed, n, x0, x1, y0, y1, opacity, length=16):
    rng = random.Random(seed)
    parts = []
    for _ in range(n):
        x = rng.uniform(x0, x1)
        y = rng.uniform(y0, y1)
        parts.append(
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x+5:.1f}" y2="{y+length:.1f}" '
            f'stroke="#c5d0dc" stroke-width="0.8" opacity="{opacity:.3f}" stroke-linecap="round"/>'
        )
    return "\n".join(parts)


def build(face=1.0, window=1.0, crowd=1.0, text=1.0):
    parts = []
    A = parts.append

    A('<?xml version="1.0" encoding="UTF-8"?>')
    A(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    A("<title>Someone is home in there</title>")
    A(
        "<desc>A person stands in the rain at night, upright and calm, meeting your eyes. "
        "Set into their chest is a real window with a wooden frame and a sill. Through it, "
        "a warmly lit room: a lamp, two cups on a table, a plant, and someone sitting at home, "
        "turned toward their own light. The same warmth is caught in the standing person's eyes. "
        "Around them on the wet street, other people — a child, an elder, neighbors — each carry "
        "a small lit window. The words read: Someone is home in there. Leave them warmer than "
        "you found them. You are in there too.</desc>"
    )

    A("""<defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#07090e"/>
      <stop offset="38%" stop-color="#101722"/>
      <stop offset="62%" stop-color="#161e2a"/>
      <stop offset="100%" stop-color="#0b0e14"/>
    </linearGradient>
    <radialGradient id="lampPool" cx="50%" cy="46%" r="48%">
      <stop offset="0%" stop-color="#f0a24a" stop-opacity="0.30"/>
      <stop offset="32%" stop-color="#c46a28" stop-opacity="0.10"/>
      <stop offset="68%" stop-color="#c46a28" stop-opacity="0.02"/>
      <stop offset="100%" stop-color="#c46a28" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="vignette" cx="50%" cy="40%" r="72%">
      <stop offset="55%" stop-color="#000" stop-opacity="0"/>
      <stop offset="100%" stop-color="#000" stop-opacity="0.62"/>
    </radialGradient>
    <linearGradient id="faceGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2a3344"/>
      <stop offset="42%" stop-color="#3a343c"/>
      <stop offset="70%" stop-color="#5c433c"/>
      <stop offset="100%" stop-color="#7a5648"/>
    </linearGradient>
    <linearGradient id="neckGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#4a3834"/>
      <stop offset="55%" stop-color="#3a2c2c"/>
      <stop offset="100%" stop-color="#241c22"/>
    </linearGradient>
    <radialGradient id="coatGrad" cx="50%" cy="42%" r="62%">
      <stop offset="0%" stop-color="#2a241f"/>
      <stop offset="42%" stop-color="#1a2130"/>
      <stop offset="100%" stop-color="#121820"/>
    </radialGradient>
    <linearGradient id="wood" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#7a5340"/>
      <stop offset="40%" stop-color="#4e3426"/>
      <stop offset="100%" stop-color="#3a261c"/>
    </linearGradient>
    <radialGradient id="roomWall" cx="42%" cy="28%" r="75%">
      <stop offset="0%" stop-color="#ffe0b0"/>
      <stop offset="45%" stop-color="#f0b56e"/>
      <stop offset="100%" stop-color="#d4894e"/>
    </radialGradient>
    <linearGradient id="floorG" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#c48448"/>
      <stop offset="100%" stop-color="#8a542e"/>
    </linearGradient>
    <linearGradient id="reflect" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#ffb25c" stop-opacity="0.42"/>
      <stop offset="35%" stop-color="#e88840" stop-opacity="0.14"/>
      <stop offset="100%" stop-color="#e88840" stop-opacity="0"/>
    </linearGradient>
    <linearGradient id="street" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#141b26"/>
      <stop offset="30%" stop-color="#10151e"/>
      <stop offset="100%" stop-color="#0c1016"/>
    </linearGradient>
    <filter id="blur18" x="-60%" y="-60%" width="220%" height="220%">
      <feGaussianBlur stdDeviation="18"/>
    </filter>
    <filter id="blur8" x="-40%" y="-40%" width="180%" height="180%">
      <feGaussianBlur stdDeviation="7"/>
    </filter>
    <filter id="blur3" x="-30%" y="-30%" width="160%" height="160%">
      <feGaussianBlur stdDeviation="2.4"/>
    </filter>
    <clipPath id="roomClip">
      <rect x="518" y="778" width="164" height="196"/>
    </clipPath>
    <clipPath id="eyeL">
      <path d="M 518 422 C 534 410, 566 410, 582 422 C 566 434, 534 434, 518 422 Z"/>
    </clipPath>
    <clipPath id="eyeR">
      <path d="M 618 422 C 634 410, 666 410, 682 422 C 666 434, 634 434, 618 422 Z"/>
    </clipPath>
    <linearGradient id="haze" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#243246" stop-opacity="0"/>
      <stop offset="45%" stop-color="#243246" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#243246" stop-opacity="0.08"/>
    </linearGradient>
    <clipPath id="posterClip">
      <rect width="1200" height="1600"/>
    </clipPath>
  </defs>""")

    A('<g clip-path="url(#posterClip)">')

    # sky
    A('<rect width="1200" height="1600" fill="url(#sky)"/>')
    A(f'<rect width="1200" height="1600" fill="url(#lampPool)" opacity="{window:.3f}"/>')
    A(stars())

    # moon — crescent facing the figure
    A('<circle cx="1042" cy="118" r="46" fill="#d5e2f2" opacity="0.10" filter="url(#blur18)"/>')
    A("""<mask id="crescent">
      <circle cx="1036" cy="124" r="26" fill="white"/>
      <circle cx="1050" cy="112" r="22" fill="black"/>
    </mask>
    <circle cx="1036" cy="124" r="26" fill="#f4f7fb" mask="url(#crescent)"/>""")

    # distant buildings, framing the head but leaving sky around the face
    A(building(0, 610, 78, 430, "#0e141c", [
        (18, 40, True), (46, 70, False), (22, 120, False), (48, 160, True),
        (20, 220, False), (44, 250, False), (24, 310, True),
    ], True))
    A(building(62, 690, 118, 350, "#121924", [
        (16, 36, False), (48, 36, True), (80, 36, False),
        (16, 90, False), (48, 90, False), (80, 90, True),
        (22, 150, True), (60, 160, False), (86, 200, False),
        (30, 230, False),
    ], True))
    A(building(168, 760, 96, 280, "#101722", [
        (14, 28, False), (42, 28, False), (68, 48, True),
        (16, 100, False), (48, 110, False), (20, 170, True),
    ], True))
    A(building(250, 820, 70, 220, "#0e141c", [
        (14, 30, True), (40, 70, False), (18, 120, False),
    ], True))

    A(building(900, 800, 88, 240, "#101722", [
        (14, 28, False), (44, 40, True), (18, 90, False), (50, 120, False),
        (22, 170, True),
    ], True))
    A(building(972, 680, 130, 360, "#121924", [
        (16, 30, True), (52, 30, False), (88, 30, False),
        (18, 84, False), (54, 84, True), (90, 90, False),
        (20, 150, False), (60, 160, False), (96, 150, True),
        (28, 220, True), (70, 230, False),
    ], True))
    A(building(1090, 590, 110, 450, "#0e141c", [
        (18, 36, False), (52, 50, True), (80, 36, False),
        (20, 110, True), (58, 120, False), (84, 160, False),
        (24, 200, False), (62, 220, True), (28, 290, False),
        (70, 320, True),
    ], True))

    # rain behind the figure
    A(rain(3, 110, 0, 1200, 0, 1100, 0.11, 15))

    # horizon haze so the small figures separate from the buildings
    A('<rect x="0" y="860" width="1200" height="230" fill="url(#haze)"/>')
    A('<rect x="0" y="1044" width="1200" height="220" fill="url(#street)"/>')
    A('<line x1="0" y1="1048" x2="1200" y2="1048" stroke="#3a4a5c" stroke-width="1" opacity="0.45"/>')

    # neighbors, each carrying a light — drawn over the street so they can be seen
    A(crowd_figure(42, 1046, 46, hood=True, light=crowd))
    A(crowd_figure(108, 1048, 64, light=crowd))
    A(crowd_figure(176, 1048, 86, light=crowd))
    A(crowd_figure(214, 1050, 54, kind="child", light=crowd))
    A('<path d="M 192 1012 Q 202 1018 208 1006" stroke="#8aa0b4" stroke-width="1.4" fill="none" stroke-linecap="round" opacity="0.7"/>')
    A(crowd_figure(286, 1048, 70, hood=True, light=crowd))
    A(crowd_figure(908, 1048, 76, light=crowd))
    A(crowd_figure(978, 1046, 60, kind="elder", light=crowd))
    A(cane(996, 1004, 42))
    A(crowd_figure(1052, 1044, 66, light=crowd))
    A('<rect x="1068" y="1006" width="8" height="10" rx="1.4" fill="#0c121a" stroke="#6a7c90" stroke-width="0.6"/>')
    A(crowd_figure(1124, 1042, 50, hood=True, light=crowd))
    A(crowd_figure(1172, 1044, 44, light=crowd))
    A('<rect x="78" y="1036" width="34" height="7" rx="1" fill="#1a2430"/>')
    A(crowd_figure(94, 1036, 48, light=crowd))

    # rain behind the hero, in front of the city
    A(rain(4, 70, 0, 1200, 40, 1040, 0.10, 14))

    # warmth behind the body
    A(f'<ellipse cx="600" cy="880" rx="240" ry="200" fill="#ffb25c" opacity="{0.20 * window:.3f}" filter="url(#blur18)"/>')

    # ---------- HERO ----------
    # one coat, neck included, so the head has a body to stand on
    A("""
    <path d="M 558 548
             C 544 598, 492 632, 430 658
             C 392 678, 362 742, 354 836
             C 346 930, 366 1024, 412 1096
             C 432 1124, 468 1136, 520 1136
             L 680 1136
             C 732 1136, 768 1124, 788 1096
             C 834 1024, 854 930, 846 836
             C 838 742, 808 678, 770 658
             C 708 632, 656 598, 642 548
             C 628 566, 600 576, 572 566
             C 562 556, 558 548, 558 548 Z"
          fill="url(#coatGrad)" />
    <path d="M 430 662 C 396 710, 362 800, 354 900 C 350 980, 372 1060, 414 1104"
          fill="none" stroke="#8aa4bc" stroke-width="1.6" opacity="0.40" stroke-linecap="round"/>
    <path d="M 770 670 C 808 750, 846 860, 820 1040"
          fill="none" stroke="#c48468" stroke-width="1.8" opacity="0.28" stroke-linecap="round"/>
    <!-- sleeves, a shade darker, so the coat is a coat -->
    <path d="M 438 668 C 404 730, 378 840, 388 990 L 436 1002 C 424 860, 456 760, 478 692 Z" fill="#0c1016" opacity="0.38"/>
    <path d="M 762 668 C 796 730, 822 840, 812 990 L 764 1002 C 776 860, 744 760, 722 692 Z" fill="#0c1016" opacity="0.38"/>
    <path d="M 468 992 L 524 1004" stroke="#0a0e14" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>
    <path d="M 732 992 L 676 1004" stroke="#0a0e14" stroke-width="1.5" stroke-linecap="round" opacity="0.75"/>
    """)

    # face — lit from below by the room, cool moon on the brow
    A(f'<g opacity="{face:.3f}">')
    A("""
    <path d="M 600 270
             C 676 276, 716 340, 710 418
             C 704 486, 672 540, 628 564
             Q 600 578, 572 564
             C 528 540, 496 486, 490 418
             C 484 340, 524 276, 600 270 Z" fill="url(#faceGrad)"/>
    <path d="M 498 424
             C 484 348, 514 268, 568 256
             C 612 248, 668 254, 714 296
             C 730 328, 724 388, 710 428
             C 696 368, 658 342, 600 336
             C 546 342, 510 372, 498 424 Z" fill="#10141c"/>
    <path d="M 528 300 C 560 280, 650 278, 688 308"
          fill="none" stroke="#5a6e86" stroke-width="1.4" opacity="0.35" stroke-linecap="round"/>
    <!-- folded cuff, so the dark shape is a knit cap in the rain, not a failed haircut -->
    <path d="M 504 392
             C 512 352, 548 336, 600 334
             C 652 336, 688 352, 696 392
             C 684 362, 646 350, 600 348
             C 552 350, 516 364, 504 392 Z" fill="#1c2636"/>
    <path d="M 512 378 C 548 362, 652 362, 688 378" fill="none" stroke="#3a4a60" stroke-width="0.7" opacity="0.45"/>
    """)

    # eyes
    A("""
    <ellipse cx="550" cy="424" rx="34" ry="16" fill="#140e12" opacity="0.16"/>
    <ellipse cx="650" cy="424" rx="34" ry="16" fill="#140e12" opacity="0.16"/>
    <g clip-path="url(#eyeL)">
      <rect x="510" y="400" width="80" height="44" fill="#c9b8a6"/>
      <circle cx="550" cy="422" r="13" fill="#1a100c"/>
      <circle cx="550" cy="422" r="11.2" fill="#2c1c14"/>
      <circle cx="550" cy="423" r="5.8" fill="#0c0806"/>
      <rect x="546" y="426.5" width="3.6" height="4.2" rx="0.4" fill="#ffe2ae"/>
      <circle cx="556" cy="416" r="1.2" fill="#d7e6f6"/>
    </g>
    <g clip-path="url(#eyeR)">
      <rect x="610" y="400" width="80" height="44" fill="#c9b8a6"/>
      <circle cx="650" cy="422" r="13" fill="#1a100c"/>
      <circle cx="650" cy="422" r="11.2" fill="#2c1c14"/>
      <circle cx="650" cy="423" r="5.8" fill="#0c0806"/>
      <rect x="646" y="426.5" width="3.6" height="4.2" rx="0.4" fill="#ffe2ae"/>
      <circle cx="656" cy="416" r="1.2" fill="#d7e6f6"/>
    </g>
    <path d="M 518 422 C 534 410, 566 410, 582 422" fill="none" stroke="#140e0c" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M 618 422 C 634 410, 666 410, 682 422" fill="none" stroke="#140e0c" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M 526 423 C 548 434, 570 434, 576 423" fill="none" stroke="#e0a080" stroke-width="0.9" opacity="0.5"/>
    <path d="M 622 423 C 644 434, 666 434, 674 423" fill="none" stroke="#e0a080" stroke-width="0.9" opacity="0.5"/>
    <path d="M 522 400 Q 550 392, 578 402" fill="none" stroke="#161210" stroke-width="2.6" stroke-linecap="round"/>
    <path d="M 678 400 Q 650 392, 622 402" fill="none" stroke="#161210" stroke-width="2.6" stroke-linecap="round"/>
    <path d="M 598 438 Q 602 468, 600 488" fill="none" stroke="#2a2226" stroke-width="3.2" opacity="0.10" stroke-linecap="round"/>
    <ellipse cx="600" cy="496" rx="12" ry="5" fill="#1a1210" opacity="0.15"/>
    <path d="M 584 518 Q 600 522, 616 518 Q 600 530, 584 518 Z" fill="#7a4e48"/>
    <path d="M 588 520 Q 600 524, 612 520" fill="none" stroke="#3a2420" stroke-width="1.05" stroke-linecap="round"/>
    <path d="M 590 523 Q 600 530, 610 523" fill="none" stroke="#c48a78" stroke-width="1.2" opacity="0.35" stroke-linecap="round"/>
    """)
    A('</g>')

    # window — a made thing, framed and silled, not an opening in flesh
    A(f'<g opacity="{window:.3f}">')
    A('<ellipse cx="600" cy="900" rx="150" ry="120" fill="#ffb25c" opacity="0.28" filter="url(#blur18)"/>')
    A('<rect x="506" y="768" width="196" height="228" rx="3" fill="#000" opacity="0.30"/>')
    A('<rect x="498" y="758" width="204" height="232" rx="2" fill="#1a120e"/>')
    A('<rect x="502" y="762" width="196" height="222" fill="url(#wood)"/>')
    A('<rect x="502" y="762" width="196" height="3" fill="#e8c498" opacity="0.55"/>')
    A('<rect x="502" y="762" width="3" height="196" fill="#e8c498" opacity="0.28"/>')
    A('<rect x="514" y="774" width="172" height="202" fill="#120e0c"/>')

    A("""
    <g clip-path="url(#roomClip)">
      <g transform="translate(518, 778)">
        <rect width="164" height="196" fill="url(#roomWall)"/>
        <rect y="148" width="164" height="48" fill="url(#floorG)"/>
        <rect y="146" width="164" height="3" fill="#7a4a30"/>
        <ellipse cx="68" cy="162" rx="42" ry="9" fill="#ffe0a8" opacity="0.32"/>
        <rect x="14" y="28" width="32" height="36" fill="#5c3a28"/>
        <rect x="17" y="31" width="26" height="30" fill="#f3e6d2"/>
        <rect x="17" y="31" width="26" height="16" fill="#8aabbe"/>
        <circle cx="34" cy="37" r="2" fill="#f7f4ee"/>
        <rect x="17" y="47" width="26" height="14" fill="#c49868"/>
        <path d="M 0 0 C 24 8, 30 36, 22 78 C 16 110, 6 130, 0 144 Z" fill="#243044"/>
        <path d="M 0 0 C 12 16, 14 48, 8 88 L 0 94 Z" fill="#1a2433"/>
        <rect x="2" y="66" width="12" height="3" rx="1" fill="#d4a868"/>
        <line x1="68" y1="0" x2="68" y2="18" stroke="#5c4030" stroke-width="1.2"/>
        <path d="M 50 18 L 86 18 L 94 38 L 42 38 Z" fill="#fff8ee"/>
        <path d="M 52 20 L 84 20 L 90 36 L 46 36 Z" fill="#f0e0c4"/>
        <ellipse cx="68" cy="48" rx="32" ry="14" fill="#ffe6b0" opacity="0.7"/>
        <path d="M 16 136 L 104 136 L 108 144 L 12 144 Z" fill="#c48448"/>
        <path d="M 16 136 L 104 136 L 102 139 L 18 139 Z" fill="#e0b078" opacity="0.6"/>
        <rect x="26" y="144" width="3.5" height="24" fill="#8a5430"/>
        <rect x="94" y="144" width="3.5" height="22" fill="#8a5430"/>
        <rect x="28" y="122" width="10" height="14" rx="1.3" fill="#fffaf4"/>
        <ellipse cx="33" cy="122" rx="5" ry="1.7" fill="#f4ece2"/>
        <ellipse cx="33" cy="122.4" rx="2.8" ry="1" fill="#c4a080"/>
        <rect x="68" y="120" width="11" height="16" rx="1.3" fill="#fffaf4"/>
        <ellipse cx="73.5" cy="120" rx="5.5" ry="1.8" fill="#fff"/>
        <ellipse cx="73.5" cy="120.5" rx="3" ry="1" fill="#d4b090"/>
        <rect x="128" y="102" width="5" height="44" rx="1" fill="#6b422c"/>
        <rect x="112" y="140" width="34" height="5" rx="1" fill="#7a4c30"/>
        <path d="M 118 116 C 110 118, 106 128, 108 140 L 110 146 L 136 146 C 140 134, 140 120, 134 116 Z" fill="#3a2820"/>
        <rect x="118" y="104" width="11" height="14" rx="2" fill="#3a2820"/>
        <circle cx="124" cy="94" r="13.5" fill="#3a2820"/>
        <path d="M 112 92 C 112 80, 136 78, 138 94 C 132 86, 116 86, 112 92 Z" fill="#2a1c18"/>
        <path d="M 112 122 Q 98 130, 82 136" stroke="#3a2820" stroke-width="5" fill="none" stroke-linecap="round"/>
        <path d="M 111 86 C 110 94, 111 100, 114 106" stroke="#ffd7a4" stroke-width="1.5" fill="none" stroke-linecap="round"/>
        <path d="M 110 116 C 108 124, 108 132, 110 140" stroke="#ffd7a4" stroke-width="1.1" fill="none" stroke-linecap="round" opacity="0.75"/>
      </g>
    </g>
    """)

    A('<rect x="516" y="776" width="168" height="198" fill="none" stroke="#e8c898" stroke-width="1" opacity="0.6"/>')
    A('<path d="M 534 792 L 592 792 L 548 958 L 524 958 Z" fill="#fff" opacity="0.05"/>')
    for dx, dy, rx, ry in ((38, 34, 1.2, 2.0), (78, 52, 0.9, 1.5), (112, 40, 1.1, 1.8), (96, 96, 0.8, 1.4), (58, 124, 1.0, 1.7)):
        A(f'<ellipse cx="{518+dx}" cy="{778+dy}" rx="{rx}" ry="{ry}" fill="#fff" opacity="0.28"/>')

    A("""
    <polygon points="492,972 708,972 716,982 484,982" fill="#e4b488"/>
    <polygon points="484,982 716,982 710,998 490,998" fill="#a06840"/>
    <line x1="492" y1="998" x2="708" y2="998" stroke="#6a4028" stroke-width="1"/>
    <line x1="500" y1="974" x2="700" y2="974" stroke="#fff1dc" stroke-width="0.8" opacity="0.45"/>
    <g transform="translate(546, 970)">
      <ellipse cx="0" cy="10" rx="10" ry="6.5" fill="#9a4030"/>
      <ellipse cx="0" cy="7" rx="8" ry="3.2" fill="#c45a40"/>
      <ellipse cx="-1" cy="-14" rx="5" ry="13" fill="#1e5c40" transform="rotate(-18)"/>
      <ellipse cx="5" cy="-16" rx="4.2" ry="12" fill="#2e7a50" transform="rotate(16)"/>
      <ellipse cx="-8" cy="-10" rx="3.6" ry="9" fill="#164832" transform="rotate(-48)"/>
      <ellipse cx="11" cy="-8" rx="3.2" ry="8" fill="#4e9a62" transform="rotate(42)"/>
      <ellipse cx="2" cy="-20" rx="3.4" ry="8" fill="#3d8a58" transform="rotate(4)"/>
    </g>
    """)

    A(rain(9, 14, 370, 460, 760, 960, 0.15, 11))
    A(rain(10, 12, 750, 840, 780, 980, 0.13, 11))
    A('<rect x="545" y="1096" width="110" height="210" fill="url(#reflect)" filter="url(#blur8)"/>')
    A('<ellipse cx="600" cy="1118" rx="70" ry="10" fill="#ffc080" opacity="0.28" filter="url(#blur3)"/>')
    A('</g>')

    # reflection is inside the window group above; the ground stays

    # contact shadow
    A('<ellipse cx="600" cy="1106" rx="150" ry="8" fill="#000" opacity="0.35" filter="url(#blur3)"/>')

    # ---------- TYPE ----------
    A(f'<g opacity="{text:.3f}">')
    # "Someone is home"
    el, _ = svg_text(ROMAN, "Someone is home", 76, 600, 1264, "#f4f0e6", tracking=0.6)
    A(el)
    # italic, nudged left a hair so the slant looks centered
    el, _ = svg_text(ITALIC, "in there.", 76, 600, 1352, "#f0c98a", tracking=0.4, dx=-6)
    A(el)

    # tiny window, the same idea at the size of a word
    A("""
    <g transform="translate(600, 1388)">
      <ellipse cx="0" cy="0" rx="16" ry="14" fill="#ffb25c" opacity="0.35" filter="url(#blur8)"/>
      <rect x="-8" y="-11" width="16" height="20" fill="#3a2a20"/>
      <rect x="-6" y="-9" width="12" height="14" fill="#ffd7a0"/>
      <rect x="-6" y="-9" width="12" height="6" fill="#fff0d4"/>
      <rect x="-9" y="5" width="18" height="3" fill="#e0b080"/>
    </g>
    """)

    el, _ = svg_text(ROMAN, "Leave them warmer", 34, 600, 1454, "#f6ead4", tracking=0.4)
    A(el)
    el, _ = svg_text(ITALIC, "than you found them.", 34, 600, 1498, "#f0c98a", tracking=0.3, dx=-4)
    A(el)

    el, _ = svg_text(ITALIC, "You are in there too.", 22, 600, 1546, "#d4b48a", tracking=0.8, dx=-2)
    A(el)

    el, _ = svg_text(
        ROMAN,
        "BEFORE THE HARSH WORD, THE TURNED BACK, THE RAISED HAND.",
        15,
        600,
        1584,
        "#aeb6be",
        tracking=1.35,
    )
    A(el)
    A('</g>')

    # vignette last, but not over type too heavily — it's full-frame, gentle
    A('<rect width="1200" height="1600" fill="url(#vignette)"/>')

    A("</g>")
    A("</svg>")
    return "\n".join(parts)


def main():
    svg = build()
    out = os.path.join(ROOT, "output", "someone-is-home.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"wrote {out} ({len(svg)} bytes)")


if __name__ == "__main__":
    main()
