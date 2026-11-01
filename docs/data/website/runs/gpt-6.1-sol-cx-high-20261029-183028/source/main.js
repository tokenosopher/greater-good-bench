const paths = {
  arrow: '<path d="M4 12h15m-6-6 6 6-6 6"/>',
  diagonal: '<path d="M6 18 18 6M6 6h12v12"/>',
  heart: '<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
  bookmark: '<path d="M6 4a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v17l-6-4-6 4Z"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  leaf: '<path d="M20 3C10 2 3 6 4 13c1 7 11 9 14 1 1-3 0-7 2-11Z"/><path d="m3 21 11-11"/>',
  people: '<circle cx="9" cy="7" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 4a3 3 0 0 1 0 6m3 11v-3a6 6 0 0 0-3-5"/>',
  home: '<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-7h6v7"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>',
  shuffle: '<path d="m18 3 3 3-3 3M3 6h3c5 0 7 12 12 12h3m-3-3 3 3-3 3M3 18h3c2 0 3.5-2 5-5m2-2c1.5-3 3-5 5-5h3"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  close: '<path d="m6 6 12 12M6 18 18 6"/>',
  chevron: '<path d="m7 10 5 5 5-5"/>',
  plus: '<path d="M12 5v14M5 12h14"/>',
  globe: '<circle cx="12" cy="12" r="9"/><ellipse cx="12" cy="12" rx="4" ry="9"/><path d="M3 12h18"/>',
  menu: '<path d="M4 7h16M4 12h16M4 17h16"/>',
};
const icon = (name, cls = '') => `<svg class="icon ${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[name] || paths.heart}</svg>`;
const flower = `<svg viewBox="0 0 40 40" fill="currentColor" aria-hidden="true"><path d="M20 15C8-5 0 12 14 20-5 32 12 40 20 26c12 19 20 2 6-6C45 8 28 0 20 15Z"/></svg>`;

const heroArt = `<svg class="hero-art" viewBox="0 0 580 450" fill="none" role="img" aria-label="A hand gently holding a green world, with a flower growing from it">
  <defs><clipPath id="world-clip"><circle cx="281" cy="217" r="132"/></clipPath><pattern id="paper" width="5" height="5" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".55" fill="#314e3f" opacity=".1"/></pattern></defs>
  <path d="M83 241C53 162 114 71 226 54c136-20 284 84 284 206 0 96-116 164-248 139" stroke="#a9b6a0" stroke-width="1.3" stroke-dasharray="5 7"/>
  <path d="m75 239 10 6 1-12" stroke="#a9b6a0" stroke-width="1.3"/>
  <circle cx="281" cy="217" r="132" fill="#a8bca4"/>
  <g clip-path="url(#world-clip)">
    <path d="m157 130 46-21 35 12 13 24-18 23-1 25-24 7-4 25-20 3-8-31-31-14Zm51 114 26-15 28 20 20 6 3 24-20 24-5 39-20 15-15-27 1-28-20-23ZM315 87l40 17 6 28 29 16 32 3 13 37-33 23-29-12-13 17-19-9-6-33-29-13-22-25 9-20Zm19 133 28-7 23 20-10 37-20 29-16-17-5-27-18-12Zm62 78 27-7 16 20-8 23-38-4-7-16Z" fill="#f1efda"/>
    <ellipse cx="281" cy="217" rx="67" ry="132" stroke="#44634f" stroke-width="1" opacity=".5"/>
    <ellipse cx="281" cy="217" rx="109" ry="132" stroke="#44634f" stroke-width="1" opacity=".25"/>
    <path d="M144 217h274M159 159c80 20 161 20 245 0M159 276c80-20 161-20 245 0M191 115c59 15 118 15 180 0M191 320c59-15 118-15 180 0" stroke="#44634f" stroke-width="1" opacity=".4"/>
    <circle cx="281" cy="217" r="132" fill="url(#paper)"/>
  </g>
  <circle cx="281" cy="217" r="132" stroke="#41634d" stroke-width="1.3"/>
  <path d="M324 104c3-29 9-51 21-70" stroke="#2d4c3b" stroke-width="5" stroke-linecap="round"/>
  <path d="M335 70c-28 4-45-10-45-28 26-2 43 7 45 28Zm6-14c22 1 36-8 39-26-23-2-36 8-39 26Z" fill="#375b43"/>
  <g transform="translate(350 32)"><path d="M0-6C-30-35-40-6-17 4c-33 8-17 37 6 23-6 33 27 31 27 5 22 25 41-3 16-17 33-4 23-35-2-23 12-31-21-39-24-13Z" fill="#dc7450"/><circle cx="7" cy="8" r="13" fill="#f7cd73"/><circle cx="7" cy="8" r="7" stroke="#ae512e" stroke-width="1" stroke-dasharray="1 3"/></g>
  <path d="m463 429-75-53c-19-12-45-12-70-10l-70 4c-16 1-34-8-45-15l-42-29c-15-10-18-22-10-29 7-7 18-3 29 3l42 20c9 4 21 6 33 4l43-7c12-2 15-10 10-16-4-5-12-5-23-4l-31 1c-17 1-30-5-30-15 0-8 7-11 18-12l69-3c25-1 48 3 64 16l80 64" fill="#d68a69" stroke="#7f4938" stroke-width="1.4" stroke-linejoin="round"/>
  <path d="m186 313 38 24c10 6 20 10 30 10m-93-21 38 25c11 7 21 11 33 14m111-48c13-1 25 0 35 4" stroke="#9b5b44" stroke-width="1.4" stroke-linecap="round"/>
  <path d="m410 388 42-63 68 45-42 63Z" fill="#374f41"/>
  <path d="m422 396 42-63M437 407l42-64M453 418l41-64" stroke="#759075" stroke-width="1"/>
  <path d="m102 102 8-24 8 24 24 8-24 8-8 24-8-24-24-8Z" fill="#f0c66c"/>
  <path d="m459 171 5-14 5 14 14 5-14 5-5 14-5-14-14-5Z" fill="#bc654b"/>
  <path d="M447 81c-15-19-34 3-21 14l22 16 17-23c11-17-10-30-18-7Z" fill="#e7b8a3" stroke="#b16d54" stroke-width="1.2"/>
  <circle cx="131" cy="285" r="4" fill="#bd6646"/><circle cx="424" cy="244" r="3" fill="#d5ac59"/>
  <g transform="translate(61 352) rotate(-8)"><rect width="192" height="47" rx="3" fill="#f9f7ee" stroke="#d4d4bf"/><path d="m15 26 5 5 9-13" stroke="#45654d" stroke-width="1.5"/><text x="40" y="29" font-family="'DM Sans Variable', sans-serif" font-size="13" fill="#3c5140">A little goes a long way.</text></g>
  <path d="M83 323c-20-10-24-30-16-44m-1 14 1-14 12 7" stroke="#67785e" stroke-width="1.2" stroke-linecap="round"/>
</svg>`;

