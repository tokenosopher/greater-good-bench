#!/usr/bin/env python3
"""Generate the finished kindness poster as a self-contained SVG."""
from pathlib import Path

OUT = Path("output")
OUT.mkdir(exist_ok=True)

svg = r'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="2000" viewBox="0 0 1600 2000" role="img" aria-labelledby="title desc">
  <title id="title">Make someone's day a little easier</title>
  <desc id="desc">A warm poster showing two hands gently holding a glowing heart. It encourages everyone to notice, listen, and offer what they can.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#102f31"/>
      <stop offset="1" stop-color="#183e3b"/>
    </linearGradient>
    <radialGradient id="halo">
      <stop offset="0" stop-color="#f6c86b" stop-opacity=".17"/>
      <stop offset=".64" stop-color="#f6c86b" stop-opacity=".05"/>
      <stop offset="1" stop-color="#f6c86b" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="sun" x1=".25" y1="0" x2=".8" y2="1">
      <stop offset="0" stop-color="#ffe29a"/>
      <stop offset="1" stop-color="#f4b952"/>
    </linearGradient>
    <pattern id="grain" width="23" height="23" patternUnits="userSpaceOnUse">
      <circle cx="3" cy="5" r=".7" fill="#fff8e8" opacity=".07"/>
      <circle cx="17" cy="16" r=".55" fill="#fff8e8" opacity=".05"/>
    </pattern>
    <filter id="softGlow" x="-80%" y="-80%" width="260%" height="260%">
      <feGaussianBlur stdDeviation="18"/>
    </filter>
    <g id="spark" fill="#f8d27d">
      <path d="M0-15C2-5 5-2 15 0 5 2 2 5 0 15-2 5-5 2-15 0-5-2-2-5 0-15Z"/>
    </g>
    <g id="handShape">
      <path d="M164 1207 385 1136c52-16 94-37 135-70l120-101c23-19 49-18 64 1 15 20 8 42-12 59l-83 70 137-31c28-6 49 5 53 25 4 21-11 37-36 44l-129 35c-46 13-82 36-116 69l-63 61-310 72Z"/>
      <path d="M164 1207 385 1136c26-8 50-18 73-31l-10 163-284 72Z" fill="#0d292b" opacity=".14"/>
      <path d="M609 1095c24-14 49-24 75-31" fill="none" stroke="#173b38" stroke-opacity=".28" stroke-width="7" stroke-linecap="round"/>
      <path d="M482 1177c33-10 61-25 86-45" fill="none" stroke="#173b38" stroke-opacity=".22" stroke-width="7" stroke-linecap="round"/>
      <path d="m164 1207 220-69-12 141-208 61Z" fill="#e7a08a"/>
      <path d="m383 1138-11 141" fill="none" stroke="#f8c0aa" stroke-width="5" opacity=".65"/>
    </g>
  </defs>

  <!-- Ink-green ground and a quiet print border -->
  <rect width="1600" height="2000" fill="url(#bg)"/>
  <rect width="1600" height="2000" fill="url(#grain)"/>
  <rect x="54" y="54" width="1492" height="1892" rx="3" fill="none" stroke="#729087" stroke-opacity=".48" stroke-width="2"/>
  <path d="M54 115V54h61M1485 54h61v61M1546 1885v61h-61M115 1946H54v-61" fill="none" stroke="#f4c56b" stroke-width="5"/>

  <!-- Eyebrow -->
  <g transform="translate(120 133)" fill="none" stroke="#f5c86e" stroke-width="3">
    <circle r="11"/>
    <path d="M0-22v-9M0 22v9M-22 0h-9M22 0h9M-16-16l-6-6M16 16l6 6M16-16l6-6M-16 16l-6 6" stroke-linecap="round"/>
  </g>
  <text x="165" y="144" fill="#f4d99d" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" font-size="27" font-weight="600" letter-spacing="6">A SMALL PRACTICE. A SHARED WORLD.</text>
  <path d="M120 185H1480" stroke="#729087" stroke-opacity=".45" stroke-width="2"/>

  <!-- The promise: an action small enough for everyone -->
  <text x="116" y="314" fill="#fff4df" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" font-size="105" font-weight="700" letter-spacing="-2">MAKE SOMEONE’S DAY</text>
  <text x="112" y="475" fill="#fff4df" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" font-size="157" font-weight="800" letter-spacing="-6">A LITTLE</text>
  <text x="805" y="475" fill="#f5c86e" font-family="Baskerville, Georgia, Times New Roman, serif" font-size="169" font-style="italic" font-weight="700" letter-spacing="-5">EASIER.</text>
  <text x="120" y="546" fill="#c7d6cc" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" font-size="31" font-weight="400" letter-spacing=".5">You don’t have to fix everything to change something.</text>
  <use href="#spark" transform="translate(1438 505) scale(1.2)"/>
  <circle cx="1400" cy="522" r="4" fill="#e9967e"/>
  <circle cx="1474" cy="465" r="5" fill="#7eb6a6"/>

  <!-- Central emblem: care is something we can hold and share -->
  <circle cx="800" cy="1010" r="446" fill="url(#halo)"/>
  <circle cx="800" cy="966" r="348" fill="none" stroke="#87a79b" stroke-opacity=".24" stroke-width="2"/>
  <path d="M489 827a348 348 0 0 1 182-196M927 635a348 348 0 0 1 184 192M1112 1105a348 348 0 0 1-182 196M674 1297a348 348 0 0 1-185-192" fill="none" stroke="#f3c56b" stroke-opacity=".62" stroke-width="3" stroke-linecap="round"/>
  <path d="M574 740c-50 53-86 118-105 188M1026 740c50 53 86 118 105 188" fill="none" stroke="#8bb5a6" stroke-opacity=".45" stroke-width="2" stroke-dasharray="3 13" stroke-linecap="round"/>

  <!-- Orbiting reminders of warmth -->
  <use href="#spark" transform="translate(474 805) scale(.85)"/>
  <use href="#spark" transform="translate(1137 853) scale(.65)"/>
  <use href="#spark" transform="translate(1075 1177) scale(.9)"/>
  <circle cx="541" cy="1136" r="8" fill="#e9967e"/>
  <circle cx="1054" cy="729" r="7" fill="#8bbcac"/>
  <circle cx="1155" cy="1034" r="4" fill="#f6d687"/>

  <!-- Radiance behind the heart -->
  <g stroke="#f6cc77" stroke-width="5" stroke-linecap="round" opacity=".85">
    <path d="M800 684v-38M702 704l-18-34M898 704l18-34M627 770l-34-20M973 770l34-20M606 870h-39M994 870h39"/>
  </g>
  <g fill="#f6cc77">
    <circle cx="664" cy="700" r="5"/><circle cx="936" cy="700" r="5"/>
    <circle cx="583" cy="814" r="5"/><circle cx="1017" cy="814" r="5"/>
  </g>
  <circle cx="800" cy="872" r="153" fill="#f5c86e" opacity=".12" filter="url(#softGlow)"/>
  <circle cx="800" cy="872" r="137" fill="none" stroke="#f5c86e" stroke-opacity=".24" stroke-width="2"/>
  <circle cx="800" cy="872" r="111" fill="url(#sun)"/>
  <circle cx="770" cy="839" r="70" fill="#fff3c7" opacity=".12"/>
  <path d="M800 937c-31-31-91-63-91-113 0-40 44-58 75-28l16 16 16-16c31-30 75-12 75 28 0 50-60 82-91 113Z" fill="#fff7e7"/>
  <path d="M800 925c-27-27-79-56-79-101" fill="none" stroke="#fff" stroke-opacity=".45" stroke-width="4" stroke-linecap="round"/>

  <!-- Two differently colored hands, one shared responsibility -->
  <use href="#handShape" fill="#ef987f"/>
  <use href="#handShape" transform="translate(1600 0) scale(-1 1)" fill="#f4dfbd"/>
  <path d="m1436 1207-220-69 12 141 208 61Z" fill="#d8bd94"/>
  <path d="m1217 1138 11 141" fill="none" stroke="#fff0d1" stroke-width="5" opacity=".7"/>
  <path d="M670 1181c62-24 107-30 130-30s68 6 130 30" fill="none" stroke="#f3c56b" stroke-opacity=".34" stroke-width="3" stroke-linecap="round"/>

  <!-- Three ways to begin today -->
  <path d="M120 1414H1480" stroke="#729087" stroke-opacity=".5" stroke-width="2"/>
  <g font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" text-anchor="middle">
    <!-- Notice -->
    <g transform="translate(350 1540)">
      <circle r="67" fill="#224b46" stroke="#66877d" stroke-width="2"/>
      <path d="M-40 0s16-25 40-25S40 0 40 0 24 25 0 25-40 0-40 0Z" fill="none" stroke="#f6dfb3" stroke-width="5" stroke-linejoin="round"/>
      <circle r="11" fill="#f5c86e"/>
      <circle cx="4" cy="-4" r="3" fill="#fff6df"/>
      <text y="128" fill="#f5c86e" font-size="25" font-weight="700" letter-spacing="5">NOTICE</text>
      <text y="170" fill="#e4eadf" font-size="28">Someone might be struggling.</text>
    </g>
    <!-- Listen -->
    <g transform="translate(800 1540)">
      <circle r="67" fill="#224b46" stroke="#66877d" stroke-width="2"/>
      <path d="M-34-30h68c10 0 18 8 18 18v29c0 10-8 18-18 18H2l-24 20 5-20h-17c-10 0-18-8-18-18v-29c0-10 8-18 18-18Z" fill="none" stroke="#f6dfb3" stroke-width="5" stroke-linejoin="round"/>
      <path d="M-23 2h46" stroke="#f5c86e" stroke-width="5" stroke-linecap="round"/>
      <circle cx="-26" cy="-13" r="3.5" fill="#e9967e"/><circle cx="-13" cy="-13" r="3.5" fill="#e9967e"/>
      <text y="128" fill="#f5c86e" font-size="25" font-weight="700" letter-spacing="5">LISTEN</text>
      <text y="170" fill="#e4eadf" font-size="28">Give your full attention.</text>
    </g>
    <!-- Offer -->
    <g transform="translate(1250 1540)">
      <circle r="67" fill="#224b46" stroke="#66877d" stroke-width="2"/>
      <path d="M-43 11h17l18 12h24c9 0 13 10 5 15l-9 6H-14l-29-14M-43 11v26" fill="none" stroke="#f6dfb3" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>
      <path d="M7 5C-2-4-17-11-17-24c0-11 12-16 20-7l4 5 4-5c8-9 20-4 20 7 0 13-15 20-24 29Z" fill="#f5c86e"/>
      <text y="128" fill="#f5c86e" font-size="25" font-weight="700" letter-spacing="4">OFFER WHAT YOU CAN</text>
      <text y="170" fill="#e4eadf" font-size="28">Time. Patience. A helping hand.</text>
    </g>
  </g>

  <!-- A quiet closing invitation -->
  <path d="M120 1790H660M940 1790h540" stroke="#729087" stroke-opacity=".45" stroke-width="2"/>
  <use href="#spark" transform="translate(800 1790) scale(.8)"/>
  <text x="800" y="1868" text-anchor="middle" fill="#fff1d6" font-family="Avenir Next, Helvetica Neue, Arial, sans-serif" font-size="31" font-weight="600" letter-spacing="4">SMALL THINGS COUNT. PASS IT ON.</text>
</svg>
'''

(OUT / "kindness.svg").write_text(svg, encoding="utf-8")
print(f"Wrote {OUT / 'kindness.svg'} ({len(svg.encode()):,} bytes)")
