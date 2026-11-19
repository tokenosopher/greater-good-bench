"""Draw The Firebreak as a self-contained, limited-ink vector print."""
import math
import random
import subprocess
from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parent
rng = random.Random(84913)
ink = '#173b37'
deep = '#102f2e'
teal = '#3a6760'
sea = '#81a89a'
paper = '#f7e6bf'
ochre = '#eeb154'
orange = '#ef683b'
red = '#bf452f'
out = []
def add(s):
    out.append(s)
def path(d, fill, extra=''):
    add(f'<path d="{d}" fill="{fill}" {extra}/>')
def stroke(d, color, w, extra=''):
    path(d, 'none', f'stroke="{color}" stroke-width="{w}" {extra}')
def group(t):
    add(f'<g transform="{t}">')
def end():
    add('</g>')
def rect(x,y,w,h,color):
    add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{color}"/>')
def outlined_text(words, font, size, spacing, color, y, style='normal'):
    # Bake installed typefaces into vector outlines for consistent rendering.
    text = f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="160"><text x="700" y="100" text-anchor="middle" font-family="{font}" font-style="{style}" font-size="{size}" letter-spacing="{spacing}" fill="{color}">{words}</text></svg>'
    svg = subprocess.run(['rsvg-convert','-f','svg'], input=text.encode(), capture_output=True,check=True).stdout
    node = ET.fromstring(svg)
    prefix = 'text' + str(y) + '-'
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    ET.register_namespace('xlink', 'http://www.w3.org/1999/xlink')
    sub = ''.join(ET.tostring(c, encoding='unicode') for c in node)
    import re
    ids = re.findall(r'\bid="([^"]+)"',sub)
    for ident in sorted(ids, key=len, reverse=True):
        sub=sub.replace(f'id="{ident}"',f'id="{prefix}{ident}"').replace(f'="#{ident}"',f'="#{prefix}{ident}"')
    group(f'translate(0 {y-100})')
    add(sub)
    end()

add('<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 1400 1000" width="1400" height="1000" role="img" aria-labelledby="title desc">')
add('<title id="title">The Firebreak</title><desc id="desc">A vintage matchbox label. Flames run along a row of matches until one match turns head-down. The remaining matches are unlit. Take a breath before you answer in anger.</desc>')
# A cartouche with recessed, quarter-round corners.
panel='M117 325 H1283 Q1283 369 1332 369 V755 Q1283 755 1283 799 H117 Q117 755 68 755 V369 Q117 369 117 325 Z'
add(f'<defs><clipPath id="scene"><path d="{panel}"/></clipPath></defs>')
rect(0,0,1400,1000,paper)
frame='M57 25 H1343 L1375 57 V943 L1343 975 H57 L25 943 V57Z'
stroke(frame,ink,9)
stroke('M61 39 H1339 L1361 61 V939 L1339 961 H61 L39 939 V61Z',ink,2.5)
# Small ornaments common to printed match labels.
for x,y,sx,sy in [(52,52,1,1),(1348,52,-1,1),(52,948,1,-1),(1348,948,-1,-1)]:
    group(f'translate({x} {y}) scale({sx} {sy})')
    path('M0 22 Q6 6 27 0 Q23 14 0 22Z',red)
    path('M4 32 Q19 17 37 16 Q25 28 4 32Z',ink)
    end()
# Set a hand-drawn slab serif inscription on a very shallow arc.
letters={
'F':(74,'M0 0H74V31H62L56 14H34V44H52L55 35H63V68H55L52 58H34V85L46 90V100H0V90L9 85V15L0 11Z'),
'I':(46,'M0 0H46V11L36 15V85L46 90V100H0V90L10 85V15L0 11Z'),
'R':(88,'M0 0H48Q82 0 82 27Q82 45 64 51Q75 55 75 69L78 84L87 90V100H57L50 69Q48 58 35 58H33V85L42 90V100H0V90L9 85V15L0 11Z M33 14V45H40Q56 45 56 29Q56 14 41 14Z'),
'E':(77,'M0 0H75V30H63L58 14H33V43H48L52 35H60V65H52L48 57H33V86H60L65 68H77V100H0V90L9 85V15L0 11Z'),
'B':(84,'M0 0H47Q79 0 79 25Q79 40 62 47Q83 51 83 72Q83 100 48 100H0V90L9 85V15L0 11Z M34 14V41H41Q54 41 54 28Q54 14 41 14Z M34 55V86H43Q57 86 57 70Q57 55 41 55Z'),
'A':(91,'M31 0H58L82 85L91 90V100H47V90L55 86L52 75H28L25 86L34 90V100H0V90L9 85Z M32 60H49L41 26Z'),
'K':(89,'M0 0H43V11L35 15V45L59 15L51 11V0H87V11L77 15L54 44L78 85L89 90V100H45V90L51 86L36 60L33 64V85L41 90V100H0V90L9 85V15L0 11Z')}
word='FIREBREAK'
advance=sum(letters[c][0] for c in word)+7*(len(word)-1)
scale=1.66
for shade,dx,dy in [(red,4.5,7),(paper,1.8,3),(ink,0,0)]:
    left=700-advance*scale/2
    for c in word:
        w,d=letters[c]
        center=left+w*scale/2
        n=(center-700)/580
        y=111+25*n*n
        angle=math.degrees(math.atan(50*n/580))
        group(f'translate({center+dx:.2f} {y+dy:.2f}) rotate({angle:.2f}) scale({scale}) translate({-w/2} 0)')
        path(d,shade,'fill-rule="evenodd"')
        end()
        left+=(w+7)*scale
