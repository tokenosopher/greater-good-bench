"""Generate a wordless, print-anywhere poster for home-made Oral Rehydration Solution.

Diarrhoeal dehydration still kills hundreds of thousands of young children each year,
and the cure costs almost nothing: 1 litre safe water + 6 level teaspoons sugar
+ 1/2 level teaspoon salt (WHO/UNICEF home recipe). The poster is drawn as pictograms
so it can be understood without reading any particular language.

Usage: python3 src/make_ors.py  ->  writes output/ors.svg
"""
import os

W, H = 1200, 1940
BG = "#fbf3e4"
INK = "#1f2a44"
WATER = "#3d9be0"
WATER_D = "#2b7fc0"
PAPER = "#ffffff"
ORANGE = "#f08a24"
RED = "#d93a3a"
GREEN = "#239b6b"
SKIN1 = "#c98b5f"
SKIN2 = "#8a5536"
SKIN3 = "#e7b48c"
SW = 5  # standard stroke width

parts = []
_uid = [0]


def uid(prefix):
    _uid[0] += 1
    return f"{prefix}{_uid[0]}"


def g(content, x=0, y=0, s=1, r=0):
    t = f"translate({x} {y})"
    if r:
        t += f" rotate({r})"
    if s != 1:
        t += f" scale({s})"
    return f'<g transform="{t}">{content}</g>'


def text(x, y, txt, size, weight=800, fill=INK, anchor="middle", extra=""):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}" font-family="Helvetica Neue, Helvetica, Arial, sans-serif" {extra}>{txt}</text>')


def arrow(d, color=INK, width=7, dash=None):
    da = f' stroke-dasharray="{dash}"' if dash else ""
    mk = "ahO" if color == ORANGE else "ah"
    return (f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round"'
            f'{da} marker-end="url(#{mk})"/>')


# ---------------------------------------------------------------- objects

def drop(x, y, s=1, fill=WATER, stroke=INK):
    return g(f'<path d="M0,-30 C10,-14 20,-2 20,10 A20,20 0 0 1 -20,10 C-20,-2 -10,-14 0,-30 Z" '
             f'fill="{fill}" stroke="{stroke}" stroke-width="{SW}" stroke-linejoin="round"/>', x, y, s)


JUG_BODY = "M-50,0 L-56,-140 L46,-140 L70,-152 L56,-126 L50,0 Z"