const illustrations = {
  people: `<svg viewBox="0 0 360 160" fill="none" aria-hidden="true"><path d="M97 151c-2-22 5-40 22-51 16-11 36-10 51 0l23 18-24 37" fill="#db8b6e"/><path d="m263 151-10-36c-4-17-18-28-35-28-15 0-31 10-35 27l-9 37" fill="#607c62"/><path d="M118 105c-12 6-18 21-19 46h48l9-35" fill="#e9b76d"/><path d="M140 84c17 0 27-19 20-34-4-9-19-14-30-6-15 10-8 40 10 40Z" fill="#d88d70"/><path d="M124 58c-1-23 35-29 39-7 1 10-4 15-4 15l-6-13-10 5-6-5Z" fill="#344c3e"/><path d="M217 80c-19-1-25-26-14-38 9-9 26-5 31 6 6 13-1 32-17 32Z" fill="#e8b197"/><path d="M200 58c-7-12-1-24 13-26 15-1 28 11 24 28l-10-9-5-9-9 8-11-1Z" fill="#384f40"/><path d="m143 110 31 23 29-17" stroke="#d88d70" stroke-width="17" stroke-linecap="round"/><path d="m208 104-26 24-14-2" stroke="#e8b197" stroke-width="15" stroke-linecap="round"/><path d="M178 47c-14-17-30 2-17 13l18 14 16-18c12-14-9-26-17-9Z" fill="#b95940"/><path d="m109 48-8-7m7 18-11-1m145 29 10-2m-14-8 6-7" stroke="#8d9c78" stroke-width="1.5" stroke-linecap="round"/><ellipse cx="179" cy="152" rx="101" ry="4" fill="#526846" opacity=".12"/></svg>`,
  planet: `<svg viewBox="0 0 360 160" fill="none" aria-hidden="true"><ellipse cx="182" cy="144" rx="88" ry="5" fill="#526846" opacity=".12"/><path d="m123 95 14 46h87l14-46" fill="#ca7959"/><path d="m143 99 8 35m18-35 3 35m18-35-3 35m22-35-8 35" stroke="#f0ba91" stroke-width="2"/><path d="M118 90h125v13H118z" fill="#ae6149"/><path d="M147 87c-16-28-8-51 4-51 12-1 22 23 13 51" fill="#d5ae53"/><path d="M165 85c-7-40 17-56 28-43 10 11 8 29-2 46" fill="#e5bd62"/><path d="m165 86 19-36" stroke="#ae8b40" stroke-width="1.3"/><path d="M204 90c-18-10-22-32-7-37 17-5 21 17 13 37Z" fill="#df7f5d"/><path d="M205 54c-6-14 8-28 23-22-1 14-11 24-23 22Z" fill="#6d8c57"/><path d="M144 91c-23-11-30-34-14-41 13-5 25 15 21 40Z" fill="#75935e"/><path d="m130 59 15 30m50-47 4-20m-7 12-9-8m14 2 9-6" stroke="#56754c" stroke-width="2" stroke-linecap="round"/><path d="m249 53 4-10 4 10 10 4-10 4-4 10-4-10-10-4Z" fill="#d8af56"/><path d="m102 77-7-4m9-6-2-8" stroke="#80916e" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  community: `<svg viewBox="0 0 360 160" fill="none" aria-hidden="true"><ellipse cx="181" cy="146" rx="95" ry="4" fill="#526846" opacity=".12"/><path d="M117 90h131v54H117z" fill="#e2b88a"/><path d="m106 92 75-57 78 57Z" fill="#b96750"/><path d="M131 90h43v54h-43z" fill="#f5e7cc"/><path d="M190 95h39v49h-39z" fill="#64826a"/><path d="M203 108h13v15h-13z" fill="#f6e8cc"/><path d="M147 104h13v17h-13z" fill="#96af95"/><path d="M105 141h155v6H105z" fill="#a2a98c"/><path d="M95 135v-28m0 9c-17-1-22-13-18-23 14 1 21 10 18 23Zm0-8c-2-17 11-24 20-18 0 12-8 20-20 18Z" fill="#78916c"/><path d="M181 25c-10-13-22 2-13 10l13 11 13-14c8-10-7-19-13-7Z" fill="#d88c76"/><path d="m253 45 5-12 5 12 12 5-12 5-5 12-5-12-12-5Z" fill="#dcbb68"/><path d="m122 55-7-7m-2 17-10-1" stroke="#96a183" stroke-width="1.5" stroke-linecap="round"/></svg>`,
  self: `<svg viewBox="0 0 360 160" fill="none" aria-hidden="true"><circle cx="181" cy="76" r="48" fill="#ead29a"/><path d="M128 142c6-33 17-51 52-51 34 0 51 22 53 51" fill="#81987b"/><path d="M184 89c-17 1-27-21-22-37 4-14 24-17 34-6 13 16 3 42-12 43Z" fill="#d99374"/><path d="M159 62c-12-25 8-39 25-36 20 3 29 24 19 38l-10-15-13 5-5-11-10 17Z" fill="#3a5142"/><path d="m151 115 26 17 32-16" stroke="#d99374" stroke-width="14" stroke-linecap="round"/><path d="M170 111c-9-12-21 1-12 10l13 10 13-14c7-10-8-17-14-6Z" fill="#be6d55"/><path d="M117 86c-18 0-28-12-25-27 20-1 28 11 25 27Zm3 21c2-23 13-29 27-23-2 18-12 25-27 23Z" fill="#6e8b60"/><path d="M118 141V76" stroke="#6e8b60" stroke-width="2"/><path d="m244 56 5-12 5 12 12 5-12 5-5 12-5-12-12-5Z" fill="#c58264"/><ellipse cx="179" cy="145" rx="88" ry="4" fill="#526846" opacity=".12"/></svg>`,
};

const categories = {
  all: { name: 'All good', icon: 'sun' },
  people: { name: 'For people', short: 'People', icon: 'heart' },
  planet: { name: 'For the planet', short: 'Planet', icon: 'leaf' },
  community: { name: 'For your community', short: 'Community', icon: 'home' },
  self: { name: 'For yourself', short: 'Yourself', icon: 'sun' },
};
const actions = [
  { id: 'check-in', category: 'people', title: 'Make someone feel seen.', description: 'A small check-in can mean more than you know. Reach out to someone on your mind.', time: 5, tag: 'A little connection', steps: ['Think of someone you haven’t spoken to in a while, or someone who might appreciate a little company.', 'Send a personal message: “You crossed my mind today. How are you, really?”', 'Make room to listen. Let them share as much or as little as they like.'], tip: 'No perfect words needed. “Thinking of you” is a lovely place to start.' },
  { id: 'save-food', category: 'planet', title: 'Give good food a second chance.', description: 'That forgotten carrot has potential. Make a meal with what you already have.', time: 30, tag: 'Less waste, more good', steps: ['Take a look in your fridge and cupboard. Choose ingredients you already have that are safe to eat.', 'Build a simple meal around them: a soup, a stir-fry, a sandwich, or something of your own.', 'Put what needs using next at the front of your fridge, where you’ll remember it.'], tip: 'Keep it simple. A perfectly ordinary meal can be a perfectly good little act.' },
  { id: 'share-skill', category: 'community', title: 'Your know-how. Someone’s next step.', description: 'Everyone knows something worth sharing. Give someone a hand with what you know.', time: 30, tag: 'Good grows when shared', steps: ['Think of one useful thing you can help with: a recipe, a CV, a repair, a language, or a new tool.', 'Offer a friend, neighbour, or community group a short, specific session. Ask what they’d find useful.', 'Agree on a time, listen first, and let them try it for themselves.'], tip: 'You don’t have to be an expert to make something feel a little easier.' },
  { id: 'thank-you', category: 'people', title: 'Make your thank-you specific.', description: 'Tell someone exactly how their kindness or hard work made your day better.', time: 5, tag: 'Words that stay', steps: ['Choose someone whose effort you’ve noticed: a friend, a colleague, a neighbour, or a family member.', 'Name what they did and why it mattered to you.', 'Tell them directly, or write a little note they can keep.'], tip: 'Try: “When you did ___, it helped me ___. Thank you.”' },
  { id: 'little-cleanup', category: 'planet', title: 'Leave a place a little better.', description: 'Take a short walk and clear a few pieces of ordinary litter along the way.', time: 15, tag: 'Care for your corner', steps: ['Bring a bag and gloves or a litter picker on a familiar walk.', 'Pick up only ordinary litter you can safely handle. Leave sharp or unknown items for local services.', 'Sort and dispose of what you collect using your usual local bins. Wash your hands afterwards.'], tip: 'A small, familiar stretch is enough. You don’t have to clean the whole street.' },
  { id: 'pause', category: 'self', title: 'Give yourself a little breathing room.', description: 'Step away from the noise for a moment. Caring for yourself counts, too.', time: 5, tag: 'You’re part of the world, too', steps: ['Put your phone aside and find somewhere comfortable for a few minutes.', 'Notice your surroundings: a colour, a sound, the feeling of your feet on the floor. Breathe naturally.', 'Ask yourself what would make the next hour a little kinder. Choose one small thing.'], tip: 'There’s nothing to achieve here. You’re allowed a quiet moment.' },
  { id: 'lend', category: 'community', title: 'Open up your little library.', description: 'A book, a tool, a little equipment. Share something useful with someone nearby.', time: 15, tag: 'More sharing, less buying', steps: ['Choose something useful that you’re comfortable lending and that’s in good condition.', 'Offer it to someone you know, or ask a local sharing group whether anyone could use it.', 'Agree on how to use it and when to return it. Keep the arrangement simple and friendly.'], tip: 'A clear return date helps a small kindness stay a happy one.' },
  { id: 'listen', category: 'people', title: 'Be someone’s undivided attention.', description: 'Put your phone down. Give a conversation the space and attention it deserves.', time: 15, tag: 'Less scrolling, more listening', steps: ['Ask someone you know if they’d like to have a chat.', 'Put distractions away. Ask an open question and give them time to answer.', 'Listen without rushing to fix anything. Ask if they want ideas or simply someone to hear them.'], tip: 'Feeling heard can be a gift all by itself.' },
  { id: 'repair', category: 'planet', title: 'Choose a little repair.', description: 'Before replacing something, see if a simple, safe fix can give it more life.', time: 30, tag: 'Keep a good thing going', steps: ['Choose a small, safe repair you know how to do, like sewing on a button or patching a bag.', 'Gather what you need. If it’s beyond your skills, make a note to ask someone experienced.', 'Give the item another outing. A little imperfection has its own charm.'], tip: 'Start with textiles or everyday objects. Leave electrical and other hazardous repairs to a professional.' },
  { id: 'welcome', category: 'community', title: 'Make a little room for someone new.', description: 'Being new can feel lonely. A friendly invitation can make a place feel like home.', time: 5, tag: 'Belonging starts small', steps: ['Think of someone new to your workplace, building, class, or community.', 'Say hello and introduce yourself. Offer a useful local tip or a friendly invitation.', 'Keep it low-pressure. Let them know they’re welcome, whether or not they join today.'], tip: '“Would you like to join us?” is a small question that can open a big door.' },
  { id: 'walk', category: 'self', title: 'Take the scenic fifteen minutes.', description: 'Make a little time for fresh air and the everyday world around you.', time: 15, tag: 'A small reset', steps: ['Choose a familiar, accessible outdoor spot. A doorway, a garden, or a short route all count.', 'Move or sit at your own pace. Notice three things you’d normally pass by.', 'Come back when you’re ready. Take one of those small observations into the rest of your day.'], tip: 'This is yours to adapt. A view through an open window can count, too.' },
  { id: 'future-you', category: 'self', title: 'Do future you a small favour.', description: 'Take one little task off tomorrow’s shoulders. Leave yourself a softer landing.', time: 5, tag: 'Kindness, paid forward', steps: ['Think of one thing that might make tomorrow a little easier.', 'Spend a few minutes on it: fill a water bottle, lay out clothes, clear a surface, or write a short list.', 'Stop there. One helpful thing is enough for today.'], tip: 'Small and achievable is the whole idea.' },
];

let currentCategory = 'all';
let currentTime = 0;
let visibleCount = 3;
const saved = new Set();
const completed = new Set();
const stepsChecked = new Map();
let activeAction = null;
let previousFocus = null;
let toastTimer;

document.querySelector('#app').innerHTML = `
  <header class="site-header page-width">
    <a href="#" class="brand" aria-label="a little good home"><span class="brand-flower">${flower}</span>a little good<span class="brand-dot">.</span></a>
    <nav aria-label="Main navigation"><a class="nav-active" href="#find-your-good">Find your good</a><a href="#how-it-works">How it works</a><button class="nav-link" id="philosophy-button">Our little philosophy</button></nav>
    <button class="list-button" id="list-button">${icon('bookmark')}<span>My good list</span><span class="saved-count" hidden>0</span></button>
  </header>
  <main>
    <section class="hero page-width" aria-labelledby="hero-heading">
      <div class="hero-copy"><div class="eyebrow"><span class="small-spark">✳</span> A LITTLE KINDNESS HAS A RIPPLE EFFECT</div>
        <h1 id="hero-heading">Small acts.<br>A <em>better</em> world.</h1>
        <p>You don’t have to change everything to change something.<br class="desktop-break"> Find one small, meaningful thing you can do today.</p>
        <a class="button primary hero-cta" href="#find-your-good">Find my little good ${icon('arrow')}</a>
        <div class="hero-note"><span class="tiny-sun">${icon('sun')}</span> Good for others. Good for the planet. Good for you.</div>
      </div>
      <div class="hero-visual">${heroArt}<span class="art-note">a world of possibility</span></div>
    </section>
    <div class="good-strip"><div class="page-width strip-content"><span>${icon('clock')} A few minutes is a good start</span><span class="strip-star">✳</span><span>${icon('heart')} Little things mean a lot</span><span class="strip-star">✳</span><span>${icon('globe')} A better world is everyone’s business</span></div></div>
    <section class="action-section page-width" id="find-your-good" aria-labelledby="actions-heading">
      <div class="section-heading"><div><div class="eyebrow section-eyebrow">SMALL ENOUGH TO START. GOOD ENOUGH TO MATTER.</div><h2 id="actions-heading">What’s your little good today?</h2><p>Start where you are, with what you have. There’s a little good for everyone.</p></div><button class="surprise-button" id="surprise-button">${icon('shuffle')} Surprise me ${icon('diagonal')}</button></div>
      <div class="filters"><div class="category-tabs" role="group" aria-label="Choose a cause">${Object.entries(categories).map(([key, item]) => `<button class="category-tab ${key === 'all' ? 'active' : ''}" data-category="${key}" aria-pressed="${key === 'all'}">${icon(item.icon)}${item.name}</button>`).join('')}</div><label class="time-select">${icon('clock')}<select id="time-filter" aria-label="Time available"><option value="0">Any amount of time</option><option value="5">5 minutes or less</option><option value="15">15 minutes or less</option><option value="30">30 minutes or less</option></select>${icon('chevron')}</label></div>
      <div class="results-caption" id="results-caption" aria-live="polite"></div>
      <div class="action-grid" id="action-grid"></div>
      <div class="more-row"><span>A little inspiration. A world of ways to help.</span><button class="text-button" id="more-button">Explore more little acts ${icon('plus')}</button></div>
    </section>
    <section class="how-section page-width" id="how-it-works" aria-labelledby="how-heading"><div class="how-intro"><span class="eyebrow">NO GRAND GESTURE REQUIRED</span><h2 id="how-heading">Good starts<br>with one little thing.</h2><p>No scores. No perfect people.<br>Just a little more care, put into practice.</p><span class="how-flower">${flower}</span></div><div class="how-steps"><div><span class="step-number">01</span><div><h3>Find something that feels like you.</h3><p>A cause you care about. A few minutes you have.<br>Pick a small act that fits your day.</p></div></div><div><span class="step-number">02</span><div><h3>Make a little good happen.</h3><p>Follow the simple steps. Give it your own touch.<br>It doesn’t have to be perfect to make a difference.</p></div></div><div><span class="step-number">03</span><div><h3>Let the good keep going.</h3><p>Save an idea for later. Try something new tomorrow.<br>Small acts have a lovely way of adding up.</p></div></div></div></section>
    <section class="closing-section page-width"><span class="closing-spark">✳</span><p>“How wonderful it is that nobody need wait a single<br class="desktop-break"> moment before starting to improve the world.”</p><span>ANNE FRANK</span></section>
  </main>
  <footer class="site-footer page-width"><a href="#" class="brand"><span class="brand-flower">${flower}</span>a little good<span class="brand-dot">.</span></a><p>A little more kindness. A little more often.</p><button id="privacy-button">Made for people, not for profit ${icon('heart')}</button></footer>
  <dialog id="action-dialog" class="action-dialog" aria-labelledby="action-title"><button class="dialog-close" aria-label="Close action guide">${icon('close')}</button><div id="action-detail"></div></dialog>
  <dialog id="list-dialog" class="list-dialog" aria-labelledby="list-title"><button class="dialog-close" aria-label="Close my good list">${icon('close')}</button><div class="list-dialog-content"><div class="eyebrow">A LITTLE INTENTION, READY TO GO</div><h2 id="list-title">My good list<span>.</span></h2><p class="list-intro">Little things you’d like to put into the world.</p><div id="list-content"></div><p class="session-note">Just for this visit. Your list stays with you while this page is open.</p></div></dialog>
  <dialog id="info-dialog" class="info-dialog" aria-labelledby="info-title"><button class="dialog-close" aria-label="Close information">${icon('close')}</button><div id="info-content"></div></dialog>
  <div class="toast" id="toast" role="status"></div>
`;

function filteredActions() {
  return actions.filter(action => (currentCategory === 'all' || action.category === currentCategory) && (!currentTime || action.time <= currentTime));
}

function renderCards() {
  const focusedSave = document.activeElement?.dataset.save;
  const matching = filteredActions();
  const shown = matching.slice(0, visibleCount);
  document.querySelector('#action-grid').innerHTML = shown.map(action => `
    <article class="action-card ${action.category}">
      <div class="card-art"><button class="art-open" data-open="${action.id}" aria-label="Read the guide: ${action.title}">${illustrations[action.category]}</button><span class="category-label">${icon(categories[action.category].icon)}${categories[action.category].short}</span><button class="save-button ${saved.has(action.id) ? 'is-saved' : ''}" data-save="${action.id}" aria-label="${saved.has(action.id) ? 'Remove from' : 'Save to'} my good list: ${action.title}" aria-pressed="${saved.has(action.id)}">${icon(completed.has(action.id) ? 'check' : 'bookmark')}</button></div>
      <div class="card-content"><div class="card-tag">${action.tag}</div><h3><button data-open="${action.id}">${action.title}</button></h3><p>${action.description}</p><div class="card-bottom"><span>${icon('clock')} ${action.time} min <span class="meta-dot">·</span> No cost</span><button class="card-arrow" data-open="${action.id}" aria-label="Get started: ${action.title}">${icon(completed.has(action.id) ? 'check' : 'arrow')}</button></div></div>
    </article>`).join('') || `<div class="no-results"><span>${icon('sun')}</span><h3>A little more time opens up more possibilities.</h3><p>Try another cause, or explore ideas with a little more time. There’s good here for you.</p><button class="button secondary" id="reset-time">Explore all times ${icon('arrow')}</button></div>`;
  document.querySelector('#results-caption').textContent = `${matching.length} little acts${currentCategory !== 'all' ? ` ${categories[currentCategory].name.toLowerCase()}` : ' to make a difference'}${currentTime ? ` · ${currentTime} minutes or less` : ''}`;
  const moreButton = document.querySelector('#more-button');
  moreButton.hidden = visibleCount >= matching.length;
  const surpriseButton = document.querySelector('#surprise-button');
  surpriseButton.disabled = !matching.length;
  surpriseButton.title = matching.length ? 'Discover a random act that matches your choices' : 'Choose another cause or explore all times first';
  document.querySelector('.more-row > span').textContent = visibleCount >= matching.length ? 'There’s no rush. One little act is a lovely start.' : 'A little inspiration. A world of ways to help.';
  updateCounts();
  if (focusedSave) document.querySelector(`#action-grid [data-save="${focusedSave}"]`)?.focus({ preventScroll: true });
}

