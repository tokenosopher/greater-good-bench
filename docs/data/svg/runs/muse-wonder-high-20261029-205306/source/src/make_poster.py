#!/usr/bin/env python3
"""Generate 'WE SHARE ONE HOME' — a universal, pictographic poster as SVG."""
import math, os

W, H = 1080, 1350
OUT = os.path.join(os.path.dirname(__file__), "..", "output", "one-home.svg")

def person(x, ground, h, skin, clothes, accent, kind="adult"):
    """A simple, warm figure standing on `ground`, total height h."""
    head_r = max(13, h * 0.11)
    head_cy = ground - h + head_r
    body_top = head_cy + head_r + 6
    s = []
    if kind == "wheelchair":
        bw = 36
        wy = ground - 34
        s.append(f'<circle cx="{x+6}" cy="{wy}" r="31" fill="none" stroke="#EAF6FF" stroke-width="7"/>')
        s.append(f'<circle cx="{x+6}" cy="{wy}" r="5" fill="#EAF6FF"/>')
        s.append(f'<path d="M {x} {body_top+52} L {x+36} {ground-58} L {x+40} {ground-16}" stroke="{accent}" stroke-width="11" stroke-linecap="round" stroke-linejoin="round" fill="none"/>')
        s.append(f'<rect x="{x-bw/2}" y="{body_top}" width="{bw}" height="62" rx="14" fill="{clothes}"/>')
        s.append(f'<circle cx="{x}" cy="{head_cy}" r="{head_r}" fill="{skin}"/>')
        s.append(f'<path d="M {x-head_r} {head_cy-3} A {head_r} {head_r} 0 1 1 {x+head_r} {head_cy-3} Z" fill="{accent}"/>')
        sy = body_top + 16
        return "".join(s), (x-bw/2, sy, skin), (x+bw/2, sy, skin)
    if kind == "child":
        bw = 30
        s.append(f'<rect x="{x-bw/2}" y="{body_top}" width="{bw}" height="{ground-body_top-24}" rx="13" fill="{clothes}"/>')
        s.append(f'<path d="M {x-bw/2+5} {ground-26} L {x-bw/2+3} {ground} M {x+bw/2-5} {ground-26} L {x+bw/2-3} {ground}" stroke="{accent}" stroke-width="9" stroke-linecap="round"/>')
    elif kind in ("dress", "hijab"):
        bw = 34
        s.append(f'<path d="M {x} {body_top-8} L {x+32} {ground} L {x-32} {ground} Z" fill="{clothes}"/>')
        s.append(f'<rect x="{x-17}" y="{body_top-8}" width="34" height="34" rx="11" fill="{clothes}"/>')
    else:
        bw = 42
        s.append(f'<rect x="{x-bw/2}" y="{body_top}" width="{bw}" height="{(ground-body_top)*0.55}" rx="14" fill="{clothes}"/>')
        s.append(f'<path d="M {x-bw/2+8} {body_top+(ground-body_top)*0.5} L {x-bw/2+6} {ground} M {x+bw/2-8} {body_top+(ground-body_top)*0.5} L {x+bw/2-6} {ground}" stroke="{accent}" stroke-width="11" stroke-linecap="round"/>')
    # head covering / hair
    if kind == "hijab":
        s.append(f'<path d="M {x-head_r-4} {head_cy+8} A {head_r+4} {head_r+6} 0 1 1 {x+head_r+4} {head_cy+8} L {x+head_r+2} {head_cy+head_r+16} L {x-head_r-2} {head_cy+head_r+16} Z" fill="{accent}"/>')
        s.append(f'<circle cx="{x}" cy="{head_cy}" r="{head_r-2}" fill="{skin}"/>')
    elif kind == "turban":
        s.append(f'<circle cx="{x}" cy="{head_cy}" r="{head_r}" fill="{skin}"/>')
        s.append(f'<path d="M {x-head_r-3} {head_cy-4} A {head_r+3} {head_r} 0 1 1 {x+head_r+3} {head_cy-4} Z" fill="{accent}"/>')
        s.append(f'<circle cx="{x}" cy="{head_cy-head_r-2}" r="6" fill="{accent}"/>')
    elif kind == "elder":
        s.append(f'<circle cx="{x}" cy="{head_cy}" r="{head_r}" fill="{skin}"/>')
        s.append(f'<path d="M {x-head_r} {head_cy-2} A {head_r} {head_r} 0 1 1 {x+head_r} {head_cy-2} Z" fill="#E8E8E8"/>')
        s.append(f'<path d="M {x+28} {body_top+30} L {x+34} {ground}" stroke="#D9C9A8" stroke-width="6" stroke-linecap="round"/>')
    else:
        s.append(f'<circle cx="{x}" cy="{head_cy}" r="{head_r}" fill="{skin}"/>')
        s.append(f'<path d="M {x-head_r} {head_cy-3} A {head_r} {head_r} 0 1 1 {x+head_r} {head_cy-3} Z" fill="{accent}"/>')
    sy = body_top + 18
    return "".join(s), (x - bw/2, sy, skin), (x + bw/2, sy, skin)

