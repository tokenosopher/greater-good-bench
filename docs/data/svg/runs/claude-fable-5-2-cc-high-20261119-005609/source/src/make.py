#!/usr/bin/env python3
"""Before Help Arrives -- a wordless first-aid poster, generated as one SVG.

Six cards. Each reads top to bottom (a direction shared by every script):
  top, warm  = what you see        bottom, cool = what you do
Navy = the person in trouble, red = the danger, green = you, blue = water.
Only numerals and SI unit symbols are used, no words in any language.
"""
import math, os

NAVY, RED, GREEN, BLUE = "#1B2A4E", "#E5383B", "#0C9A68", "#2B95D9"
CORAL, MINT, PAGE, WHITE = "#FDE3DB", "#E4F4EB", "#141D36", "#FFFFFF"
ORANGE = "#FFB02E"
FONT = "'Helvetica Neue',Helvetica,Arial,'Liberation Sans',sans-serif"

CW, CH, TZ = 540, 700, 250          # card width, height, top-zone height
GAP, M = 30, 60


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def pts(p):
    return " ".join(f"{f(x)},{f(y)}" for x, y in p)


def line(p, w, col, extra=""):
    return (f'<polyline points="{pts(p)}" fill="none" stroke="{col}" stroke-width="{f(w)}" '
            f'stroke-linecap="round" stroke-linejoin="round" {extra}/>')


def hl(p, w, col, bg, h=5):
    """limb with a halo in the background colour so overlaps stay legible"""
    return line(p, w + 2 * h, bg) + line(p, w, col)


def circ(x, y, r, col, extra=""):
    return f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="{col}" {extra}/>'


def hcirc(x, y, r, col, bg, h=5):
    return circ(x, y, r + h, bg) + circ(x, y, r, col)


def path(d, fill="none", stroke=None, w=0, extra=""):
    s = f'<path d="{d}" fill="{fill}" '
    if stroke:
        s += f'stroke="{stroke}" stroke-width="{f(w)}" stroke-linecap="round" stroke-linejoin="round" '
    return s + extra + "/>"


def text(x, y, s, size, col=NAVY, anchor="middle", weight=700, extra=""):
    return (f'<text x="{f(x)}" y="{f(y)}" font-family="{FONT}" font-size="{size}" font-weight="{weight}" '
            f'fill="{col}" text-anchor="{anchor}" {extra}>{s}</text>')


def arrow(x1, y1, x2, y2, w, col, hs=None):
    hs = hs or w * 2.6
    a = math.atan2(y2 - y1, x2 - x1)
    bx, by = x2 - math.cos(a) * hs * 0.9, y2 - math.sin(a) * hs * 0.9
    px, py = -math.sin(a) * hs * 0.75, math.cos(a) * hs * 0.75
    tri = [(x2 + math.cos(a) * hs * 0.35, y2 + math.sin(a) * hs * 0.35), (bx + px, by + py), (bx - px, by - py)]
    return (line([(x1, y1), (bx, by)], w, col) +
            f'<polygon points="{pts(tri)}" fill="{col}" stroke="{col}" stroke-width="{f(w*0.5)}" stroke-linejoin="round"/>')


def drop(x, y, s, col, extra=""):
    d = (f"M{f(x)},{f(y-s)} C{f(x+.2*s)},{f(y-.45*s)} {f(x+.72*s)},{f(y)} {f(x+.72*s)},{f(y+.38*s)} "
         f"A{f(.72*s)},{f(.72*s)} 0 0 1 {f(x-.72*s)},{f(y+.38*s)} C{f(x-.72*s)},{f(y)} {f(x-.2*s)},{f(y-.45*s)} {f(x)},{f(y-s)}Z")
    return path(d, col, extra=extra)


def heart(x, y, s, col):
    d = "M0,-.3 C-.3,-.85 -1.1,-.6 -1.1,0 C-1.1,.5 -.45,.85 0,1.2 C.45,.85 1.1,.5 1.1,0 C1.1,-.6 .3,-.85 0,-.3Z"
    return f'<g transform="translate({f(x)},{f(y)}) scale({f(s)})">{path(d, col)}</g>'