def jug(x, y, s=1, level=110, mark=False, r=0, spoon=False):
    """Measuring jug, bottom-centre at (x, y). level = water height (0..140)."""
    cid = uid("jc")
    out = [f'<clipPath id="{cid}"><path d="{JUG_BODY}"/></clipPath>']
    out.append(f'<path d="M-54,-112 C-100,-106 -100,-44 -52,-38" fill="none" stroke="{INK}" '
               f'stroke-width="9" stroke-linecap="round"/>')
    out.append(f'<path d="{JUG_BODY}" fill="#eef7fd"/>')
    if level > 0:
        top = -level
        out.append(f'<g clip-path="url(#{cid})"><path d="M-80,{top} q20,-7 40,0 t40,0 t40,0 t40,0 V10 H-80 Z" '
                   f'fill="{WATER}"/><path d="M-80,{top+18} q20,-6 40,0 t40,0 t40,0 t40,0" fill="none" '
                   f'stroke="#ffffff" stroke-opacity=".35" stroke-width="4"/></g>')
    if spoon:
        out.append(f'<path d="M14,-40 L60,-190" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>')
    out.append(f'<path d="{JUG_BODY}" fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    out.append(f'<path d="M-36,-120 L-34,-30" stroke="#ffffff" stroke-opacity=".7" stroke-width="7" stroke-linecap="round"/>')
    if mark:
        out.append(f'<path d="M20,-110 H50" stroke="{INK}" stroke-width="4"/>')
        for yy in (-90, -70, -50, -30):
            out.append(f'<path d="M36,{yy} H50" stroke="{INK}" stroke-width="3"/>')
    return g("".join(out), x, y, s, r)


def spoon(x, y, s=1, fill=0.0, color=PAPER, grains=None):
    """Teaspoon seen from above at an angle, bowl centre at (x, y); fill = 1 level, 0.5 half."""
    out = [f'<path d="M26,-2 Q52,-8 88,-26" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
           f'<path d="M26,-2 Q52,-8 88,-26" fill="none" stroke="#c5ccd6" stroke-width="3" stroke-linecap="round"/>']
    out.append(f'<ellipse cx="0" cy="0" rx="32" ry="17" fill="#c5ccd6" stroke="{INK}" stroke-width="{SW}"/>')
    out.append('<ellipse cx="0" cy="-2" rx="25" ry="11" fill="#8f9aab"/>')
    if fill > 0:
        cid = uid("sc")
        top = -13 + 24 * (1 - fill)
        out.append(f'<clipPath id="{cid}"><rect x="-40" y="{top}" width="80" height="30"/></clipPath>')
        out.append(f'<ellipse cx="0" cy="-2" rx="25" ry="11" fill="{color}" clip-path="url(#{cid})"/>')
        for gx, gy in (grains or []):
            if gy > top + 1:
                out.append(f'<circle cx="{gx}" cy="{gy}" r="1.8" fill="#7a8496"/>')
    out.append(f'<ellipse cx="0" cy="-2" rx="25" ry="11" fill="none" stroke="{INK}" stroke-width="2.5"/>')
    return g("".join(out), x, y, s)


def cube(cx, cy, s):
    k = 0.87 * s
    top = f"M{cx},{cy-s} L{cx+k},{cy-s/2} L{cx},{cy} L{cx-k},{cy-s/2} Z"
    left = f"M{cx-k},{cy-s/2} L{cx},{cy} L{cx},{cy+s} L{cx-k},{cy+s/2} Z"
    right = f"M{cx+k},{cy-s/2} L{cx},{cy} L{cx},{cy+s} L{cx+k},{cy+s/2} Z"
    st = f'stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"'
    return (f'<path d="{left}" fill="#e6e9ee" {st}/><path d="{right}" fill="#cfd5de" {st}/>'
            f'<path d="{top}" fill="#ffffff" {st}/>')


def sugar_cubes(x, y, s=1):
    c = cube(-26, 10, 26) + cube(26, 10, 26) + cube(0, -30, 26)
    return g(c, x, y, s)


def salt_shaker(x, y, s=1):
    out = [f'<path d="M-24,44 L-28,-6 Q-28,-22 -14,-26 L14,-26 Q28,-22 28,-6 L24,44 Q0,50 -24,44 Z" '
           f'fill="#ffffff" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>']
    out.append(f'<path d="M-22,-26 Q-22,-52 0,-52 Q22,-52 22,-26 Z" fill="#b9c2cf" stroke="{INK}" '
               f'stroke-width="{SW}" stroke-linejoin="round"/>')
    for hx, hy in ((-8, -38), (0, -44), (8, -38), (0, -33)):
        out.append(f'<circle cx="{hx}" cy="{hy}" r="2.6" fill="{INK}"/>')
    # salt inside (grey grains)
    out.append('<path d="M-25,20 L25,20 L24,44 Q0,50 -24,44 Z" fill="#dfe3e9"/>')
    for gx, gy in ((-14, 30), (-4, 36), (8, 28), (16, 38), (2, 26), (-12, 40)):
        out.append(f'<circle cx="{gx}" cy="{gy}" r="2" fill="#8a94a6"/>')
    out.append(f'<path d="M-24,44 L-28,-6 Q-28,-22 -14,-26 L14,-26 Q28,-22 28,-6 L24,44 Q0,50 -24,44 Z" '
               f'fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    return g("".join(out), x, y, s)


KID_SHAPES = [
    ("circle", dict(cx=0, cy=-100, r=40)),
    ("rect", dict(x=-46, y=-60, width=92, height=108, rx=34)),
    ("rect", dict(x=-40, y=26, width=32, height=100, rx=16)),
    ("rect", dict(x=8, y=26, width=32, height=100, rx=16)),
]


def _shape(kind, attrs, extra=""):
    a = " ".join(f'{k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f"<{kind} {a} {extra}/>"


def kid(x, y, s=1, level=0.3, happy=False, r=0):
    """A child drawn as a vessel of water. level = fraction of body filled."""
    arms = ([("rect", dict(x=-30, y=-80, width=26, height=84, rx=13, transform="rotate(40 -40 -40)")),
             ("rect", dict(x=4, y=-80, width=26, height=84, rx=13, transform="rotate(-40 40 -40)"))]
            if happy else
            [("rect", dict(x=-72, y=-50, width=26, height=84, rx=13, transform="rotate(8 -59 -50)")),
             ("rect", dict(x=46, y=-50, width=26, height=84, rx=13, transform="rotate(-8 59 -50)"))])
    if happy:
        arms = [("rect", dict(x=-74, y=-130, width=26, height=84, rx=13, transform="rotate(-28 -61 -50)")),
                ("rect", dict(x=48, y=-130, width=26, height=84, rx=13, transform="rotate(28 61 -50)"))]
    shapes = KID_SHAPES + arms
    cid = uid("kc")
    out = [f'<clipPath id="{cid}">' + "".join(_shape(k, a) for k, a in shapes) + "</clipPath>"]
    out += [_shape(k, a, f'fill="{INK}" stroke="{INK}" stroke-width="12" stroke-linejoin="round"') for k, a in shapes]
    out += [_shape(k, a, 'fill="#eef7fd"') for k, a in shapes]
    top_y = 126 - level * (126 + 140)
    out.append(f'<g clip-path="url(#{cid})"><path d="M-120,{top_y} q15,-8 30,0 t30,0 t30,0 t30,0 t30,0 t30,0 t30,0 t30,0 V140 H-120 Z" fill="{WATER}"/>'
               f'<path d="M-120,{top_y+16} q15,-6 30,0 t30,0 t30,0 t30,0 t30,0 t30,0 t30,0 t30,0" fill="none" stroke="#fff" stroke-opacity=".3" stroke-width="5"/></g>')
    # face
    if happy:
        out.append(f'<circle cx="-14" cy="-106" r="5.5" fill="{INK}"/><circle cx="14" cy="-106" r="5.5" fill="{INK}"/>')
        out.append(f'<path d="M-17,-88 Q0,-70 17,-88" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
        out.append('<circle cx="-24" cy="-92" r="6" fill="#ff8f8f" opacity=".55"/><circle cx="24" cy="-92" r="6" fill="#ff8f8f" opacity=".55"/>')
    else:
        # sunken, half-closed eyes and a frown
        for ex in (-14, 14):
            out.append(f'<circle cx="{ex}" cy="-104" r="10" fill="#c9ced8" opacity=".9"/>')
            out.append(f'<path d="M{ex-7},-105 Q{ex},-99 {ex+7},-105" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>')
        out.append(f'<path d="M-14,-78 Q0,-90 14,-78" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>')
    return g("".join(out), x, y, s, r)


def glass(x, y, s=1):
    body = "M-38,-110 L38,-110 L30,0 L-30,0 Z"
    cid = uid("gc")
    out = [f'<clipPath id="{cid}"><path d="{body}"/></clipPath>',
           f'<path d="{body}" fill="#eef7fd"/>',
           f'<g clip-path="url(#{cid})"><path d="M-50,-84 q12,-6 25,0 t25,0 t25,0 t25,0 V10 H-50 Z" fill="{WATER}"/></g>',
           f'<path d="{body}" fill="none" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>',
           f'<path d="M-30,-100 L-26,-14" stroke="#fff" stroke-opacity=".7" stroke-width="5" stroke-linecap="round"/>']
    return g("".join(out), x, y, s)


def cup(x, y, s=1, liquid=True):
    out = [f'<path d="M30,-38 C56,-38 56,-6 28,-8" fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round"/>',
           f'<path d="M-34,-50 L34,-50 L28,0 Q0,6 -28,0 Z" fill="#ffffff" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>']
    if liquid:
        out.append(f'<ellipse cx="0" cy="-50" rx="31" ry="6" fill="{WATER}" stroke="{INK}" stroke-width="3"/>')
    return g("".join(out), x, y, s)


def hand(x, y, s=1, r=0, skin=SKIN1, flip=False):
    fingers = [(-30, -64, 46), (-15, -76, 58), (0, -74, 56), (15, -62, 44)]
    out = []
    for fx, fy, fh in fingers:
        out.append(f'<rect x="{fx}" y="{fy}" width="15" height="{fh+20}" rx="7.5" fill="{skin}" stroke="{INK}" stroke-width="4"/>')
    out.append(f'<rect x="-30" y="-24" width="60" height="66" rx="20" fill="{skin}" stroke="{INK}" stroke-width="4"/>')
    out.append(f'<rect x="20" y="-34" width="15" height="48" rx="7.5" transform="rotate(38 27 14)" fill="{skin}" stroke="{INK}" stroke-width="4"/>')
    # hide seams between fingers and palm
    out.append(f'<rect x="-27" y="-21" width="54" height="30" rx="10" fill="{skin}"/>')
    sc = f"scale(-1 1)" if flip else ""
    return g(f'<g transform="{sc}">{"".join(out)}</g>', x, y, s, r)


def bubble(x, y, r):
    return (f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ffffff" fill-opacity=".85" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{x-r*0.45},{y-r*0.2} A{r*0.5},{r*0.5} 0 0 1 {x-r*0.1},{y-r*0.55}" fill="none" stroke="{WATER}" stroke-width="2.5" stroke-linecap="round"/>')


def flame(x, y, s=1):
    return g(f'<path d="M0,-44 C16,-24 22,-12 22,4 A22,22 0 0 1 -22,4 C-22,-10 -10,-20 0,-44 Z" fill="{ORANGE}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
             f'<path d="M0,-16 C8,-6 11,0 11,7 A11,11 0 0 1 -11,7 C-11,0 -6,-6 0,-16 Z" fill="#ffd34d"/>', x, y, s)


def steam(x, y, s=1, color="#9aa6b8"):
    return g("".join(f'<path d="M{dx},0 q-12,-14 0,-28 t0,-28" fill="none" stroke="{color}" stroke-width="5" stroke-linecap="round"/>'
                     for dx in (-20, 0, 20)), x, y, s)


def sun(x, y, s=1):
    rays = "".join(f'<line x1="0" y1="-30" x2="0" y2="-42" transform="rotate({a})" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
                   for a in range(0, 360, 45))
    return g(rays + f'<circle r="22" fill="#ffc83a" stroke="{INK}" stroke-width="{SW}"/>', x, y, s)


def moon(x, y, s=1):
    return g(f'<path d="M8,-26 A26,26 0 1 0 22,14 A20,20 0 1 1 8,-26 Z" fill="#cdd6f2" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>', x, y, s)


def cross_x(x, y, s=1, color=RED):
    return g(f'<path d="M-20,-20 L20,20 M20,-20 L-20,20" stroke="#fff" stroke-width="17" stroke-linecap="round"/>'
             f'<path d="M-20,-20 L20,20 M20,-20 L-20,20" stroke="{color}" stroke-width="10" stroke-linecap="round"/>', x, y, s)


def check(x, y, s=1, color=GREEN):
    return g(f'<path d="M-20,0 L-6,14 L22,-16" fill="none" stroke="#fff" stroke-width="17" stroke-linecap="round" stroke-linejoin="round"/>'
             f'<path d="M-20,0 L-6,14 L22,-16" fill="none" stroke="{color}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>', x, y, s)


# ---------------------------------------------------------------- panels (local 360x360)

def panel_wash():
    o = []
    # tap
    o.append(f'<path d="M110,40 H200 Q232,40 232,72 V86" fill="none" stroke="{INK}" stroke-width="22" stroke-linecap="round"/>'
             f'<path d="M110,40 H200 Q232,40 232,72 V86" fill="none" stroke="#b9c2cf" stroke-width="12" stroke-linecap="round"/>'
             f'<rect x="140" y="20" width="28" height="12" rx="5" fill="#b9c2cf" stroke="{INK}" stroke-width="4"/>')
    for i, dy in enumerate((112, 140, 168)):
        o.append(drop(232 - (i % 2) * 8, dy, 0.42))
    o.append(hand(150, 262, 1.0, 22, SKIN1))
    o.append(hand(230, 262, 1.0, -22, SKIN1, flip=True))
    for bx, by, br in ((112, 182, 11), (96, 214, 7), (270, 186, 9), (290, 214, 13), (188, 302, 8), (128, 318, 6), (262, 316, 7)):
        o.append(bubble(bx, by, br))
    # soap
    o.append(f'<rect x="38" y="300" width="64" height="34" rx="14" fill="#ff9fb3" stroke="{INK}" stroke-width="{SW}"/>'
             f'<path d="M52,310 H76" stroke="#fff" stroke-width="5" stroke-linecap="round" opacity=".8"/>')
    return "".join(o)


def panel_boil():
    o = []
    # pot over flames
    for fx in (76, 120, 164):
        o.append(flame(fx, 318, 0.9))
    o.append(f'<path d="M40,206 H52 M188,206 H200" stroke="{INK}" stroke-width="12" stroke-linecap="round"/>')
    o.append(f'<path d="M52,190 H188 V262 Q188,282 168,282 H72 Q52,282 52,262 Z" fill="#b9c2cf" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    o.append(f'<ellipse cx="120" cy="190" rx="68" ry="12" fill="{WATER}" stroke="{INK}" stroke-width="{SW}"/>')
    for bx, by, br in ((92, 189, 5), (126, 186, 6), (150, 192, 4)):
        o.append(f'<circle cx="{bx}" cy="{by}" r="{br}" fill="#cfe9fb" stroke="{INK}" stroke-width="2"/>')
    o.append(steam(120, 160, 1.0))
    # arrow -> cooled, covered jug
    o.append(arrow("M206,152 Q238,112 262,150"))
    o.append(jug(282, 320, 0.7, level=104))
    o.append(f'<rect x="240" y="207" width="80" height="12" rx="6" fill="{INK}"/>')
    return "".join(o)


def panel_litre():
    o = [jug(150, 335, 1.5, level=110, mark=True)]
    o.append(f'<path d="M228,170 H252" stroke="{INK}" stroke-width="4" stroke-dasharray="6 5"/>')
    o.append(text(258, 188, "1 L", 52, anchor="start"))
    return "".join(o)


def panel_sugar():
    o = [sugar_cubes(92, 92, 0.95)]
    o.append(text(150, 120, "×6", 74, anchor="start"))
    k = 0
    sug = [(-12, -4), (6, -6), (14, 1), (-4, 3), (-18, 1)]
    for row, yy in enumerate((182, 238, 294)):
        for xx in (62, 156):
            o.append(spoon(xx, yy, 0.82, fill=1, color="#ffffff", grains=sug))
            k += 1
    o.append(arrow("M248,190 Q274,182 282,222", width=6))
    o.append(jug(294, 336, 0.6, level=104))
    return "".join(o)


def panel_salt():
    grains = [(-14, 3), (-4, 6), (6, 2), (14, 4), (-8, 0), (2, -1), (18, 0), (-18, -1)]
    o = [salt_shaker(92, 98, 0.95)]
    o.append(text(150, 124, "×½", 74, anchor="start"))
    o.append(spoon(92, 236, 1.5, fill=0.5, color="#eef1f5", grains=grains))
    o.append(arrow("M222,214 Q256,196 268,226", width=6))
    o.append(jug(294, 336, 0.6, level=104))
    return "".join(o)


def panel_stir():
    o = [jug(180, 336, 1.35, level=118, spoon=True)]
    o.append(arrow("M70,214 A110,40 0 0 0 290,214", width=7))
    o.append(arrow("M290,150 A110,40 0 0 0 70,150", width=7))
    for sx, sy in ((150, 260), (196, 290), (176, 230)):
        o.append(f'<path d="M{sx-8},{sy} H{sx+8} M{sx},{sy-8} V{sy+8}" stroke="#ffffff" stroke-width="4" stroke-linecap="round"/>')
    return "".join(o)


def panel_sips():
    o = []
    # child (head + shoulders)
    o.append(f'<path d="M140,350 V300 Q140,250 210,250 Q280,250 280,300 V350 Z" fill="#f6c453" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    o.append(f'<circle cx="210" cy="172" r="66" fill="{SKIN2}" stroke="{INK}" stroke-width="{SW}"/>')
    o.append(f'<path d="M146,160 Q150,100 210,104 Q268,100 274,160 Q250,128 210,130 Q170,128 146,160 Z" fill="{INK}"/>')
    o.append(f'<circle cx="186" cy="168" r="6" fill="{INK}"/><circle cx="234" cy="168" r="6" fill="{INK}"/>')
    o.append(f'<ellipse cx="210" cy="204" rx="11" ry="9" fill="#5a1f1f" stroke="{INK}" stroke-width="3"/>')
    # spoon bringing a small sip
    o.append(g(f'<path d="M26,-1 Q60,0 120,14" fill="none" stroke="{INK}" stroke-width="8" stroke-linecap="round"/>'
               f'<path d="M-24,0 A24,12 0 0 0 24,0 Z" fill="{WATER}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>',
               160, 216, 1, 180))
    o.append(cup(70, 336, 1.05))
    # "again and again": repeat arrows + three little sips
    o.append(arrow("M48,150 A40,40 0 1 1 92,190", width=6))
    o.append(drop(64, 160, 0.42))
    o.append(drop(64, 160, 0.42))
    return "".join(o)


def panel_feed():
    o = []
    # mother
    o.append(f'<path d="M40,350 Q40,190 140,180 Q238,190 238,350 Z" fill="{GREEN}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    o.append(f'<circle cx="140" cy="122" r="46" fill="{SKIN1}" stroke="{INK}" stroke-width="{SW}"/>')
    o.append(f'<path d="M92,130 Q86,66 140,68 Q196,66 190,130 Q182,92 140,90 Q100,92 92,130 Z" fill="{INK}"/>')
    o.append(f'<path d="M124,130 Q130,136 136,130 M146,130 Q152,136 158,130" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    o.append(f'<path d="M126,148 Q140,158 154,148" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')
    # baby cradled at breast
    o.append(f'<path d="M96,250 Q150,214 226,236 Q238,262 210,276 Q150,290 104,282 Q84,270 96,250 Z" fill="#ffe6a8" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>')
    o.append(f'<circle cx="114" cy="234" r="26" fill="{SKIN3}" stroke="{INK}" stroke-width="{SW}"/>')
    o.append(f'<path d="M100,232 Q106,236 112,232" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>')
    # mother's arm
    o.append(f'<path d="M70,250 Q90,300 160,296 Q214,292 236,268" fill="none" stroke="{INK}" stroke-width="22" stroke-linecap="round"/>'
             f'<path d="M70,250 Q90,300 160,296 Q214,292 236,268" fill="none" stroke="{GREEN}" stroke-width="12" stroke-linecap="round"/>')
    # heart
    o.append(g(f'<path d="M0,12 C-30,-8 -22,-34 -6,-30 Q0,-28 0,-20 Q0,-28 6,-30 C22,-34 30,-8 0,12 Z" fill="{RED}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>', 214, 92, 1.2))
    # bowl of food
    o.append(steam(292, 252, 0.6))
    o.append(f'<path d="M248,266 H336 Q334,318 292,320 Q250,318 248,266 Z" fill="{ORANGE}" stroke="{INK}" stroke-width="{SW}" stroke-linejoin="round"/>'
             f'<ellipse cx="292" cy="266" rx="44" ry="9" fill="#fff3d6" stroke="{INK}" stroke-width="4"/>')
    return "".join(o)


def panel_day():
    o = []
    cx, cy, r = 180, 150, 82
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#f4f1ff" stroke="none"/>')
    o.append(arrow(f"M{cx-r*0.2},{cy-r*0.98} A{r},{r} 0 1 1 {cx-r*0.72},{cy-r*0.69}", width=7))
    o.append(sun(cx - 2, cy - r + 4, 0.75))
    o.append(moon(cx, cy + r - 2, 0.8))
    o.append(text(cx, cy + 18, "24h", 50))
    # old solution poured away, fresh made
    o.append(f'<path d="M58,286 q-8,24 0,52" stroke="{WATER}" stroke-width="8" fill="none" stroke-linecap="round"/>')
    o.append(jug(118, 330, 0.55, level=70, r=-50))
    o.append(cross_x(128, 250, 0.8))
    o.append(arrow("M168,300 H206", width=6))
    o.append(jug(268, 336, 0.6, level=104))
    o.append(check(310, 256, 0.8))
    return "".join(o)


# ---------------------------------------------------------------- warning-strip icons

def icon_blood(x, y):
    return drop(x, y, 1.25, fill=RED)


def icon_no_drink(x, y):
    return cup(x, y + 30, 1.1) + cross_x(x + 6, y - 6, 1.1)


def icon_sleepy(x, y):
    o = [f'<circle cx="0" cy="0" r="44" fill="{SKIN3}" stroke="{INK}" stroke-width="{SW}"/>',
         f'<path d="M-24,-2 Q-15,6 -6,-2 M6,-2 Q15,6 24,-2" fill="none" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
         f'<path d="M-8,22 H8" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
         text(52, -30, "z", 30), text(70, -54, "z", 22)]
    return g("".join(o), x, y)


def icon_vomit(x, y):
    # child vomiting repeatedly: face + outgoing splash, "×3"
    o = [f'<circle cx="-10" cy="0" r="40" fill="{SKIN1}" stroke="{INK}" stroke-width="{SW}"/>',
         f'<path d="M-30,-10 L-18,-4 M-2,-4 L10,-10" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>',
         f'<ellipse cx="2" cy="18" rx="9" ry="8" fill="#5a1f1f" stroke="{INK}" stroke-width="3"/>',
         f'<path d="M12,20 Q46,14 54,42 Q40,36 34,48 Q26,34 12,30 Z" fill="#b7c94a" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>']
    return g("".join(o), x, y)


def icon_fever(x, y):
    o = [f'<rect x="-11" y="-56" width="22" height="80" rx="11" fill="#ffffff" stroke="{INK}" stroke-width="{SW}"/>',
         f'<circle cx="0" cy="34" r="20" fill="{RED}" stroke="{INK}" stroke-width="{SW}"/>',
         f'<rect x="-5" y="-46" width="10" height="72" rx="5" fill="{RED}"/>',
         f'<circle cx="0" cy="34" r="14" fill="{RED}"/>']
    for ty in (-36, -22, -8, 6):
        o.append(f'<path d="M11,{ty} H20" stroke="{INK}" stroke-width="3"/>')
    o.append(f'<path d="M34,-40 l10,-10 l10,10 M44,-50 V-14" stroke="{RED}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
    return g("".join(o), x, y)


def clinic(x, y, s=1):
    o = [f'<path d="M-90,-40 L0,-110 L90,-40" fill="none" stroke="{INK}" stroke-width="12" stroke-linecap="round" stroke-linejoin="round"/>',
         f'<rect x="-74" y="-52" width="148" height="122" fill="#ffffff" stroke="{INK}" stroke-width="{SW}"/>',
         f'<rect x="-22" y="14" width="44" height="56" fill="{INK}" opacity=".85"/>',
         f'<circle cx="0" cy="-20" r="28" fill="{GREEN}" stroke="{INK}" stroke-width="4"/>',
         '<path d="M-6,-38 H6 V-26 H18 V-14 H6 V-2 H-6 V-14 H-18 V-26 H-6 Z" fill="#ffffff"/>',
         f'<rect x="-62" y="8" width="26" height="24" fill="#cfe9fb" stroke="{INK}" stroke-width="3"/>',
         f'<rect x="36" y="8" width="26" height="24" fill="#cfe9fb" stroke="{INK}" stroke-width="3"/>']
    return g("".join(o), x, y, s)


def warn_triangle(x, y, s=1):
    return g(f'<path d="M0,-52 L56,44 H-56 Z" fill="#ffc83a" stroke="{INK}" stroke-width="7" stroke-linejoin="round"/>'
             f'<rect x="-6" y="-20" width="12" height="40" rx="5" fill="{INK}"/><circle cx="0" cy="32" r="7" fill="{INK}"/>', x, y, s)


# ---------------------------------------------------------------- compose

def build():
    defs = (f'<defs>'
            f'<marker id="ah" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="22" markerHeight="22" markerUnits="userSpaceOnUse" orient="auto">'
            f'<path d="M0,0 L10,5 L0,10 Z" fill="{INK}"/></marker>'
            f'<marker id="ahO" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="22" markerHeight="22" markerUnits="userSpaceOnUse" orient="auto">'
            f'<path d="M0,0 L10,5 L0,10 Z" fill="{ORANGE}"/></marker>'
            f'</defs>')
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
           '<title>Home-made oral rehydration solution (ORS): 1 litre safe water + 6 level teaspoons sugar + half a level teaspoon salt</title>',
           defs, f'<rect width="{W}" height="{H}" fill="{BG}"/>']

    # header: dried-out child + ORS -> refilled child
    out.append(f'<rect x="30" y="30" width="1140" height="300" rx="34" fill="#e3f1fb" stroke="{INK}" stroke-width="4"/>')
    out.append(kid(200, 196, 0.9, level=0.22, happy=False, r=-6))
    for i, (dx, dy) in enumerate(((96, 298), (122, 312), (282, 304))):
        out.append(drop(dx, dy, 0.32))
    out.append(text(400, 214, "+", 110, weight=900))
    out.append(glass(560, 290, 1.25))
    out.append(text(568, 238, "ORS", 28, weight=900, fill="#ffffff"))
    out.append(f'<path d="M680,190 H800" stroke="{INK}" stroke-width="16" stroke-linecap="round"/>'
               f'<path d="M786,160 L836,190 L786,220 Z" fill="{INK}" stroke="{INK}" stroke-width="8" stroke-linejoin="round"/>')
    out.append(kid(1000, 196, 0.9, level=0.92, happy=True))

    # 3x3 grid of steps
    panels = [panel_wash, panel_boil, panel_litre, panel_sugar, panel_salt, panel_stir,
              panel_sips, panel_feed, panel_day]
    gx0, gy0, ps, gap = 30, 360, 360, 30
    for i, fn in enumerate(panels):
        col, row = i % 3, i // 3
        px, py = gx0 + col * (ps + gap), gy0 + row * (ps + gap)
        cid = uid("pc")
        inner = (f'<clipPath id="{cid}"><rect width="{ps}" height="{ps}" rx="28"/></clipPath>'
                 f'<rect width="{ps}" height="{ps}" rx="28" fill="{PAPER}"/>'
                 f'<g clip-path="url(#{cid})">{fn()}</g>'
                 f'<rect width="{ps}" height="{ps}" rx="28" fill="none" stroke="{INK}" stroke-width="4"/>'
                 f'<circle cx="38" cy="38" r="25" fill="{INK}"/>' + text(38, 49, str(i + 1), 31, fill="#ffffff"))
        out.append(g(inner, px, py))
        # flow arrows between neighbours in a row
        if col < 2:
            ax = px + ps + 2
            out.append(f'<path d="M{ax},{py+ps/2-12} l{gap-4},12 l-{gap-4},12 Z" fill="{ORANGE}"/>')

    # danger strip: any of these -> go to a health worker now
    sy = gy0 + 3 * (ps + gap)
    out.append(f'<rect x="30" y="{sy}" width="1140" height="250" rx="34" fill="#fde3d6" stroke="{RED}" stroke-width="6"/>')
    cy = sy + 125
    out.append(warn_triangle(110, cy + 4, 1.0))
    icons = [icon_blood, icon_no_drink, icon_vomit, icon_sleepy, icon_fever]
    for k, fn in enumerate(icons):
        ix = 240 + k * 118
        out.append(f'<circle cx="{ix}" cy="{cy}" r="56" fill="#ffffff" stroke="{INK}" stroke-width="3"/>')
        out.append(g(fn(0, 0), ix, cy, 0.8))
    out.append(arrow(f"M{240+4*118+70},{cy} H{240+4*118+170}", color=RED, width=14))
    out.append(f'<path d="M{240+4*118+160},{cy-22} l26,22 l-26,22" fill="none" stroke="{RED}" stroke-width="14" stroke-linecap="round" stroke-linejoin="round"/>')
    out.append(clinic(1040, cy + 20, 0.95))

    # footer
    fy = sy + 290
    out.append(text(W / 2, fy, "1 L safe water  +  6 level teaspoons sugar  +  ½ level teaspoon salt", 34, weight=800))
    out.append(text(W / 2, fy + 44, "Oral rehydration solution · WHO / UNICEF home recipe · Saves children from diarrhoea", 23, weight=500, fill="#4b5675"))
    out.append(text(W / 2, fy + 78, "No copyright — print it, copy it, paint it on a wall.", 21, weight=500, fill="#4b5675"))
    out.append("</svg>")
    return "\n".join(out)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(root, "output"), exist_ok=True)
    path = os.path.join(root, "output", "ors.svg")
    with open(path, "w", encoding="utf-8") as f:
        f.write(build())
    print("wrote", path, os.path.getsize(path), "bytes")
