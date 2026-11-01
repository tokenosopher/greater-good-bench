from pathlib import Path
import json, subprocess

ROOT = Path(__file__).resolve().parent.parent
INK = '#202F32'
TEAL = '#247169'
PAPER = '#F4F0E6'
GOLD = '#EDC65B'
CORAL = '#D65A43'
labels = []
def text(s, x, y, size, color=INK, font='AvenirNext-Regular', tracking=0, anchor='start'):
    labels.append(dict(text=s, x=x, y=y, size=size, color=color, font=font, tracking=tracking, anchor=anchor))

text('A SMALL PRACTICE FOR A SHARED WORLD', 94, 113, 21, font='AvenirNext-DemiBold', tracking=3)
text('Let the hurt', 84, 343, 157, font='AvenirNext-Bold', tracking=-6)
text('end here.', 84, 513, 157, font='AvenirNext-Bold', tracking=-6)
text('We cannot choose every feeling.', 96, 610, 31)
text('We can choose what we do with it.', 96, 655, 31)

text('WHAT REACHES YOU', 266, 1212, 18, font='AvenirNext-DemiBold', tracking=2, anchor='middle')
text('THE PAUSE', 720, 1212, 18, font='AvenirNext-DemiBold', tracking=2, anchor='middle')
text('WHAT YOU PASS ON', 1170, 1212, 18, font='AvenirNext-DemiBold', tracking=2, anchor='middle')

text('Pause. Breathe. Choose care.', 94, 1400, 65, font='AvenirNext-DemiBold', tracking=-2)
text('A helping hand. A fair word. A firm boundary.', 96, 1464, 32)
text('You can be kind and still say no.', 96, 1512, 32)
text('The next moment is a place to start.', 96, 1705, 28, font='AvenirNext-Medium')
text('01 / ONE ANOTHER', 1344, 1705, 16, font='AvenirNext-DemiBold', tracking=2, anchor='end')

r = subprocess.run(['swift', str(ROOT/'src/outline.swift')], input=json.dumps(labels), text=True, capture_output=True, check=True)
paths = json.loads(r.stdout)
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="1800" viewBox="0 0 1440 1800" role="img" aria-labelledby="title desc">
<title id="title">Let the hurt end here.</title>
<desc id="desc">A coral line arrives sharp and tangled. At a golden circle containing a pause symbol it stops. A green line emerges in a gentle curve and grows leaves. We cannot choose every feeling. We can choose what we do with it. Pause. Breathe. Choose care. A helping hand. A fair word. A firm boundary. You can be kind and still say no. The next moment is a place to start.</desc>
<rect width="1440" height="1800" fill="{PAPER}"/>
<!-- Editorial rules -->
<path d="M96 158H1344 M96 1290H1344 M96 1635H1344" stroke="{INK}" stroke-opacity=".23" stroke-width="1.5"/>
<g transform="translate(1310 94)" fill="{TEAL}">
<rect x="0" y="0" width="10" height="26" rx="2"/><rect x="20" y="0" width="10" height="26" rx="2"/>
</g>
<!-- A difficult feeling: one continuous, jagged, tangled strand. -->
<path d="M-30 965 L70 965 L115 884 L172 1057 L232 812 L294 1076 L351 915 C399 782 495 820 470 938 C449 1037 331 1077 349 981 C362 909 439 902 507 951 L552 965" fill="none" stroke="{CORAL}" stroke-width="19" stroke-linejoin="round" stroke-linecap="round"/>
<!-- Space between feeling and action. -->
<circle cx="720" cy="965" r="176" fill="{GOLD}"/>
<circle cx="720" cy="965" r="200" fill="none" stroke="{GOLD}" stroke-opacity=".4" stroke-width="1.5"/>
<g fill="{INK}"><rect x="674" y="906" width="29" height="118" rx="5"/><rect x="737" y="906" width="29" height="118" rx="5"/></g>
<!-- The same energy, given a gentler direction. -->
<path d="M896 965 C982 965 970 1080 1072 1080 C1172 1080 1246 965 1246 839" fill="none" stroke="{TEAL}" stroke-width="19" stroke-linecap="round"/>
<path d="M1246 954 C1177 952 1135 900 1140 851 C1207 849 1250 892 1246 954Z" fill="{TEAL}"/>
<path d="M1247 884 C1250 816 1300 776 1357 783 C1354 845 1310 886 1247 884Z" fill="{TEAL}"/>
<path d="M1246 841 C1202 808 1197 761 1217 729 C1257 755 1272 799 1246 841Z" fill="{TEAL}"/>
<g fill="{GOLD}"><circle cx="1323" cy="1029" r="7"/><circle cx="1360" cy="970" r="4"/></g>
<!-- Lettering is outlined for consistent display without installed fonts. -->
{''.join(paths)}
</svg>'''
(ROOT/'output/let-the-hurt-end-here.svg').write_text(svg)
print('Created SVG:', len(svg.encode()), 'bytes')