def hand(x, y, ang, s, col, bg, arm=0, armw=46, tips=None, tipop=1):
    """mitten hand seen flat; wrist at (x,y), fingers pointing along `ang` degrees"""
    g = f'<g transform="translate({f(x)},{f(y)}) rotate({f(ang)}) scale({f(s)})">'
    if arm:
        g += line([(-arm, 0), (12, 0)], armw, col)
    g += line([(26, -18), (56, -47)], 22, col)
    g += f'<rect x="0" y="-28" width="106" height="56" rx="25" fill="{col}"/>'
    if tips:
        g += path("M58,-28 H81 A25,25 0 0 1 106,-3 V3 A25,25 0 0 1 81,28 H58Z", tips, extra=f'opacity="{tipop}"')
    for yy in (-14, 0, 14):
        g += line([(66, yy), (104, yy)], 3.2, bg)
    return g + "</g>"


def phone(x, y, r, bg, ring=True):
    """the green call button found on every phone"""
    s = r / 44
    g = f'<g transform="translate({f(x)},{f(y)})">'
    if ring:
        for i, rr in enumerate((r + 14, r + 30)):
            a0, a1 = math.radians(-70), math.radians(-20)
            d = (f"M{f(rr*math.cos(a0))},{f(rr*math.sin(a0))} "
                 f"A{f(rr)},{f(rr)} 0 0 1 {f(rr*math.cos(a1))},{f(rr*math.sin(a1))}")
            anim = (f'<animate attributeName="opacity" values="1;1;.15;1" keyTimes="0;.5;.75;1" '
                    f'dur="1.6s" begin="{0.2*i}s" repeatCount="indefinite"/>')
            g += (f'<path d="{d}" fill="none" stroke="{GREEN}" stroke-width="{f(7*s)}" '
                  f'stroke-linecap="round">{anim}</path>')
    g += circ(0, 0, r, GREEN)
    g += f'<g transform="rotate(-135) scale({f(s)}) translate(0,-3)">'
    g += path("M-24,4 Q0,-17 24,4", "none", WHITE, 12)
    g += line([(-27, 3), (-22, 14)], 17, WHITE) + line([(27, 3), (22, 14)], 17, WHITE)
    return g + "</g></g>"


def clock(x, y, r, wedge=None, wcol=BLUE, hands=True):
    g = circ(x, y, r, WHITE)
    if wedge:
        a = math.radians(wedge * 6 - 90)
        rr = r - 4
        g += path(f"M{f(x)},{f(y)} L{f(x)},{f(y-rr)} A{f(rr)},{f(rr)} 0 0 1 "
                  f"{f(x+rr*math.cos(a))},{f(y+rr*math.sin(a))}Z", wcol)
    g += f'<circle cx="{f(x)}" cy="{f(y)}" r="{f(r)}" fill="none" stroke="{NAVY}" stroke-width="{f(r*.17)}"/>'
    for k in range(12):
        a = math.radians(k * 30)
        g += line([(x + (r * .72) * math.sin(a), y - (r * .72) * math.cos(a)),
                   (x + (r * .78) * math.sin(a), y - (r * .78) * math.cos(a))], r * .07, NAVY)
    if hands:
        if wedge:
            a = math.radians(wedge * 6 - 90)
            g += line([(x, y), (x, y - r * .62)], r * .11, NAVY)
            g += line([(x, y), (x + r * .62 * math.cos(a), y + r * .62 * math.sin(a))], r * .11, NAVY)
        else:
            g += line([(x, y), (x, y - r * .6)], r * .11, NAVY) + line([(x, y), (x + r * .4, y + r * .12)], r * .11, NAVY)
        g += circ(x, y, r * .1, NAVY)
    return g


def person(col, bg, head, torso, limbs, hr=20, tw=30, lw=18, h=5):
    """torso: list of points; limbs: list of point-lists; head: (x,y)"""
    g = ""
    for l in limbs:
        g += hl(l, lw, col, bg, h)
    g += hl(torso, tw, col, bg, h)
    g += hcirc(head[0], head[1], hr, col, bg, h)
    return g