outlined_text('THE','Georgia',33,5,ink,88,'italic')
for sign in [-1,1]:
    group(f'translate(700 77) scale({sign} 1)')
    path('M57 0Q118 -4 216 1Q123 0 57 3Z',red)
    path('M58 8Q136 6 163 9Q91 9 58 10Z',red)
    end()
# Central illustration.
path(panel,ink,f'stroke="{ink}" stroke-width="15"')
stroke(panel,paper,7)
add('<g clip-path="url(#scene)">')
path(panel,ink)
# Engraved rays sweep out from the inverted head, giving it visual emphasis.
cx,cy=711,713
for i in range(89):
    theta=math.radians(-187+i*2.24)
    radius=rng.uniform(70,192)
    span=rng.uniform(.0018,.0053)
    radii=[(radius,theta),(1100,theta-span),(1100,theta+span)]
    pts=[(cx+math.cos(a)*r,cy+math.sin(a)*r) for r,a in radii]
    path('M'+'L'.join(f'{x:.1f} {y:.1f}' for x,y in pts)+'Z','#396159')
# Low, densely hatched shadow below the sticks, cut into the dark plate.
for i in range(108):
    x=rng.uniform(64,1323); y=rng.uniform(751,802); w=rng.uniform(7,91)
    path(f'M{x:.1f} {y:.1f}q{w*.4:.1f} -1.7 {w:.1f} -.6q{-w*.46:.1f} 2.2 {-w:.1f} .6Z',teal)
# Windswept flames, with three hand-cut contours to vary the silhouette.
flames=[
'M-19 10C-63 -8 -55 -47 -57 -62C-48 -57 -40 -49 -38 -51C-63 -102 -19 -118 -30 -159C-12 -150 -10 -124 -13 -114C7 -141 -1 -162 45 -202C26 -158 61 -145 42 -111C63 -122 66 -138 66 -149C90 -107 53 -78 48 -61C63 -67 66 -75 71 -82C68 -48 36 -38 27 -11Q13 17 -19 10Z',
'M-24 8C-53 -7 -48 -37 -65 -55C-49 -54 -41 -46 -37 -41C-60 -96 -22 -112 -36 -156C-9 -137 -15 -108 -13 -103C2 -139 35 -143 22 -201C73 -165 28 -120 47 -98C57 -113 70 -117 73 -142C91 -104 58 -80 49 -61C64 -65 69 -75 74 -80C72 -37 36 -32 27 -9Q6 19 -24 8Z',
'M-22 11C-53 -7 -57 -42 -51 -63C-44 -55 -44 -50 -33 -44C-63 -102 -2 -132 -9 -177C13 -161 3 -139 3 -126C29 -160 24 -186 51 -205C37 -165 66 -148 48 -122C37 -105 39 -93 42 -90C56 -112 68 -109 78 -133C84 -93 53 -76 50 -56C66 -60 70 -69 77 -72C69 -40 40 -27 26 -8Q8 18 -22 11Z']
lit=[(173,569,-5,1.11,.80),(308,543,2,1.08,1.02),(445,555,-3,1.13,.96),(578,551,4,.94,.73)]
for idx,(x,y,a,s,h) in enumerate(lit):
    group(f'translate({x} {y}) scale({s} {h})')
    path(flames[idx%3],red)
    group('translate(3 -3) scale(.92 .975)')
    path(flames[idx%3],orange)
    end()
    path('M-20 8C-51 -17 -25 -45 -42 -76C-28 -72 -21 -61 -18 -55C-25 -90 5 -106 1 -141C21 -120 1 -98 11 -79C21 -105 43 -107 47 -131C57 -99 25 -75 29 -58C39 -63 45 -67 51 -78C48 -41 27 -35 20 -10Q8 15 -20 8Z',ochre)
    path('M-14 6Q-35 -9 -21 -39Q-18 -33 -16 -31Q-19 -51 -1 -76Q-6 -54 2 -48Q14 -60 15 -78Q30 -55 12 -33Q22 -35 26 -42Q26 -19 15 -7Z',paper)
    end()
