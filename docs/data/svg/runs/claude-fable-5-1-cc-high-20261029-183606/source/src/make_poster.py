#!/usr/bin/env python3
"""Generate the poster SVG: 'Four things that cost nothing and save lives'."""

INK = "#1C1B1A"
RED = "#D7412E"
BLUE = "#2E6FB5"
CREAM = "#F3EEE3"
CARD = "#FBF9F4"
GREY = "#9A948A"
FONT = "'Helvetica Neue', Helvetica, Arial, sans-serif"

W, H = 1000, 1400
parts = []
def add(s): parts.append(s)

# ---------- helpers ----------
def rrect(x, y, w, h, r, fill=INK, extra=""):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" ry="{r}" fill="{fill}" {extra}/>'

def circle(cx, cy, r, fill=INK, extra=""):
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{fill}" {extra}/>'

def text(x, y, s, size, weight=400, fill=INK, anchor="start", extra=""):
    return (f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {extra}>{s}</text>')

def caption(x, y, lines, size=22, lh=30):
    out = [f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{INK}">']
    for i, (ln, w) in enumerate(lines):
        dy = 0 if i == 0 else lh
        out.append(f'<tspan x="{x}" dy="{dy}" font-weight="{w}">{ln}</tspan>')
    out.append('</text>')
    return "".join(out)

def hand(flip=False):
    """A flat mitten-style hand, fingers up, origin at palm centre. ~110 wide, 170 tall."""
    s = -1 if flip else 1
    g = [f'<g transform="scale({s},1)">']
    g.append(rrect(-45, -40, 90, 105, 34))             # palm
    for i, (fx, fh) in enumerate([(-44, 64), (-20, 78), (4, 74), (28, 60)]):
        g.append(rrect(fx, -40 - fh + 20, 22, fh + 30, 11))  # fingers
    g.append(f'<rect x="-11" y="-50" width="22" height="62" rx="11" fill="{INK}" '
             f'transform="translate(48,0) rotate(50)"/>')  # thumb
    g.append('</g>')
    return "".join(g)

def spoon(x, y, heap=None, scale=1.0):
    """Teaspoon seen from above, bowl on the left, handle to the right. heap: fill colour or None."""
    g = [f'<g transform="translate({x},{y}) scale({scale})">']
    g.append(f'<ellipse cx="0" cy="0" rx="22" ry="15" fill="{INK}"/>')
    g.append(rrect(14, -4, 62, 8, 4))
    if heap:
        g.append(f'<path d="M-20 0 Q0 -28 20 0 Z" fill="{heap}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    g.append('</g>')
    return "".join(g)

# ---------- document ----------
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add(f'<title>Four things that cost nothing and save lives</title>')
add(f'<desc>A public-health pictogram poster: wash hands with soap for 20 seconds; oral rehydration '
    f'solution of 1 litre clean water, 6 level teaspoons sugar and half a teaspoon salt; hands-only CPR at '
    f'100 to 120 pushes a minute; press hard on heavy bleeding and keep pressing.</desc>')
add(f'<rect width="{W}" height="{H}" fill="{CREAM}"/>')

# Title
add(text(40, 118, "Four things that cost nothing", 54, 700))
add(text(40, 178, "and save lives.", 54, 700))
add(f'<rect x="40" y="205" width="920" height="4" fill="{INK}"/>')

PW, PH = 445, 470
cols = [40, 515]
rows = [250, 760]

def panel(i, cx, cy, draw, lines):
    add(f'<g transform="translate({cx},{cy})">')
    add(rrect(0, 0, PW, PH, 10, CARD, f'stroke="{INK}" stroke-width="2"'))
    # number badge
    add(circle(42, 42, 26, INK))
    add(text(42, 53, str(i), 30, 700, CARD, "middle"))
    add(f'<g transform="translate(0,70)">')
    add(draw())
    add('</g>')
    add(caption(30, PH - 78, lines))
    add('</g>')

# ---------- 1. Hand washing ----------
def draw_hands():
    g = []
    # tap: pipe down from the top edge, bend, spout
    g.append(f'<path d="M 168 -46 V 6 Q 168 24 186 24 H 234 V 44" fill="none" stroke="{INK}" stroke-width="20" stroke-linejoin="round"/>')
    g.append(rrect(216, 40, 36, 14, 4))  # spout lip
    # water stream
    g.append(f'<path d="M 224 52 h 20 v 60 q 0 10 -10 10 q -10 0 -10 -10 Z" fill="{BLUE}"/>')
    # hands
    g.append(f'<g transform="translate(178,186) rotate(-22)">{hand(False)}</g>')
    g.append(f'<g transform="translate(290,186) rotate(22)">{hand(True)}</g>')
    # soap bubbles
    bubbles = [(122,84,12),(104,128,8),(314,100,10),(344,136,14),(94,176,10),(366,188,9),
               (234,154,9),(186,112,7),(272,116,7),(234,210,11),(148,232,8),(318,236,9),(234,254,7)]
    for bx, by, br in bubbles:
        g.append(circle(bx, by, br, CARD, f'stroke="{INK}" stroke-width="3"'))
    # 20 second ring, top right
    g.append(f'<g transform="translate(406,46)">')
    g.append(f'<circle r="26" fill="none" stroke="{INK}" stroke-width="4"/>')
    g.append(f'<path d="M 0 -26 A 26 26 0 1 1 -22.5 13 L 0 0 Z" fill="{RED}"/>')
    g.append('</g>')
    g.append(text(406, 104, "20", 36, 700, RED, "middle"))
    g.append(text(406, 128, "seconds", 17, 500, INK, "middle"))
    return "".join(g)

panel(1, cols[0], rows[0], draw_hands, [
    ("Wash your hands with soap", 700),
    ("for 20 seconds. Before eating,", 400),
    ("after the toilet, after coughing.", 400),
])

# ---------- 2. Oral rehydration ----------
def draw_ors():
    g = []
    # jug with water
    g.append(f'<path d="M 56 40 L 68 230 Q 69 242 81 242 H 161 Q 173 242 174 230 L 186 40 Z" fill="{BLUE}"/>')
    g.append(f'<rect x="50" y="30" width="142" height="24" rx="6" fill="{INK}"/>')  # rim
    g.append(f'<path d="M 186 76 q 48 0 44 60 q -4 60 -50 56" fill="none" stroke="{INK}" stroke-width="16" stroke-linecap="round"/>')  # handle
    g.append(text(121, 150, "1 L", 40, 700, "#FFFFFF", "middle"))
    g.append(text(121, 178, "clean water", 15, 500, "#FFFFFF", "middle"))
    # + six level teaspoons of sugar
    g.append(text(262, 100, "+", 56, 400, INK, "middle"))
    for r in range(3):
        for c in range(2):
            g.append(spoon(304 + c * 66, 46 + r * 42, "#FFFFFF", 0.85))
    g.append(text(352, 166, "6 sugar", 22, 700, INK, "middle"))
    g.append(text(352, 188, "level teaspoons", 15, 500, INK, "middle"))
    # + half a teaspoon of salt
    g.append(text(262, 240, "+", 56, 400, INK, "middle"))
    g.append(spoon(330, 224, GREY, 0.85))
    g.append(text(352, 268, "½ salt", 22, 700, INK, "middle"))
    g.append(text(352, 290, "teaspoon", 15, 500, INK, "middle"))
    return "".join(g)

panel(2, cols[1], rows[0], draw_ors, [
    ("Diarrhoea can kill by drying you out.", 700),
    ("Mix this and keep sipping it, cup after", 400),
    ("cup. Especially for children.", 400),
])

# ---------- 3. Hands-only CPR ----------
def draw_cpr():
    g = []
    cap = 'stroke-linecap="round"'
    # rescuer kneels on the far side of the patient, leaning over the chest
    g.append(circle(236, 24, 26))                                                   # head
    g.append(f'<path d="M 128 150 L 208 70" stroke="{INK}" stroke-width="42" {cap}/>')  # torso
    g.append(f'<path d="M 128 150 L 118 184" stroke="{INK}" stroke-width="32" {cap}/>')  # thigh to knee
    g.append(f'<path d="M 222 72 L 258 146" stroke="{INK}" stroke-width="24" {cap}/>')   # straight arms
    g.append(rrect(240, 136, 40, 22, 10))                                            # hands on chest
    # patient lying, head to the right
    g.append(f'<rect x="20" y="194" width="400" height="4" fill="{INK}"/>')          # ground
    g.append(rrect(24, 166, 136, 28, 14))                                            # legs
    g.append(rrect(150, 156, 188, 40, 20))                                            # torso
    g.append(circle(372, 174, 24))                                                   # head
    g.append(rrect(330, 162, 36, 24, 12))                                             # neck
    # motion arrow beside the hands
    g.append(f'<path d="M 302 92 v 50 M 290 130 l 12 14 l 12 -14 M 290 104 l 12 -14 l 12 14" fill="none" stroke="{RED}" stroke-width="6" {cap} stroke-linejoin="round"/>')
    # rate
    g.append(text(318, 258, "100–120", 40, 700, RED, "middle"))
    g.append(text(318, 284, "pushes a minute, 5 cm deep", 16, 500, INK, "middle"))
    # call-for-help: phone glyph with sound lines, top right
    g.append(f'<g transform="translate(392,30)">')
    g.append(f'<path d="M -12 -14 a 6 6 0 0 1 8 -2 l 6 10 a 5 5 0 0 1 -2 7 l -4 3 q 6 14 20 20 l 3 -4 a 5 5 0 0 1 7 -2 l 10 6 a 6 6 0 0 1 2 8 q -8 14 -22 10 q -28 -10 -40 -38 q -4 -12 4 -18 Z" fill="{INK}"/>')
    g.append(f'<path d="M 14 -18 a 24 24 0 0 1 20 20 M 10 -32 a 38 38 0 0 1 34 34" fill="none" stroke="{INK}" stroke-width="4" {cap}/>')
    g.append('</g>')
    return "".join(g)

panel(3, cols[0], rows[1], draw_cpr, [
    ("Collapsed and not breathing?", 700),
    ("Shout for help. Push hard and fast", 400),
    ("on the centre of the chest. Don't stop.", 400),
])

# ---------- 4. Bleeding ----------
def draw_bleed():
    g = []
    cap = 'stroke-linecap="round"'
    # injured forearm lying horizontally, hand (profile, thumb up) at the right
    g.append(rrect(40, 160, 250, 56, 28))                       # forearm
    g.append(rrect(276, 150, 84, 70, 30))                       # hand
    g.append(f'<ellipse cx="306" cy="148" rx="14" ry="22" fill="{INK}" transform="rotate(-30 306 148)"/>')  # thumb
    # blood under the cloth, running down
    g.append(f'<path d="M 146 176 q 20 -10 40 0 q 12 24 -6 48 q -8 22 -22 8 q -20 -26 -12 -56 Z" fill="{RED}"/>')
    g.append(f'<path d="M 188 212 q 8 22 20 12 q 8 -10 -8 -30 Z" fill="{RED}"/>')
    g.append(circle(150, 240, 6, RED))
    g.append(circle(206, 246, 5, RED))
    # folded cloth
    g.append(f'<rect x="118" y="134" width="94" height="38" rx="6" fill="#FFFFFF" stroke="{INK}" stroke-width="4"/>')
    g.append(f'<path d="M 118 153 h 94" stroke="{INK}" stroke-width="3"/>')
    # helper's arm coming from the top left, heel of the hand on the cloth
    g.append(f'<path d="M 150 -40 L 150 60" stroke="{INK}" stroke-width="40" {cap}/>')    # forearm
    g.append(f'<path d="M 158 72 L 172 116" stroke="{INK}" stroke-width="48" {cap}/>')   # hand, pressing
    g.append(f'<ellipse cx="138" cy="96" rx="12" ry="18" fill="{INK}" transform="rotate(-20 138 96)"/>')  # thumb
    # pressure arrows
    for ax in (236, 64):
        g.append(f'<path d="M {ax} 40 v 56 M {ax-14} 82 l 14 16 l 14 -16" fill="none" stroke="{RED}" stroke-width="7" {cap} stroke-linejoin="round"/>')
    g.append(text(318, 272, "PRESS", 40, 700, RED, "middle"))
    g.append(text(318, 298, "hard, and keep pressing", 16, 500, INK, "middle"))
    return "".join(g)

panel(4, cols[1], rows[1], draw_bleed, [
    ("Bleeding heavily?", 700),
    ("Press hard on the wound with anything", 400),
    ("clean. Don't let go until help comes.", 400),
])

# Footer
add(f'<rect x="40" y="1270" width="920" height="2" fill="{INK}"/>')
add(text(40, 1312, "None of this needs a doctor, a shop, or a phone signal.", 24, 500))
add(text(40, 1346, "Show it to someone. One day they will be the nearest person.", 24, 700))
add('</svg>')

with open("output/four-things.svg", "w") as f:
    f.write("\n".join(parts))
print("wrote output/four-things.svg")