# ---------------------------------------------------------------- cards
def card_cpr():
    bg = CORAL
    top = line([(60, 208), (480, 208)], 4, NAVY, 'opacity=".18"')
    # heartbeat that stops
    top += heart(104, 82, 30, RED)
    top += line([(160, 88), (196, 88), (208, 68), (224, 120), (243, 34), (260, 106), (270, 88), (470, 88)], 7, RED)
    # collapsed person
    top += line([(288, 188), (410, 190)], 24, NAVY) + line([(410, 190), (415, 168)], 17, NAVY)
    top += line([(170, 186), (288, 186)], 36, NAVY) + circ(128, 182, 21, NAVY)
    top += line([(119, 176), (129, 186)], 4, bg) + line([(129, 176), (119, 186)], 4, bg)

    bg = MINT
    b = phone(92, 338, 42, bg)
    b += text(506, 336, "100–120", 50, anchor="end")
    b += text(506, 374, "/ min", 32, anchor="end", weight=600)
    b += (f'<circle cx="284" cy="319" r="11" fill="{GREEN}">'
          f'<animate attributeName="r" values="11;17;11" keyTimes="0;.35;1" dur="0.545s" repeatCount="indefinite"/></circle>')
    b += line([(40, 646), (500, 646)], 4, NAVY, 'opacity=".18"')
    # victim
    b += line([(276, 624), (420, 626)], 24, NAVY) + line([(420, 626), (425, 603)], 17, NAVY)
    b += line([(150, 622), (276, 622)], 38, NAVY) + circ(108, 618, 21, NAVY)
    # rescuer: lower legs stay, the rest rocks from the hips at 110 pushes a minute
    b += hl([(282, 634), (372, 636)], 22, GREEN, bg)
    b += hl([(282, 634), (308, 552)], 24, GREEN, bg)
    up = hl([(214, 470), (212, 596)], 18, GREEN, bg)
    up += hl([(308, 552), (216, 466)], 34, GREEN, bg)
    up += hcirc(192, 430, 21, GREEN, bg)
    b += (f'<g>{up}<animateTransform attributeName="transform" type="rotate" '
          f'values="0 308 552;-4.5 308 552;0 308 552" keyTimes="0;.38;1" calcMode="spline" '
          f'keySplines=".3 0 .6 1;.3 0 .6 1" dur="0.545s" repeatCount="indefinite"/></g>')
    b += arrow(150, 520, 150, 578, 9, GREEN)
    b += text(128, 540, "5–6", 34, anchor="end") + text(128, 574, "cm", 30, anchor="end", weight=600)
    return top, b, "Someone collapses and is not breathing: call for help, then push hard on the centre of the chest, 5 to 6 cm deep, 100 to 120 times a minute."