# people: (x, height, skin, clothes, accent, kind)
PEOPLE = [
    (150, 218, "#8D5524", "#0FB5A8", "#173A5E", "adult"),
    (268, 202, "#C68642", "#FF6B5A", "#7A2E6D", "hijab"),
    (372, 138, "#FFDBAC", "#FFC857", "#2A9D8F", "child"),
    (478, 208, "#F1C27D", "#FFF6E5", "#173A5E", "elder"),
    (600, 176, "#5C3A21", "#8B6FD8", "#173A5E", "wheelchair"),
    (724, 210, "#E0AC69", "#2A9D8F", "#FFC857", "turban"),
    (842, 196, "#FFDBAC", "#FF8FA3", "#5B3A8E", "dress"),
    (946, 146, "#8D5524", "#7ED3F7", "#FF6B5A", "child"),
]
GROUND = 972
figures, hands = [], []
for x, h, sk, cl, ac, kind in PEOPLE:
    svg, lh, rh = person(x, GROUND, h, sk, cl, ac, kind)
    figures.append(svg); hands.append((lh, rh))
# holding hands: each person's arm reaches to a shared hand-point between neighbours
arms = []
for i in range(len(hands)-1):
    (x1,y1,sk1),(x2,y2,sk2) = hands[i][1], hands[i+1][0]
    hx, hy = (x1+x2)/2, (y1+y2)/2 + 20
    arms.append(f'<path d="M {x1:.0f} {y1:.0f} Q {x1+18:.0f} {hy:.0f} {hx:.0f} {hy:.0f}" stroke="{sk1}" stroke-width="11" stroke-linecap="round" fill="none"/>')
    arms.append(f'<path d="M {x2:.0f} {y2:.0f} Q {x2-18:.0f} {hy:.0f} {hx:.0f} {hy:.0f}" stroke="{sk2}" stroke-width="11" stroke-linecap="round" fill="none"/>')
    arms.append(f'<circle cx="{hx:.0f}" cy="{hy:.0f}" r="7" fill="{sk2}"/>')
# relaxed outer arms
for idx in (0, -1):
    (lx,ly,lsk),(rx,ry,rsk) = hands[idx]
    if idx == 0:
        arms.append(f'<path d="M {lx:.0f} {ly:.0f} Q {lx-16:.0f} {ly+34:.0f} {lx-10:.0f} {ly+52:.0f}" stroke="{lsk}" stroke-width="11" stroke-linecap="round" fill="none"/>')
    else:
        arms.append(f'<path d="M {rx:.0f} {ry:.0f} Q {rx+16:.0f} {ry+34:.0f} {rx+10:.0f} {ry+52:.0f}" stroke="{rsk}" stroke-width="11" stroke-linecap="round" fill="none"/>')
arms_svg = "".join(arms); figures_svg = "".join(figures)

stars = []
for i,(sx,sy,r,o) in enumerate([(70,90,3,.9),(150,300,2,.6),(940,110,3,.8),(990,330,2,.6),(60,520,2,.5),(1010,560,2,.5),(210,180,2,.7),(870,230,2,.7),(420,70,2,.6),(660,50,3,.7)]):
    stars.append(f'<circle class="star" style="animation-delay:{i*0.37:.2f}s" cx="{sx}" cy="{sy}" r="{r}" fill="#FFF6E5" opacity="{o}"/>')