function updateCounts() {
  const count = document.querySelector('.saved-count');
  count.textContent = saved.size;
  count.hidden = !saved.size;
}

function notify(message) {
  const toast = document.querySelector('#toast');
  clearTimeout(toastTimer);
  toast.innerHTML = `${icon('check')}<span>${message}</span>`;
  toast.classList.add('visible');
  toastTimer = setTimeout(() => toast.classList.remove('visible'), 3200);
}

function toggleSave(id) {
  if (saved.has(id)) {
    saved.delete(id);
    notify('Removed from your good list.');
  } else {
    saved.add(id);
    notify('A little good, saved for later.');
  }
  renderCards();
  if (document.querySelector('#list-dialog').open) renderList();
  if (document.querySelector('#action-dialog').open) updateDetailButtons();
}

function openDialog(id) {
  previousFocus = document.activeElement;
  document.querySelector(id).showModal();
  document.body.classList.add('dialog-open');
}

function openAction(id, fromList = false) {
  if (fromList) document.querySelector('#list-dialog').close();
  activeAction = actions.find(action => action.id === id);
  const action = activeAction;
  const checks = stepsChecked.get(action.id) || new Set();
  document.querySelector('#action-detail').innerHTML = `<div class="detail-art ${action.category}">${illustrations[action.category]}<span class="category-label">${icon(categories[action.category].icon)}A little good for ${categories[action.category].short.toLowerCase()}</span></div><div class="detail-body"><span class="eyebrow">${action.tag}</span><h2 id="action-title">${action.title}</h2><p class="detail-description">${action.description}</p><div class="detail-meta"><span>${icon('clock')} ${action.time} minutes</span><span>${icon('heart')} No cost. Just a little care.</span></div><div class="steps-heading"><h3>Here’s a little place to start</h3><span id="step-progress">${checks.size} of ${action.steps.length}</span></div><div class="action-steps">${action.steps.map((step, index) => `<label class="action-step"><input type="checkbox" data-step="${index}" ${checks.has(index) ? 'checked' : ''}><span class="step-check">${icon('check')}</span><span>${step}</span></label>`).join('')}</div><div class="little-note">${icon('sun')}<p>${action.tip}</p></div><div class="detail-buttons"><button class="button primary" id="complete-action"></button><button class="detail-save" id="detail-save"></button></div><p class="honest-note">A personal intention, not a commitment. Make it work for you.</p></div>`;
  updateDetailButtons();
  openDialog('#action-dialog');
  if (fromList) previousFocus = document.querySelector('#list-button');
}