def card_choke():
    bg = CORAL
    top = path("M150,260 L150,212 Q150,166 204,160 L336,160 Q390,166 390,212 L390,260Z", NAVY)
    top += line([(270, 118), (270, 160)], 34, NAVY)
    top += circ(270, 84, 44, NAVY)
    top += line([(244, 70), (256, 76), (244, 82)], 5, bg) + line([(296, 70), (284, 76), (296, 82)], 5, bg)
    top += f'<ellipse cx="270" cy="103" rx="11" ry="13" fill="{bg}"/>' + circ(270, 106, 6.5, RED)
    top += hl([(178, 260), (190, 232), (258, 150)], 27, NAVY, bg, 5)
    top += hl([(362, 260), (350, 232), (282, 150)], 27, NAVY, bg, 5)
    for sx in (-1, 1):
        for a, r0, r1 in ((-18, 62, 82), (8, 64, 86), (34, 62, 82)):
            ra = math.radians(a)
            top += line([(270 + sx * r0 * math.cos(ra), 100 + r0 * math.sin(ra) - 10),
                         (270 + sx * r1 * math.cos(ra), 100 + r1 * math.sin(ra) - 10)], 7, RED)

    bg = MINT
    b = text(140, 352, "5×", 56) + text(404, 352, "5×", 56)
    b += path("M232,322 Q272,300 312,322", "none", GREEN, 7) + \
        f'<polygon points="324,330 300,326 314,308" fill="{GREEN}"/>'
    b += path("M312,352 Q272,374 232,352", "none", GREEN, 7) + \
        f'<polygon points="220,344 244,348 230,366" fill="{GREEN}"/>'
    b += line([(30, 652), (510, 652)], 4, NAVY, 'opacity=".18"')
    # --- back blows
    b += person(GREEN, bg, (214, 410), [(216, 450), (228, 536)],
                [[(228, 536), (240, 640)], [(228, 536), (212, 640)]])
    b += person(NAVY, bg, (68, 448), [(96, 472), (160, 536)],
                [[(160, 536), (172, 640)], [(160, 536), (150, 640)], [(100, 480), (96, 536)]])
    b += hl([(216, 450), (180, 434), (137, 470)], 18, GREEN, bg)
    for ang in (-88, -122, -156):
        ra = math.radians(ang)
        b += line([(128 + 22 * math.cos(ra), 462 + 22 * math.sin(ra)),
                   (128 + 40 * math.cos(ra), 462 + 40 * math.sin(ra))], 7, RED)
    # --- abdominal thrusts
    b += person(GREEN, bg, (440, 408), [(434, 448), (448, 536)],
                [[(448, 536), (462, 640)], [(448, 536), (438, 640)]])
    b += person(NAVY, bg, (380, 412), [(384, 450), (392, 536)],
                [[(392, 536), (402, 640)], [(392, 536), (378, 640)]])
    b += hl([(434, 450), (430, 512), (368, 510)], 18, GREEN, bg)
    b += hcirc(366, 510, 12, GREEN, bg, 4)
    b += arrow(314, 548, 342, 523, 9, GREEN)
    b += circ(318, 398, 9, RED) + line([(336, 404), (348, 408)], 5, RED) + line([(334, 392), (346, 392)], 5, RED)
    return top, b, "Someone is choking and cannot breathe or speak: give 5 hard blows between the shoulder blades, then 5 inward-and-upward thrusts above the navel, and repeat."


def card_bleed():
    bg = CORAL
    top = line([(-40, 112), (322, 112)], 66, NAVY) + hand(318, 112, 0, 1.22, NAVY, bg)
    top += line([(160, 92), (206, 132)], 22, bg) + line([(160, 92), (206, 132)], 12, RED)
    top += drop(170, 178, 20, RED) + drop(212, 212, 14, RED) + drop(140, 222, 10, RED)

    bg = MINT
    b = line([(-40, 520), (322, 520)], 66, NAVY) + hand(318, 520, 0, 1.22, NAVY, bg)
    b += f'<rect x="106" y="444" width="160" height="152" rx="18" fill="{WHITE}" stroke="{NAVY}" stroke-width="6"/>'
    ang = 104
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    s = 1.12
    wx, wy = 186 - 56 * s * ca, 520 - 56 * s * sa
    b += hand(wx, wy, ang, s, GREEN, bg, arm=150, armw=44)
    b += arrow(64, 350, 64, 420, 11, GREEN) + arrow(336, 372, 336, 430, 11, GREEN)
    b += phone(440, 348, 42, bg)
    b += clock(440, 632, 34, wedge=10, wcol=GREEN)
    b += text(386, 645, "10+", 34, anchor="end") 
    b += text(386, 676, "min", 26, anchor="end", weight=600)
    return top, b, "Heavy bleeding: press a clean cloth firmly on the wound and keep pressing without letting go, for ten minutes or more, and call for help."


