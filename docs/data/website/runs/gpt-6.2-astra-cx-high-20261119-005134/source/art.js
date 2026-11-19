// Original print-style illustrations, drawn at the display's pixel density.
const ink = '#252820', paper = '#fff7db', orange = '#ff6432';
function painter(c) {
  return {
    shape(d, color, edge, width=2) {
      const path = new Path2D(d);
      if (color) { c.fillStyle=color; c.fill(path); }
      if (edge) { c.lineWidth=width; c.strokeStyle=edge; c.stroke(path); }
    },
    ellipse(x,y,rx,ry,color,angle=0) {
      c.beginPath(); c.ellipse(x,y,rx,ry,angle,0,Math.PI*2); c.fillStyle=color; c.fill();
    },
    line(d,color=ink,width=2) { this.shape(d,null,color,width); },
    star(x,y,size,color=ink) {
      c.save(); c.translate(x,y); c.scale(size/10,size/10);
      this.shape('M0 -12 Q2 -2 11 0 Q2 2 0 12 Q-2 3 -11 0 Q-2 -2 0 -12Z',color); c.restore();
    }
  };
}
function flower(c,p) {
  // A faint, irregularly bounded graph-paper ground.
  c.save();
  for(let i=0;i<18;i++) for(let j=0;j<12;j++){
    const x=35+i*26, y=15+j*26;
    const a=Math.max(0,1-((x-262)/244)**4-((y-164)/176)**4);
    c.globalAlpha=a*.53;
    p.line('M'+x+' '+y+'h26m-26 0v26','#b5b5a1',.65);
  }
  c.restore();
  p.line('M205 320 C239 295 274 239 282 190 Q288 155 299 129',ink,10);
  p.shape('M260 258 C200 250 168 208 148 157 C205 161 255 181 269 219 Q273 240 260 258Z','#648044',ink,2.5);
  p.line('M151 160 Q213 203 261 256 M191 189 L184 174 M212 210 L206 187 M220 217 L195 208 M241 235 L234 209',ink,1.7);
  p.shape('M251 273 C269 223 303 202 361 198 C352 241 314 273 251 273Z','#7e9654',ink,2.4);
  p.line('M253 271 Q308 233 357 201 M284 250 L291 230 M300 240 L324 237 M319 226 L326 212',ink,1.6);
  c.save(); c.translate(299,124); c.rotate(.16); c.scale(.93,.93);
  const sizes=[1,.94,.98,1.02,.98,.95,1.03,.98,.94,1.01,1.03];
  sizes.forEach((s,i)=>{
    c.save(); c.rotate(i*Math.PI*2/11); c.scale(1,s);
    p.shape('M-16 -22 C-22 -44 -35 -79 -27 -103 C-21 -123 -3 -129 12 -120 C29 -109 27 -88 22 -70 L16 -26Z',orange); c.restore();
  });
  p.ellipse(0,0,52,52,ink);
  p.ellipse(-16,-11,5.5,10,paper,-.08); p.ellipse(16,-13,5.5,10,paper,-.09);
  p.line('M-27 8 C-19 35 16 37 29 6',paper,4.8);
  c.restore();
  p.star(121,84,16); p.star(427,187,10); p.star(137,249,8);
  p.line('M161 121 l-14 -7 M167 106 l-10 -15 M178 98 l-4 -14',ink,2.7);
  p.line('M398 83 l14 -7 M394 71 l10 -10',ink,2.4);
}
function conversation(c,p) {
  c.save(); c.translate(140,91); c.rotate(-.15);
  p.shape('M-61 -43 Q-75 -43 -75 -28 L-75 18 Q-75 34 -57 34 L-43 34 L-53 55 L-18 35 L47 35 Q64 35 64 16 L64 -25 Q64 -44 45 -44Z',ink);
  [-42,-7,28].forEach(x=>p.ellipse(x,-7,7,7,'#decdf7')); c.restore();
  c.save(); c.translate(254,108); c.rotate(.11);
  p.shape('M-62 -34 Q-71 -18 -67 6 Q-63 40 -14 44 Q10 47 32 37 L62 50 L53 24 Q73 5 65 -18 Q52 -56 0 -56 Q-47 -57 -62 -34Z','#f9f5df',ink,2.6);
  p.ellipse(-18,-11,4,7,ink); p.ellipse(12,-12,4,7,ink); p.line('M-28 5 Q-9 34 23 5',ink,3.5); c.restore();
  p.star(63,117,8); p.line('M285 35 l6 -13 M295 40 l12 -9 M300 48 l14 -3',ink,2.3);
}
function homes(c,p) {
  p.line('M61 145 Q182 142 330 146',ink,2);
  p.shape('M84 87 L121 52 L158 82 L158 143 L84 145Z','#fbf4db',ink,2.2);
  p.shape('M76 88 L119 42 L164 80 L157 87 L120 57 L84 96Z',ink);
  for(const x of [94,128])p.shape('M'+x+' 92h12v17h-12Z',ink);
  p.shape('M103 145v-25h17v25Z','#bc6c32',ink,1.5);
  p.shape('M151 62 L207 48 L211 144 L152 145Z','#f7ae68',ink,2.5);
  p.shape('M145 60 L214 43 L215 53 L145 71Z',ink);
  for(const x of [164,186])for(const y of [77,100])p.shape('M'+x+' '+y+'l10 -2v13l-10 2Z',ink);
  p.shape('M175 144v-20l13 -2v22Z',ink);
  p.shape('M211 91 L249 50 L291 87 L292 145 L211 144Z','#fcf3d7',ink,2.4);
  p.shape('M203 93 L249 42 L300 86 L293 94 L250 58 L212 101Z','#b94d2d',ink,2);
  p.ellipse(250,84,6,6,ink); p.shape('M225 104h15v17h-15Z',ink);
  p.shape('M254 144v-37h19v37Z','#92a176',ink,2);
  p.line('M312 143v-29 M312 134l-8 -10 M312 128l6 -7',ink,2.5);
  p.ellipse(312,110,13,22,'#89925e'); p.line('M312 144v-32 M312 128l6 -8 M312 123l-6 -7',ink,2);
  p.line('M76 47q6 -5 12 1q5 -9 12 -7 M268 28q5 -4 10 1q4 -6 10 -6',ink,2);
}
function sprout(c,p) {
  p.shape('M126 146 C135 132 152 136 167 125 Q188 116 208 129 Q231 125 252 147Z',ink);
  p.line('M187 133 Q187 107 203 80',ink,5);
  p.shape('M191 113 C163 114 149 100 146 82 Q179 77 192 103Z','#547d4e',ink,2);
  p.shape('M194 100 Q190 61 235 54 Q235 86 194 100Z','#8faa68',ink,2);
  p.line('M151 85l41 25 M195 98l35 -39',ink,1.7);
  c.save(); c.translate(111,59); c.rotate(.32); c.scale(.8,.8);
  p.line('M-29 -11 C-71 -30 -70 25 -32 22',ink,8);
  p.shape('M-39 -20 Q-6 -27 26 -20 L31 27 Q-2 40 -37 27Z','#f5a451',ink,2.8);
  p.shape('M23 6 L47 -17 L55 -11 L28 23Z','#f5a451',ink,2.5);
  p.ellipse(55,-15,6,11,ink,-.55); p.ellipse(-6,-20,32,5,ink); c.restore();
  p.line('M162 64l6 4 M160 73l6 4 M171 70l6 4 M171 82l5 4','#426861',2.3);
  p.star(272,88,10); p.star(253,45,5);
}
function heart(c,p) {
  c.save(); c.translate(194,87); c.rotate(-.15);
  p.shape('M0 59 C-96 2 -60 -59 -22 -46 Q-7 -41 0 -25 Q18 -60 45 -45 C91 -19 57 25 0 59Z',orange,ink,2.5);
  p.ellipse(-10,-5,4,7,ink);p.ellipse(12,-5,4,7,ink);p.line('M-15 10 Q0 28 18 9',ink,3);c.restore();
  p.star(107,67,12);p.star(281,103,10);
}
function book(c,p) {
  p.shape('M80 53 Q139 42 186 65 Q238 38 298 46 L302 133 Q246 127 192 149 Q138 128 85 139Z',ink);
  p.shape('M84 43 Q143 32 187 57 L191 138 Q145 113 83 125Z',paper,ink,2.5);
  p.shape('M187 57 Q245 29 295 40 L295 120 Q250 113 191 138Z','#ed9963',ink,2.5);
  for(let i=0;i<4;i++)p.line('M99 '+(60+i*13)+'q41 -5 70 10',ink,2);
  p.star(243,80,20);
}
function reuse(c,p) {
  p.shape('M114 72 L180 47 L258 65 L194 96Z','#efc98a',ink,2.5);
  p.shape('M114 72 L194 96 L193 150 L115 125Z','#e9af65',ink,2.5);
  p.shape('M194 96 L258 65 L258 120 L193 150Z','#c48e4e',ink,2.5);
  p.shape('M114 72 L94 53 L157 28 L180 47Z',paper,ink,2.5);
  p.shape('M194 96 L217 107 L279 79 L258 65Z',paper,ink,2.5);
  p.line('M213 43 Q242 13 272 36 M266 22l8 15 -16 0',ink,3);
  p.star(92,106,9);
}
const pictures={flower,conversation,homes,sprout,heart,book,reuse};
function grain(c,w,h,hero) {
  // Deterministic ink flecks leave a tactile surface without external images.
  let seed=90867;
  const r=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
  c.save(); if(hero)c.globalCompositeOperation='source-atop';
  for(let i=0;i<(hero?21000:9500);i++){
    const x=r()*w,y=r()*h,a=r();
    c.fillStyle=a>.28?'rgba(255,250,224,'+(a*.45)+')':'rgba(42,40,26,.15)';
    const size=.22+r()*.8; c.fillRect(x,y,size,size*(.5+r()));
  }c.restore();
}
export function paint(canvas) {
  const name=canvas.dataset.art, hero=name==='flower', w=hero?515:380,h=hero?340:174;
  const box=canvas.getBoundingClientRect(), dpr=Math.min(window.devicePixelRatio||1,2);
  canvas.width=Math.round(box.width*dpr);canvas.height=Math.round(box.height*dpr);
  if(!canvas.width||!canvas.height)return;
  const c=canvas.getContext('2d');const scale=Math.min(canvas.width/w,canvas.height/h);
  c.translate((canvas.width-w*scale)/2,(canvas.height-h*scale)/2);c.scale(scale,scale);
  c.lineCap='round';c.lineJoin='round';pictures[name](c,painter(c));grain(c,w,h,hero);
}