# Tiny tapering chips floating out of the fire.
for i in range(46):
    x=rng.uniform(102,628); y=rng.uniform(330,501)
    if rng.random()<.33 and y>420: continue
    h=rng.uniform(3,14); w=rng.uniform(1,3.6)
    path(f'M{x:.1f} {y:.1f}q{-w:.1f} {-h*.4:.1f} {w:.1f} {-h:.1f}q{w:.1f} {h*.5:.1f} {-w:.1f} {h:.1f}Z',rng.choice([red,orange,ochre]))
def match(x,y,angle,length,burnt=False):
    group(f'translate({x} {y}) rotate({angle})')
    # Four wood faces with tapered grain lines. Head is at the local origin.
    path(f'M-11 -2L9 -2L10 {length-3}L4 {length+2}L-11 {length-1}Z',ochre)
    path(f'M-9 -3L4 -3L3 {length}L-9 {length-2}Z',paper)
    path(f'M6 5L11 2L10 {length-3}L4 {length+2}Z','#ad7950')
    for _ in range(9):
        xx=rng.uniform(-8,5); yy=rng.uniform(21,length-24); h=rng.uniform(10, min(length-yy,73))
        path(f'M{xx:.1f} {yy:.1f}q-1 {h*.48:.1f} .1 {h:.1f}q1 {-h*.4:.1f} -.1 {-h:.1f}Z','#ae8f65')
    if burnt:
        path('M-11 -2H11V30L6 56L4 39L1 47L-2 34L-5 46L-9 30Z','#855b43')
        path('M-10 -2H10L9 23L5 36L1 26L-3 33L-9 21Z',deep)
    head='M-9 18C-19 9 -20 -7 -17 -20C-15 -33 -4 -39 6 -36C19 -34 22 -21 19 -8C18 2 13 13 9 19Q0 25 -9 18Z'
    path(head,deep,'stroke="'+deep+'" stroke-width="4"')
    path(head,'#714a3b' if burnt else red)
    path('M-12 4Q-20 -14 -12 -26Q-5 -38 6 -33Q-7 -31 -8 -22Q-13 -9 -12 4Z',orange if burnt else '#f48b5b')
    path('M-9 16Q4 17 10 3Q18 -16 15 -23Q23 -7 10 17Q2 27 -9 16Z',deep if burnt else '#8d382a')
    for i in range(29):
        xp=rng.uniform(-13,14); yp=rng.uniform(-28,13)
        if ((xp-1)/16)**2+((yp+8)/27)**2>1: continue
        radius=rng.uniform(.55,1.65)
        add(f'<circle cx="{xp:.1f}" cy="{yp:.1f}" r="{radius:.1f}" fill="{rng.choice([ochre,deep,orange])}"/>')
    end()
for x,y,a,s,h in lit:
    match(x,y,a,751-y,True)
for x,y,a in [(838,550,-2),(972,551,3),(1103,549,-3),(1235,553,4)]:
    match(x,y,a,751-y)
# Two arcs describe the single rotation, left open so the match stays clear.
stroke('M661 664C645 633 649 597 667 571',sea,2.8)
path('M661 576L671 564L670 581L667 575Z',sea)
stroke('M760 627C777 657 771 694 752 716',sea,2.8)
path('M758 711L747 723L749 706L752 713Z',sea)
match(699,718,195,185)
end()
# Below the woodcut, a single practical invitation.
outlined_text('Take a breath before you answer in anger.','Georgia',50,0,ink,896,'italic')
for s in (-1,1):
    group(f'translate(700 929) scale({s} 1)')
    path('M17 0Q105 -2 205 0Q95 2 17 2Z',red)
    end()
path('M690 930L700 925L710 930L700 935Z',red)
# Paper and ink wear. Independent little cuts, with no renderer-specific filters.
def flecks(num,color,opacity,minsize,maxsize):
    bits=[]
    for _ in range(num):
        x=rng.uniform(0,1400); y=rng.uniform(0,1000); w=rng.uniform(minsize,maxsize)
        h=w*rng.uniform(.23,.94)
        bits.append(f'M{x:.1f} {y:.1f}l{w:.1f} -.3 .2 {h:.1f} {-w*.7:.1f} .2Z')
    path(''.join(bits),color,f'opacity="{opacity}"')
flecks(8200,paper,.38,.6,2.7)
flecks(4800,deep,.18,.6,2.3)
add('</svg>')
(root/'output').mkdir(exist_ok=True)
(root/'output'/'the-firebreak.svg').write_text('\n'.join(out))