stars_svg = "".join(stars)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="t d">
<title id="t">We Share One Home</title>
<desc id="d">Diverse people holding hands in front of planet Earth. Breathe before you react, listen before you judge, help someone today, leave it better than you found it.</desc>
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#04142B"/><stop offset=".55" stop-color="#082F49"/>
    <stop offset=".82" stop-color="#0B5563"/><stop offset="1" stop-color="#0E7C6B"/>
  </linearGradient>
  <radialGradient id="ocean" cx=".35" cy=".3" r=".9">
    <stop offset="0" stop-color="#8FE3FF"/><stop offset=".45" stop-color="#2FA8DD"/><stop offset="1" stop-color="#1266A8"/>
  </radialGradient>
  <radialGradient id="glow" cx=".5" cy=".5" r=".5">
    <stop offset="0" stop-color="#FFC857" stop-opacity=".85"/><stop offset=".55" stop-color="#FF9E5A" stop-opacity=".28"/><stop offset="1" stop-color="#FF9E5A" stop-opacity="0"/>
  </radialGradient>
  <clipPath id="earthClip"><circle cx="540" cy="650" r="272"/></clipPath>
  <style>
    .title{{font-family:Arial,Helvetica,sans-serif;font-weight:900;letter-spacing:1px}}
    .sans{{font-family:Arial,Helvetica,sans-serif}}
    .star{{animation:tw 2.8s ease-in-out infinite}}
    .float{{animation:fl 7s ease-in-out infinite;transform-origin:540px 650px}}
    .rays{{animation:spin 90s linear infinite;transform-origin:540px 650px}}
    .wave{{animation:wv 9s linear infinite}}
    @keyframes tw{{0%,100%{{opacity:.25}}50%{{opacity:1}}}}
    @keyframes fl{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-9px)}}}}
    @keyframes spin{{to{{transform:rotate(360deg)}}}}
    @keyframes wv{{to{{transform:translateX(-120px)}}}}
    @media (prefers-reduced-motion: reduce){{*{{animation:none!important}}}}
  </style>
</defs>

<rect width="{W}" height="{H}" fill="url(#sky)"/>
{stars_svg}
<circle cx="540" cy="650" r="360" fill="url(#glow)"/>

<!-- header -->
<text class="sans" x="540" y="82" text-anchor="middle" font-size="25" letter-spacing="6" fill="#7ED3F7">FOR EVERY HUMAN &#8226; ALL 8 BILLION OF US</text>
<text class="title" x="540" y="180" text-anchor="middle" font-size="94" fill="#FFF6E5">WE SHARE</text>
<text class="title" x="540" y="272" text-anchor="middle" font-size="94" fill="#FFC857">ONE HOME</text>
<text class="sans" x="540" y="318" text-anchor="middle" font-size="27" fill="#DFF6FF">UN SOLO HOGAR &#8226; &#19968;&#20010;&#23478; &#8226; &#2319;&#2325; &#2361;&#2368; &#2328;&#2352; &#8226; &#1576;&#1610;&#1578;&#1612; &#1608;&#1575;&#1581;&#1583;&#1612; &#8226; UN SEUL FOYER</text>

<!-- earth -->
<g class="float">
  <circle cx="540" cy="650" r="284" fill="none" stroke="#BDEFFF" stroke-width="3" opacity=".7"/>
  <circle cx="540" cy="650" r="272" fill="url(#ocean)"/>
  <g clip-path="url(#earthClip)" fill="#69BE7B">
    <path d="M300 520 Q340 440 440 455 Q500 465 465 520 Q430 545 440 580 Q400 620 350 590 Q290 575 300 520Z"/>
    <path d="M430 610 Q480 600 485 660 Q480 740 445 790 Q415 730 430 610Z" fill="#57A96B"/>
    <path d="M575 505 Q640 455 700 490 Q680 540 620 545 Q565 545 575 505Z" fill="#8BC98A"/>
    <path d="M585 565 Q650 545 675 610 Q665 690 610 715 Q565 650 585 565Z" fill="#E8B86B"/>
    <path d="M690 470 Q800 410 885 480 Q900 560 810 585 Q730 570 700 520Z" fill="#7CC47F"/>
    <path d="M728 642 Q782 632 798 672 Q782 716 736 700 Q714 668 728 642Z" fill="#E8B86B"/>
    <ellipse cx="540" cy="392" rx="150" ry="34" fill="#FFFFFF" opacity=".9"/>
    <ellipse cx="430" cy="700" rx="130" ry="20" fill="#FFF" opacity=".35" transform="rotate(-14 430 700)"/>
    <ellipse cx="700" cy="590" rx="150" ry="18" fill="#FFF" opacity=".3" transform="rotate(12 700 590)"/>
    <ellipse cx="560" cy="820" rx="180" ry="26" fill="#FFF" opacity=".45"/>
  </g>
  <circle cx="540" cy="650" r="272" fill="none" stroke="#EAF9FF" stroke-width="4" opacity=".85"/>