def card_stroke():
    bg = CORAL
    # face drooping on one side
    top = circ(100, 112, 60, NAVY)
    top += circ(78, 96, 7, bg) + line([(112, 97), (130, 103)], 7, bg)
    top += path("M68,128 Q88,146 104,134 Q120,124 134,152", "none", bg, 7)
    top += arrow(176, 104, 176, 150, 8, RED)
    # one arm cannot stay up
    top += line([(284, 112), (284, 200)], 44, NAVY) + circ(284, 62, 24, NAVY)
    top += hl([(270, 108), (214, 104)], 19, NAVY, bg) + hl([(298, 108), (338, 132), (346, 178)], 19, NAVY, bg)
    top += arrow(372, 120, 372, 166, 8, RED)
    # speech comes out scrambled
    top += path("M408,58 h70 a18,18 0 0 1 18,18 v48 a18,18 0 0 1 -18,18 h-34 l-26,26 v-26 h-10 "
                "a18,18 0 0 1 -18,-18 v-48 a18,18 0 0 1 18,-18Z", WHITE, NAVY, 7)
    top += path("M408,112 q8,-34 18,-8 q6,22 14,-14 q4,-18 12,4 q10,30 8,-20 q10,-12 18,26", "none", RED, 6)

    bg = MINT
    b = phone(160, 392, 66, bg)
    b += clock(398, 392, 56)
    for yy, x0 in ((362, 300), (392, 286), (422, 300)):
        b += line([(x0, yy), (x0 + 22, yy)], 7, GREEN)
    # ambulance
    b += line([(40, 652), (500, 652)], 4, NAVY, 'opacity=".18"')
    for yy, x0, x1 in ((552, 92, 140), (584, 70, 140), (616, 100, 140)):
        b += line([(x0, yy), (x1, yy)], 7, GREEN)
    b += path("M166,512 h150 a12,12 0 0 1 12,12 v100 h-174 v-100 a12,12 0 0 1 12,-12Z", WHITE, NAVY, 8)
    b += path("M328,548 h46 q10,0 16,10 l22,36 q4,6 4,14 v16 h-88Z", WHITE, NAVY, 8)
    b += path("M342,562 h28 l20,32 h-48Z", NAVY)
    b += f'<rect x="232" y="486" width="26" height="26" rx="6" fill="{RED}"/>'
    for dx, dy in ((-.8, -.6), (0, -1), (.8, -.6)):
        b += line([(245 + dx * 24, 494 + dy * 24), (245 + dx * 38, 494 + dy * 38)], 6, RED)
    b += f'<rect x="228" y="538" width="24" height="68" rx="4" fill="{GREEN}"/>' \
         f'<rect x="206" y="560" width="68" height="24" rx="4" fill="{GREEN}"/>'
    for cx in (206, 362):
        b += circ(cx, 628, 27, NAVY) + circ(cx, 628, 10, WHITE)
    return top, b, "Signs of a stroke: one side of the face droops, one arm cannot stay raised, speech is slurred or confused. Call an ambulance immediately; every minute counts."


def spoon(x, y, fill=1.0, s=1.0):
    """teaspoon seen from above: white = filled, shaded = empty"""
    g = f'<g transform="translate({f(x)},{f(y)}) scale({f(s)})">'
    g += line([(0, 18), (0, 56)], 6, NAVY) + line([(0, 46), (0, 57)], 10, NAVY)
    g += f'<ellipse cx="0" cy="0" rx="15" ry="20" fill="{WHITE}" stroke="{NAVY}" stroke-width="6"/>'
    if fill < 1:
        g += path("M-12,0 A12,17 0 0 1 12,0Z", "#9FB2C4")
        g += line([(-12, 0), (12, 0)], 3, NAVY)
    return g + "</g>"


