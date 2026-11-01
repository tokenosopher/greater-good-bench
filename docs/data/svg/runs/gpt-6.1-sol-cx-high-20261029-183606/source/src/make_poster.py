"""Build an accessible, entirely vector poster. No external assets or dependencies."""
from pathlib import Path
import json, math, random, subprocess
from html import escape

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output'
OUT.mkdir(exist_ok=True)
NAVY='#183F46'
PAPER='#F5EFDF'
GOLD='#E8B654'
RUST='#C86649'
PALE='#EDC398'
TEAL='#559B91'
DARK='#275B59'
requests = [
    dict(id='eyebrow', text='A SMALL PRACTICE FOR A SHARED WORLD', font='AvenirNext-Medium', size=18),
    dict(id='title1', text='Everyone', font='Baskerville', size=182),
    dict(id='title2', text='is someone.', font='Baskerville-Italic', size=182),
    dict(id='equal', text='Different lives. Equal worth.', font='Baskerville', size=57),
    dict(id='action', text='Pause. Listen. Choose care.', font='AvenirNext-Medium', size=31),
]
req_path = ROOT/'src/type_requests.json'
paths_path = ROOT/'src/type_outlines.json'
req_path.write_text(json.dumps(requests))
subprocess.run(['swift', str(ROOT/'src/outline_text.swift'), str(req_path), str(paths_path)], check=True)
typepaths=json.loads(paths_path.read_text())
req_path.unlink()
paths_path.unlink()
parts=[]
def a(s): parts.append(s)
def text(id,x,y,color=NAVY,width=None,center=False):
    d=typepaths[id]
    scale=(width/d['width']) if width else 1
    if center: x-=d['width']*scale/2
    label=next(r['text'] for r in requests if r['id']==id)
    a(f'<path aria-label="{escape(label)}" fill="{color}" transform="translate({x:.3f} {y:.3f}) scale({scale:.5f})" d="{d["path"]}"/>')

a('''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1800" viewBox="0 0 1440 1800" role="img" aria-labelledby="title description">
<title id="title">Everyone is someone.</title>
<desc id="description">Two people face each other. Inside one silhouette, a moon shines over a home and a winding river. Inside the other, the sun shines over a garden and rolling fields. One continuous golden thread joins their different worlds. Different lives. Equal worth. Pause. Listen. Choose care.</desc>
<defs>
<path id="leftHead" d="M104 1367V954C104 738 215 587 382 587C523 587 615 678 609 798C607 831 620 857 643 888L676 934Q687 949 669 957L633 968L637 992Q659 1003 643 1019L632 1029Q654 1044 636 1059L624 1069C618 1115 585 1139 544 1136L528 1221C595 1257 653 1303 678 1367Z"/>
<path id="rightHead" d="M1336 1367V954C1336 739 1233 587 1065 587C926 587 831 680 835 795C836 830 825 857 800 890L764 938Q754 954 772 960L809 972L804 992Q785 1007 801 1020L812 1030Q790 1044 805 1060L818 1070C823 1116 856 1140 897 1137L913 1221C846 1257 787 1303 762 1367Z"/>
<clipPath id="clipLeft"><use href="#leftHead"/></clipPath>
<clipPath id="clipRight"><use href="#rightHead"/></clipPath>
<pattern id="paperGrain" width="170" height="170" patternUnits="userSpaceOnUse">
''')
r=random.Random(28)
for i in range(75):
    a(f'<circle cx="{r.uniform(0,170):.2f}" cy="{r.uniform(0,170):.2f}" r="{r.uniform(.3,.8):.2f}" fill="{NAVY}" opacity="{r.uniform(.025,.065):.3f}"/>')
a('</pattern></defs>')
a(f'<path fill="{PAPER}" d="M0 0H1440V1800H0Z"/>')
text('eyebrow',104,94,width=539)
# Two equal circles share a common space.
a(f'<g fill="none" stroke-width="2.1"><circle cx="1299" cy="83" r="16" stroke="{NAVY}"/><circle cx="1319" cy="83" r="16" stroke="{RUST}"/></g>')
text('title1',97,283,width=824)
text('title2',96,458,width=1005)
# A fine lead-in to the illustration; a small sun in the shared sky.
a(f'<g stroke="{GOLD}" stroke-width="3" stroke-linecap="round" fill="none">')
for angle in range(0,360,45):
    t=math.radians(angle)
    a(f'<path d="M{720+math.cos(t)*29:.2f} {651+math.sin(t)*29:.2f}L{720+math.cos(t)*42:.2f} {651+math.sin(t)*42:.2f}"/>')