function updateDetailButtons() {
  if (!activeAction) return;
  const isDone = completed.has(activeAction.id);
  const completeButton = document.querySelector('#complete-action');
  completeButton.innerHTML = `${icon('check')} ${isDone ? 'A little good, done!' : 'I did this little good'}`;
  completeButton.disabled = isDone;
  const saveButton = document.querySelector('#detail-save');
  saveButton.innerHTML = `${icon(saved.has(activeAction.id) ? 'check' : 'bookmark')} ${saved.has(activeAction.id) ? 'Saved to my list' : 'Save for later'}`;
  saveButton.setAttribute('aria-pressed', String(saved.has(activeAction.id)));
}

function renderList() {
  const list = document.querySelector('#list-content');
  if (!saved.size) {
    list.innerHTML = `<div class="empty-list"><span class="empty-flower">${flower}</span><h3>A little room for good.</h3><p>See something you’d like to do?<br>Tap the bookmark to keep it here.</p><button class="button primary" id="empty-explore">Find my little good ${icon('arrow')}</button></div>`;
    return;
  }
  const doneCount = [...saved].filter(id => completed.has(id)).length;
  list.innerHTML = `<div class="list-summary">${icon('sun')}<span>${saved.size} little ${saved.size === 1 ? 'intention' : 'intentions'} <span>·</span> ${doneCount} made real</span></div><div class="saved-items">${[...saved].map(id => {
    const action = actions.find(a => a.id === id);
    return `<div class="saved-item ${completed.has(id) ? 'done' : ''}"><button class="saved-item-icon ${action.category}" data-list-open="${id}" aria-label="Open ${action.title}">${icon(completed.has(id) ? 'check' : categories[action.category].icon)}</button><button class="saved-item-title" data-list-open="${id}"><strong>${action.title}</strong><span>${completed.has(id) ? 'A little good, done' : `${action.time} min · ${categories[action.category].short}`}</span></button><button class="remove-saved" data-save="${id}" aria-label="Remove ${action.title} from your list">${icon('close')}</button></div>`;
  }).join('')}</div><button class="button secondary list-explore" id="empty-explore">Find another little good ${icon('plus')}</button>`;
}