def card_ors():
    bg = CORAL
    ox = -50
    top = f'<rect x="{128+ox}" y="96" width="34" height="76" rx="8" fill="{WHITE}" stroke="{NAVY}" stroke-width="7"/>'
    top += path(f"M{162+ox},162 L{290+ox},162 Q{288+ox},204 {252+ox},212 L{252+ox},228 L{206+ox},228 L{206+ox},212 "
                f"Q{170+ox},200 {162+ox},162Z", WHITE, NAVY, 7)
    top += person(NAVY, bg, (268 + ox, 50), [(256 + ox, 88), (232 + ox, 146)],
                  [[(232 + ox, 148), (302 + ox, 150), (304 + ox, 222), (326 + ox, 224)]], hr=21, tw=32, lw=21)
    top += hl([(258 + ox, 92), (250 + ox, 132), (282 + ox, 128)], 16, NAVY, bg, 4)
    top += drop(370, 96, 34, RED) + drop(438, 150, 24, RED) + drop(376, 186, 16, RED)
    top += drop(464, 74, 12, RED)

    bg = MINT
    b = ""
    # 1 litre of clean water
    b += f'<rect x="70" y="300" width="52" height="24" rx="7" fill="{NAVY}"/>'
    b += path("M78,324 h36 v24 q34,10 34,44 v118 a16,16 0 0 1 -16,16 h-72 a16,16 0 0 1 -16,-16 v-118 q0,-34 34,-44Z", WHITE, NAVY, 7)
    b += path("M51.5,400 q22,-10 44,0 t49,0 v108 a14,14 0 0 1 -14,14 h-65 a14,14 0 0 1 -14,-14Z", BLUE)
    b += text(96, 482, "1 L", 40, WHITE)
    for sx, sy, ss in ((30, 338, 9), (162, 320, 12)):
        b += path(f"M{sx},{sy-ss} Q{sx},{sy} {sx+ss},{sy} Q{sx},{sy} {sx},{sy+ss} Q{sx},{sy} {sx-ss},{sy} Q{sx},{sy} {sx},{sy-ss}Z", BLUE)
    b += text(196, 450, "+", 54)
    # 6 level teaspoons of sugar
    for cx, cy in ((270, 344), (306, 344), (288, 314)):
        b += f'<rect x="{cx-17}" y="{cy-15}" width="34" height="30" rx="5" fill="{WHITE}" stroke="{NAVY}" stroke-width="6"/>'
    for r in range(2):
        for c in range(3):
            b += spoon(246 + c * 42, 400 + r * 72, s=.9)
    b += text(288, 574, "6", 56)
    b += text(382, 450, "+", 54)
    # half a level teaspoon of salt
    b += path("M440,364 l6,-40 h36 l6,40Z", WHITE, NAVY, 6)
    b += path("M444,324 q20,-36 40,0Z", NAVY, NAVY, 6)
    for dx, dy in ((-9, 0), (0, -8), (9, 0)):
        b += circ(464 + dx, 314 + dy, 2.6, WHITE)
    for dx, dy in ((-8, 0), (0, 8), (8, 0)):
        b += circ(464 + dx, 342 + dy, 2.6, NAVY)
    b += spoon(464, 436, fill=.5, s=.9)
    b += text(464, 574, "½", 56)
    # stir, then small sips, again and again
    b += path("M150,612 h60 l-7,62 h-46Z", WHITE, NAVY, 6) + path("M156,634 h48 l-4,37 h-40Z", BLUE)
    b += line([(196, 596), (176, 660)], 7, NAVY)
    b += arrow(238, 644, 286, 644, 9, GREEN)
    b += path("M356,712 Q356,682 388,678 L436,678 Q468,682 468,712Z", NAVY)
    b += circ(412, 640, 28, NAVY) + line([(412, 660), (412, 680)], 22, NAVY)
    b += hl([(318, 704), (352, 668)], 16, GREEN, bg, 4)
    b += f'<g transform="rotate(28 362 646)">' + path("M344,628 h38 l-5,36 h-28Z", WHITE, NAVY, 5) + \
         path("M348,644 h30 l-3,18 h-24Z", BLUE) + '</g>'
    return top, b, "Diarrhoea drains the body of water and kills by dehydration: stir 6 level teaspoons of sugar and half a level teaspoon of salt into 1 litre of clean water, and give it in frequent small sips."