a(f'<circle cx="720" cy="651" r="14" fill="{GOLD}" stroke="none"/></g>')
# Night world.
a(f'<use href="#leftHead" fill="{NAVY}"/>')
a('<g clip-path="url(#clipLeft)">')
a('<path d="M53 935C185 911 191 695 349 638C398 620 473 626 528 659C387 549 178 537 85 721Z" fill="#22535A"/>')
# Crescent: an actual compound path, no background paint-over.
a(f'<path d="M438 674A42 42 0 1 0 478 738A42 42 0 0 1 438 674Z" fill="{GOLD}"/>')
# Constellation and small stars.
a(f'<g fill="{PAPER}">')
for x,y,s in [(289,699,3),(362,738,2.3),(507,782,2.4),(224,787,2),(389,655,2.1),(474,835,2.2),(339,798,1.9)]:
    a(f'<circle cx="{x}" cy="{y}" r="{s}"/>')
a('<path d="M235 713l2.5 8.5 8.5 2.5-8.5 2.5-2.5 8.5-2.5-8.5-8.5-2.5 8.5-2.5Z"/></g>')
# Hills and home occupy the back of the head, keeping the face clear.
a(f'<path d="M66 1040C180 952 223 877 328 912C425 944 458 1034 567 1044C619 1050 669 1046 711 1060V1410H66Z" fill="{TEAL}"/>')
a(f'<path d="M70 1121C220 1036 349 1054 432 1132C510 1206 615 1175 730 1195V1410H70Z" fill="{DARK}"/>')
# Path to a lit home.
a(f'<path d="M322 973C321 1030 254 1042 269 1090C285 1142 438 1143 440 1217C442 1279 337 1311 351 1384" fill="none" stroke="{GOLD}" stroke-width="25"/>')
# Home with chimney and two warm windows.
a(f'<path d="M274 900V841H286V884L324 855L383 900V976H266V900Z" fill="{PALE}"/>')
a(f'<path d="M252 903L324 847L396 903" fill="none" stroke="{PAPER}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/>')
a(f'<path d="M284 919H302V942H284ZM344 919H362V942H344ZM316 943H334V976H316Z" fill="{NAVY}"/>')
a(f'<path d="M291 924H297V937H291ZM351 924H357V937H351Z" fill="{GOLD}"/>')
# Garden behind home: three vertical stems and leaves.
a(f'<g stroke="{PALE}" stroke-width="4" stroke-linecap="round" fill="none"><path d="M184 1001V928M184 962L167 947M184 979L201 960M214 972V911M214 944L231 927"/></g>')
a(f'<g fill="{PALE}"><ellipse cx="184" cy="921" rx="9" ry="18"/><ellipse cx="166" cy="945" rx="7" ry="12" transform="rotate(-40 166 945)"/><ellipse cx="202" cy="957" rx="7" ry="12" transform="rotate(40 202 957)"/><ellipse cx="214" cy="905" rx="7" ry="15"/><ellipse cx="231" cy="925" rx="6" ry="11" transform="rotate(40 231 925)"/></g>')
# A few fine contours give the terrain its rhythm.
a(f'<g stroke="{TEAL}" stroke-width="2" fill="none" opacity=".75"><path d="M107 1205C179 1166 226 1162 278 1174M107 1224C181 1186 230 1184 295 1202M108 1244C179 1207 227 1207 306 1232M475 1289C542 1275 588 1282 645 1318M477 1311C541 1298 591 1307 656 1347"/></g>')
a('</g>')
# Day world.
a(f'<use href="#rightHead" fill="{RUST}"/>')
a('<g clip-path="url(#clipRight)">')
a('<path d="M1359 942C1248 904 1236 695 1088 635C1035 614 972 624 919 651C1070 537 1282 550 1375 731Z" fill="#D67B56"/>')
a(f'<circle cx="1075" cy="726" r="46" fill="{GOLD}"/>')
# A pair of birds, and cloud arcs.
a(f'<g stroke="{PAPER}" fill="none" stroke-width="3.5" stroke-linecap="round"><path d="M1180 783q12-11 24 0q12-11 24 0M1161 752q8-8 16 0q8-8 16 0"/></g>')
a(f'<path d="M723 1068C829 1039 866 1061 935 1030C1031 988 1070 901 1164 908C1266 916 1318 1000 1384 1011V1410H723Z" fill="{GOLD}"/>')
a('<path d="M713 1204C828 1182 882 1218 978 1157C1102 1077 1221 1109 1381 1181V1410H713Z" fill="#B9803F"/>')
a(f'<path d="M712 1357C824 1317 909 1304 1005 1305C1142 1306 1237 1222 1376 1252V1410H712Z" fill="{DARK}"/>')
# Garden tree, with elegantly alternating leaves.
a(f'<path d="M1120 1036V865" fill="none" stroke="{NAVY}" stroke-width="6" stroke-linecap="round"/>')
for d in [
    'M1120 952C1077 952 1064 927 1067 901C1097 905 1122 923 1120 952Z',
    'M1120 920C1156 919 1172 893 1168 871C1140 875 1120 892 1120 920Z',
    'M1120 891C1087 885 1075 862 1080 841C1106 848 1121 865 1120 891Z',
    'M1120 867C1146 849 1147 826 1137 806C1114 820 1111 845 1120 867Z',
    'M1120 985C1159 985 1184 962 1181 935C1148 939 1121 958 1120 985Z',
]: a(f'<path d="{d}" fill="{NAVY}"/>')
# Little plant, the next generation.
a(f'<g fill="{DARK}" stroke="{DARK}" stroke-width="4" stroke-linecap="round"><path d="M1244 1087V1022"/><path d="M1244 1055C1224 1054 1216 1040 1217 1027C1235 1029 1244 1040 1244 1055ZM1244 1039C1267 1034 1275 1018 1271 1005C1255 1011 1245 1021 1244 1039Z" stroke="none"/></g>')
# Curving field rows.
a(f'<g stroke="{PALE}" stroke-width="2.5" fill="none" opacity=".85"><path d="M942 1176C1039 1121 1179 1154 1307 1203M952 1193C1044 1144 1183 1176 1290 1218M963 1211C1051 1168 1175 1195 1266 1234M978 1228C1055 1195 1150 1211 1229 1245"/></g>')
# Continuation of the night world's thread.
a(f'<path d="M1145 1050C1130 1106 1039 1108 1043 1172C1048 1235 1120 1276 1090 1384" stroke="{GOLD}" stroke-width="25" fill="none"/>')
a('</g>')
# Quiet attentive eyes: two short curves at exactly the same level.
a(f'<g stroke="{PAPER}" stroke-width="4.5" stroke-linecap="round" fill="none"><path d="M561 877Q579 866 598 877"/></g>')
a(f'<g stroke="{NAVY}" stroke-width="4.5" stroke-linecap="round" fill="none"><path d="M842 877Q861 866 879 877"/></g>')
# Join both river paths outside the silhouettes: one uninterrupted shared ground.
a(f'<path d="M351 1367C355 1441 543 1425 720 1425C897 1425 1070 1441 1090 1367" fill="none" stroke="{GOLD}" stroke-width="25"/>')
# A seed suspended in the middle of the shared thread.
a(f'<path d="M720 1425V1381M720 1407C695 1407 686 1390 687 1376C707 1378 720 1388 720 1407ZM720 1392C743 1392 754 1376 753 1360C732 1362 720 1377 720 1392Z" fill="{NAVY}" stroke="{NAVY}" stroke-width="3.5" stroke-linejoin="round"/>')
text('equal',720,1560,center=True)
a(f'<path d="M104 1625H1336" fill="none" stroke="{NAVY}" stroke-opacity=".28" stroke-width="1.4"/>')
text('action',720,1697,center=True)
a('<path d="M0 0H1440V1800H0Z" fill="url(#paperGrain)" pointer-events="none"/>')
a('</svg>')
svg='\n'.join(parts)+'\n'
(OUT/'everyone-is-someone.svg').write_text(svg)
print(f'Wrote SVG: {len(svg):,} bytes')

# Render the companion JPEG through an in-memory PNG stream; no raster intermediates.
render = subprocess.run(['rsvg-convert', str(OUT/'everyone-is-someone.svg')], check=True, stdout=subprocess.PIPE)
subprocess.run(['ffmpeg', '-y', '-hide_banner', '-loglevel', 'error', '-i', 'pipe:0', '-frames:v', '1', '-q:v', '2', str(OUT/'everyone-is-someone.jpg')], input=render.stdout, check=True)
for path in OUT.iterdir():
    assert path.stat().st_size < 2_000_000, f'{path.name} exceeds the size limit'
    print(f'{path.name}: {path.stat().st_size:,} bytes')