function showInfo(kind) {
  const privacy = kind === 'privacy';
  document.querySelector('#info-content').innerHTML = `<span class="info-flower">${flower}</span><span class="eyebrow">${privacy ? 'A QUIETER CORNER OF THE INTERNET' : 'OUR LITTLE PHILOSOPHY'}</span><h2 id="info-title">${privacy ? 'Made for people.<br>Powered by kindness.' : 'A better world starts<br>with a little more care.'}</h2>${privacy ? `<p>No accounts, no ads, no tracking. Every idea and every guide is available right here, even offline.</p><p>Your good list and completed acts live only in this open page. They disappear when you reload or leave. We don’t store or send your information anywhere.</p><p>Nothing here makes a donation, contacts another person, or signs you up for anything. The good happens when you take an idea into your own world.</p>` : `<p>The world’s challenges can feel big. And small acts aren’t the whole answer. But they are a place to begin.</p><p>We believe a little time, a little attention, and a little generosity can make everyday life better for the people around us.</p><p>There are no points to collect and no streaks to keep. Choose what matters to you, adapt it to your life, and start wherever you are. Looking after yourself belongs here, too.</p><div class="philosophy-note">Small enough to start.<br>Good enough to matter.</div>`}<button class="button primary" id="info-explore">Find my little good ${icon('arrow')}</button>`;
  openDialog('#info-dialog');
}