def card_burn():
    bg = CORAL
    fl = ("M0,-1 C.1,-.55 .72,-.3 .72,.3 C.72,.75 .38,1 0,1 C-.38,1 -.72,.75 -.72,.3 "
          "C-.72,.02 -.58,-.18 -.44,-.38 C-.4,-.12 -.3,0 -.18,.04 C-.3,-.4 -.22,-.75 0,-1Z")
    top = f'<g transform="translate(128,122) scale(84)">{path(fl, RED)}</g>'
    top += f'<g transform="translate(128,150) scale(50)">{path(fl, ORANGE)}</g>'
    top += hand(432, 124, 180, 1.22, NAVY, bg, arm=160, armw=42, tips=RED)
    for a in (150, 180, 210):
        ra = math.radians(a)
        top += line([(318 + 34 * math.cos(ra), 124 + 46 * math.sin(ra)),
                     (318 + 54 * math.cos(ra), 124 + 74 * math.sin(ra))], 7, RED)

    bg = MINT
    # cool running water
    X, Y = 208, 560
    b = line([(X, 404), (X, 672)], 30, BLUE)
    for dx, dy, s in ((-52, 78, 11), (50, 88, 12), (-76, 116, 8), (80, 124, 8)):
        b += drop(X + dx, Y + dy, s, BLUE)
    b += hand(312, Y, 180, 1.22, NAVY, bg, arm=240, armw=42, tips=RED, tipop=.6)
    b += line([(X, 404), (X, Y - 28)], 30, BLUE)
    b += path(f"M{X-38},{Y-26} q38,-26 76,0", "none", BLUE, 9) + path(f"M{X-50},{Y-8} q-20,-4 -30,-22", "none", BLUE, 8) + \
        path(f"M{X+50},{Y-8} q20,-4 30,-22", "none", BLUE, 8)
    b += path(f"M-20,332 H{X-46} Q{X},332 {X},376 V392", "none", NAVY, 38)
    b += line([(110, 290), (110, 316)], 16, NAVY) + line([(78, 286), (142, 286)], 16, NAVY)
    b += f'<rect x="{X-22}" y="388" width="44" height="16" rx="5" fill="{NAVY}"/>'
    b += clock(410, 366, 56, wedge=20)
    b += text(410, 482, "20 min", 46)
    return top, b, "A burn: hold it under cool running water for 20 minutes, as soon as possible."


def build():
    cards = [card_cpr, card_choke, card_bleed, card_stroke, card_ors, card_burn]
    W = 2 * M + 3 * CW + 2 * GAP
    H = 2 * M + 2 * CH + GAP
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         f'role="img" aria-labelledby="t d">',
         '<title id="t">Before Help Arrives</title>',
         '<desc id="d">A wordless first-aid poster of six cards. Each card shows an emergency on top and, '
         'below the arrow, what anyone can do about it. Navy is the person in trouble, red the danger, '
         'green is you.</desc>',
         '<defs>',
         f'<clipPath id="card"><rect width="{CW}" height="{CH}" rx="40"/></clipPath>',
         f'<clipPath id="top"><rect width="{CW}" height="{TZ}"/></clipPath>',
         f'<clipPath id="bot"><rect y="{TZ}" width="{CW}" height="{CH-TZ}"/></clipPath>',
         '</defs>',
         f'<rect width="{W}" height="{H}" fill="{PAGE}"/>']
    for i, fn in enumerate(cards):
        x = M + (i % 3) * (CW + GAP)
        y = M + (i // 3) * (CH + GAP)
        top, bot, desc = fn()
        o.append(f'<g transform="translate({x},{y})" role="group" aria-label="{desc}"><title>{desc}</title>')
        o.append('<g clip-path="url(#card)">')
        o.append(f'<rect width="{CW}" height="{TZ}" fill="{CORAL}"/>')
        o.append(f'<rect y="{TZ}" width="{CW}" height="{CH-TZ}" fill="{MINT}"/>')
        o.append(f'<g clip-path="url(#top)">{top}</g>')
        o.append(f'<g clip-path="url(#bot)">{bot}</g>')
        o.append('</g>')
        o.append(circ(CW / 2, TZ, 33, PAGE) + circ(CW / 2, TZ, 27, WHITE))
        o.append(line([(CW / 2, TZ - 12), (CW / 2, TZ + 10)], 7, PAGE) +
                 line([(CW / 2 - 11, TZ + 1), (CW / 2, TZ + 12), (CW / 2 + 11, TZ + 1)], 7, PAGE))
        o.append('</g>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    out = os.path.join(here, "..", "output", "before-help-arrives.svg")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(build())
    print("wrote", os.path.normpath(out), os.path.getsize(out), "bytes")