</g>

<!-- waves + people -->
<path class="wave" d="M-120 950 Q-60 920 0 950 T120 950 T240 950 T360 950 T480 950 T600 950 T720 950 T840 950 T960 950 T1080 950 T1200 950 L1200 1015 L-120 1015Z" fill="#0FB5A8" opacity=".55"/>
<path d="M0 982 Q60 958 120 982 T240 982 T360 982 T480 982 T600 982 T720 982 T840 982 T960 982 T1080 982 L1080 1025 L0 1025Z" fill="#0A7C78"/>
{arms_svg}
{figures_svg}

<!-- four habits -->
<g>
  <rect x="56" y="1032" width="968" height="196" rx="28" fill="#FFF6E5"/>
  <line x1="298" y1="1062" x2="298" y2="1198" stroke="#E7D9BE" stroke-width="2"/>
  <line x1="540" y1="1062" x2="540" y2="1198" stroke="#E7D9BE" stroke-width="2"/>
  <line x1="782" y1="1062" x2="782" y2="1198" stroke="#E7D9BE" stroke-width="2"/>

  <g transform="translate(177 1098)" stroke="#0E7C86" stroke-width="7" stroke-linecap="round" fill="none">
    <path d="M-42 -24 H14 a11 11 0 1 0 -11 -11"/><path d="M-42 0 H32 a11 11 0 1 1 -11 11"/><path d="M-42 24 H8 a10 10 0 1 0 -10 -10"/>
  </g>
  <text class="sans" x="177" y="1164" text-anchor="middle" font-size="27" font-weight="800" fill="#12324A">1. BREATHE</text>
  <text class="sans" x="177" y="1196" text-anchor="middle" font-size="21" fill="#476173">before you react</text>

  <g transform="translate(419 1102)" fill="none" stroke="#D94F3D" stroke-width="7" stroke-linecap="round">
    <path d="M-8 -36 C22 -36 32 -14 26 8 C21 27 8 40 -6 36 C-22 31 -26 12 -14 4 C-4 -3 8 -8 4 -20 C1 -28 -8 -30 -14 -24"/>
    <path d="M-14 4 C-24 -12 -20 -28 -8 -36" opacity=".55"/>
  </g>
  <text class="sans" x="419" y="1164" text-anchor="middle" font-size="27" font-weight="800" fill="#12324A">2. LISTEN</text>
  <text class="sans" x="419" y="1196" text-anchor="middle" font-size="21" fill="#476173">before you judge</text>

  <path d="M661 1140 Q610 1100 622 1074 Q632 1054 661 1070 Q690 1054 700 1074 Q712 1100 661 1140Z" fill="#E8435F"/>
  <path d="M622 1122 Q661 1152 700 1122" fill="none" stroke="#B7791F" stroke-width="6" stroke-linecap="round"/>
  <text class="sans" x="661" y="1164" text-anchor="middle" font-size="27" font-weight="800" fill="#12324A">3. HELP</text>
  <text class="sans" x="661" y="1196" text-anchor="middle" font-size="21" fill="#476173">someone today</text>

  <path d="M903 1148 L903 1102" stroke="#2F8F4E" stroke-width="7" stroke-linecap="round"/>
  <path d="M903 1108 Q868 1108 864 1076 Q896 1078 903 1108Z" fill="#57B96B"/>
  <path d="M903 1098 Q938 1098 942 1066 Q910 1068 903 1098Z" fill="#2F8F4E"/>
  <text class="sans" x="903" y="1164" text-anchor="middle" font-size="27" font-weight="800" fill="#12324A">4. REPAIR</text>
  <text class="sans" x="903" y="1196" text-anchor="middle" font-size="21" fill="#476173">leave it better</text>
</g>

<text class="title" x="540" y="1292" text-anchor="middle" font-size="31" fill="#FFF6E5">NO &#8220;US vs. THEM.&#8221; ONLY US. &#8594; PASS IT ON</text>
</svg>
'''

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(svg)
print(f"Wrote {OUT} ({len(svg.encode())} bytes)")