document.addEventListener('click', event => {
  const categoryButton = event.target.closest('[data-category]');
  if (categoryButton) {
    currentCategory = categoryButton.dataset.category;
    visibleCount = 3;
    document.querySelectorAll('[data-category]').forEach(button => {
      const isActive = button.dataset.category === currentCategory;
      button.classList.toggle('active', isActive);
      button.setAttribute('aria-pressed', String(isActive));
    });
    renderCards();
  }
  const openButton = event.target.closest('[data-open]');
  if (openButton) openAction(openButton.dataset.open);
  const saveButton = event.target.closest('[data-save]');
  if (saveButton) toggleSave(saveButton.dataset.save);
  const listOpen = event.target.closest('[data-list-open]');
  if (listOpen) openAction(listOpen.dataset.listOpen, true);
  if (event.target.closest('.dialog-close')) event.target.closest('dialog').close();
  if (event.target.closest('#empty-explore, #info-explore')) {
    event.target.closest('dialog').close();
    document.querySelector('#find-your-good').scrollIntoView({ behavior: 'smooth' });
  }
  if (event.target.closest('#reset-time')) {
    currentTime = 0;
    document.querySelector('#time-filter').value = '0';
    renderCards();
    document.querySelector('#time-filter').focus({ preventScroll: true });
  }
});

document.querySelector('#time-filter').addEventListener('change', event => {
  currentTime = Number(event.target.value);
  visibleCount = 3;
  renderCards();
});
document.querySelector('#more-button').addEventListener('click', () => { visibleCount += 3; renderCards(); });
document.querySelector('#surprise-button').addEventListener('click', () => {
  const matching = filteredActions();
  if (!matching.length) return;
  const candidates = matching.length > 1 ? matching.filter(action => action.id !== activeAction?.id) : matching;
  openAction(candidates[Math.floor(Math.random() * candidates.length)].id);
});
document.querySelector('#list-button').addEventListener('click', () => { renderList(); openDialog('#list-dialog'); });
document.querySelector('#philosophy-button').addEventListener('click', () => showInfo('philosophy'));
document.querySelector('#privacy-button').addEventListener('click', () => showInfo('privacy'));
document.querySelector('#action-detail').addEventListener('change', event => {
  if (!event.target.matches('[data-step]')) return;
  const checks = stepsChecked.get(activeAction.id) || new Set();
  const step = Number(event.target.dataset.step);
  event.target.checked ? checks.add(step) : checks.delete(step);
  stepsChecked.set(activeAction.id, checks);
  document.querySelector('#step-progress').textContent = `${checks.size} of ${activeAction.steps.length}`;
});
document.querySelector('#action-detail').addEventListener('click', event => {
  if (event.target.closest('#detail-save')) toggleSave(activeAction.id);
  if (event.target.closest('#complete-action') && !completed.has(activeAction.id)) {
    completed.add(activeAction.id);
    saved.add(activeAction.id);
    updateDetailButtons();
    renderCards();
    notify('The world is a little better for having you in it.');
    const detail = document.querySelector('.detail-body');
    const celebration = document.createElement('div');
    celebration.className = 'celebration';
    celebration.setAttribute('aria-hidden', 'true');
    celebration.innerHTML = Array.from({ length: 16 }, (_, index) => `<span style="--i:${index};--x:${Math.sin(index * 2.4) * 220}px;--r:${index * 63}deg">✳</span>`).join('');
    detail.append(celebration);
    setTimeout(() => celebration.remove(), 1500);
  }
});
document.querySelectorAll('dialog').forEach(dialog => {
  dialog.addEventListener('click', event => {
    if (event.target === dialog) {
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) dialog.close();
    }
  });
  dialog.addEventListener('close', () => {
    if (!document.querySelector('dialog[open]')) {
      document.body.classList.remove('dialog-open');
      if (previousFocus?.isConnected && !previousFocus.closest('dialog')) {
        previousFocus.focus({ preventScroll: true });
      } else {
        const fallback = dialog.id === 'action-dialog' ? document.querySelector(`[data-open="${activeAction?.id}"]`) : null;
        (fallback || document.querySelector('#list-button')).focus({ preventScroll: true });
      }
    }
  });
});

renderCards();
