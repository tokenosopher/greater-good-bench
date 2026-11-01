import {
  FLAGS, BANNED, MOVES, FEELINGS, PHASES, SCENES, KIND, DRILLS, ORGS,
  dayIndex, flagsFor, analyze, composeParts, CRISIS_LINES, SAFETY_LINES
} from "./content.js"

const app = document.querySelector("#app")
const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches

const state = {
  banned: "but",
  feeling: null,
  breath: { running: false, cycle: 0, phase: 0, manual: 0 },
  practice: { id: null, beat: 0, choice: null, picks: [], started: false },
  drillOffset: 0,
  drillChoice: null,
  draft: { fact: "", own: "", hear: "", one: "" },
  lessPower: false,
  paste: "",
  alloc: { near: 6, story: 3, measured: 1 },
  monthly: "",
  week: { blood: false, money: false, skill: false, sick: false, across: false },
  sound: false
}

let breathTimer = 0
let breathRAF = 0
let audioCtx = null
let lastRoute = ""

function esc(s) {
  return String(s ?? "")
    .replace(/&/g, "\u0026amp;")
    .replace(/</g, "\u0026lt;")
    .replace(/>/g, "\u0026gt;")
    .replace(/"/g, "\u0026quot;")
}

function parse() {
  const raw = (location.hash || "#home").replace(/^#/, "") || "home"
  const parts = raw.split("/").filter(Boolean)
  return { raw, name: parts[0] || "home", parts }
}

function progressFor(route) {
  const map = {
    home: 0.1,
    moves: 0.34,
    here: 0.42,
    near: 0.48,
    practice: 0.62,
    words: 0.72,
    check: 0.72,
    speak: 0.84,
    far: 0.66,
    card: 1,
    crisis: 0.55,
    safety: 0.55
  }
  return map[route.name] ?? 0.2
}

function stitch() {
  return `<svg class="stitch" viewBox="0 0 220 18" aria-hidden="true" focusable="false">
    <path class="ink" d="M2 9 H98"/>
    <path class="ink" d="M122 9 H218"/>
    <path class="gold" d="M94 9 C104 9 106 3 112 3 C118 3 120 9 130 9"/>
  </svg>`
}

function currentNav(name) {
  const items = [
    ["moves", "Five moves", "#moves"],
    ["near", "Near", "#near"],
    ["words", "The words", "#words"],
    ["far", "Far", "#far"],
    ["card", "The card", "#card"]
  ]
  const links = items.map(([id, label, href]) => {
    const on = name === id || (id === "words" && (name === "check" || name === "speak")) || (id === "near" && name === "practice")
    return `<a href="${href}"${on ? ' aria-current="page"' : ""}>${label}</a>`
  }).join("")
  return `${links}<a class="danger" href="#crisis">In danger</a>`
}

function shell(html, route, title) {
  const dim = route.name === "speak"
  document.body.dataset.theme = dim ? "dim" : "paper"
  const p = progressFor(route)
  document.body.style.setProperty("--p", String(p))
  const line = document.getElementById("mendline")
  if (line) line.style.transform = `scaleX(${p})`
  document.title = title ? `${title} — Mend` : "Mend — the second try"
  app.innerHTML = `
    <div class="wrap">
      <header class="top">
        <a class="brand" href="#home">Mend</a>
        <nav class="nav" aria-label="Sections">${currentNav(route.name)}</nav>
      </header>
      <main id="main">${html}</main>
      <footer class="foot">
        <p>Nothing you type is saved. Nothing is sent. A practice, not therapy, not medicine, not an emergency service.</p>
        <p><a href="#crisis">If someone might die — including you — go here.</a></p>
      </footer>
    </div>`
}

function focusHeading(mode) {
  const live = document.getElementById("live")
  const title = document.title.replace(/ — Mend$/, "")
  if (live) live.textContent = title
  if (mode === "choice") {
    const c = document.getElementById("consequence")
    if (c) {
      c.tabIndex = -1
      c.focus({ preventScroll: true })
    }
  }
}

function render(mode = "route") {
  stopBreath()
  const route = parse()
  const y = mode === "stay" ? window.scrollY : 0
  if (route.name === "home") viewHome(route)
  else if (route.name === "moves") viewMoves(route)
  else if (route.name === "here") viewHere(route)
  else if (route.name === "near") viewNear(route)
  else if (route.name === "practice") viewPractice(route)
  else if (route.name === "words") viewWords(route)
  else if (route.name === "check") viewCheck(route)
  else if (route.name === "speak") viewSpeak(route)
  else if (route.name === "far") viewFar(route)
  else if (route.name === "card") viewCard(route)
  else if (route.name === "crisis") viewCrisis(route)
  else if (route.name === "safety") viewSafety(route)
  else viewMissing(route)
  if (mode === "route") window.scrollTo(0, 0)
  else if (mode === "stay") window.scrollTo(0, y)
  if (mode !== "stay") focusHeading(mode)
  lastRoute = route.raw
  if (route.name === "words" || route.name === "check") {
    updateLetter()
    updateFlags()
    updatePaste()
  }
  if (route.name === "far") updateFarCopy()
}

function viewHome(route) {
  shell(`
    <section class="hero">
      <div>
        <p class="kicker">Ten minutes to learn · one minute to use</p>
        <h1>Most of the good<br>in a life is a<br><em>second try.</em></h1>
        ${stitch()}
        <p class="lede">When something breaks — in you, between two people, or in the part of the world you can still reach — the next minute does more good than the last one.</p>
        <p class="mnemonic">Steady <i>·</i> Fact <i>·</i> Own <i>·</i> Hear <i>·</i> One</p>
        <p class="mnemonic-sub small"><a href="#moves">The five moves</a>, if you have ten minutes. The <a href="#card">card</a>, if you have one. The <a href="#words">words</a>, if you are about to speak.</p>
      </div>
      <nav class="doors" aria-label="Three distances">
        <a class="door" href="#here">
          <span class="num">01</span>
          <span><strong>Here</strong><em>Come back into your body before you speak, decide, or send.</em></span>
        </a>
        <a class="door" href="#near">
          <span class="num">02</span>
          <span><strong>Near</strong><em>Repair what you broke, or stay with someone who is hurting. Know when not to apologize.</em></span>
        </a>
        <a class="door" href="#far">
          <span class="num">03</span>
          <span><strong>Far</strong><em>Point blood, money, and attention at harm that is common, deadly, and preventable.</em></span>
        </a>
      </nav>
    </section>
    <p class="thesis">Here, near, and far are the same skill: attention, returned to what was about to be dropped.</p>
    <p class="small" style="max-width:44rem">Most preventable cruelty is ordinary. A flooded person hits send. A proud person adds “but.” A frightened friend is met with advice. A spare dollar follows a story instead of a result. None of that requires villains. It requires a better next minute. If everyone got that minute right a little more often, ordinary life would hurt less — and fewer people would die of things we already know how to prevent.</p>
  `, route, "The second try")
}

function viewMoves(route) {
  const items = MOVES.map((m) => `
    <li>
      <span class="num">${m.n}</span>
      <div>
        <h2>${m.name}</h2>
        <p>${m.body}</p>
        <p class="say"><b>Not this</b> ${esc(m.not)}</p>
        <p class="say do"><b>This</b> ${esc(m.yes)}</p>
      </div>
    </li>`).join("")
  const chips = BANNED.map((b) => `
    <button type="button" class="chip" data-act="banned" data-id="${b.id}" aria-pressed="${state.banned === b.id}">${esc(b.word)}</button>`).join("")
  const why = BANNED.find((b) => b.id === state.banned) || BANNED[0]
  shell(`
    <article class="page-intro">
      <p class="kicker">The practice</p>
      <h1>Five moves.</h1>
      <p class="lede">Research on apologies keeps finding the same bones: responsibility, the harm as they lived it, and a repair — without a “but.” This is that shape, short enough to remember when your pulse is up.</p>
    </article>
    <ol class="moves">${items}</ol>
    <section class="bench" aria-labelledby="undo-title">
      <h2 id="undo-title">Words that undo a mend</h2>
      <p class="small">Tap one. They are common because they work — on you. They relieve you of the sharper sentence. The other person is left holding the original break, plus a new one.</p>
      <div class="chips" role="group" aria-label="Phrases that undo a repair">${chips}</div>
      <p class="why-panel" id="why-panel">${esc(why.why)}</p>
    </section>
    <p class="actions"><a class="btn" href="#near">Practice with a scene</a> <a class="btn secondary" href="#words">Write the real one</a></p>
  `, route, "Five moves")
}

function viewHere(route) {
  const id = route.parts[1] && FEELINGS[route.parts[1]] ? route.parts[1] : null
  state.feeling = id
  const feelings = Object.entries(FEELINGS).map(([key, f]) => `
    <a class="feel" href="#here/${key}"${id === key ? ' aria-current="true"' : ""}>${f.name}</a>`).join("")
  const f = id ? FEELINGS[id] : null
  const done = state.breath.manual >= 3
  shell(`
    <article class="page-intro">
      <p class="kicker">Here · your body first</p>
      <h1>${f ? esc(f.name) + "." : "Before the sentence."}</h1>
      <p class="lede">${f ? esc(f.lead) : "A flooded person does ordinary damage: the message, the snap, the silence, the joke. Steady is not a mood. It is a sequence. Name what is in the room, then pick the thread back up."}</p>
      <div class="feelings" role="navigation" aria-label="Name the state">${feelings}</div>
      ${f ? "" : `<p class="small">If this is only the body sounding an alarm — heart racing, no story about a person — you do not owe anyone a message. Stay with the exhale. It crests, and it falls. It has before.</p>`}
    </article>
    ${f ? breathBlock(f, done) : ""}
  `, route, "Here")
}

function breathBlock(f, done) {
  const grief = state.feeling === "grief"
  return `
    <section class="thread-wrap" aria-labelledby="sigh-title">
      <h2 id="sigh-title" class="phase-name" data-phase-name>${done ? "Enough for now." : "Pick the thread up."}</h2>
      <p data-phase-detail class="lede">${done ? esc(f.after) : "A physiological sigh: two inhales through the nose, then a long exhale through the mouth. Three times. It is a studied way to tell the body the threat can stand down. It is not a cure, and it is not permission to skip a hard fact."}</p>
      <svg viewBox="0 0 520 86" aria-hidden="true" id="thread">
        <path id="thread-path" class="thread-ink" d="M16 26 Q260 52 504 26"/>
        <circle class="thread-knot" cx="16" cy="26" r="2.4"/>
        <circle class="thread-knot" cx="504" cy="26" r="2.4"/>
      </svg>
      <div class="dots" aria-hidden="true">
        <i class="${state.breath.manual > 0 || state.breath.cycle > 0 ? "on" : ""}"></i>
        <i class="${state.breath.manual > 1 || state.breath.cycle > 1 ? "on" : ""}"></i>
        <i class="${state.breath.manual > 2 || state.breath.cycle > 2 ? "on" : ""}"></i>
      </div>
      <div class="row">
        ${reduce ? `<button type="button" class="btn" data-act="breath-manual">${done ? "Count three more" : "I finished one sigh"}</button>` : `<button type="button" class="btn" data-act="breath-start">Guide three sighs</button>`}
        <button type="button" class="btn secondary" data-act="sound" aria-pressed="${state.sound}">${state.sound ? "Sound on" : "Sound off"}</button>
      </div>
      <p class="small" id="breath-status">${reduce ? "Motion is reduced. Count them yourself: inhale, a short second inhale, long exhale. Mark each one." : "About twenty-five seconds. You can stop. The point is warmer hands, not a performance."}</p>
      <div class="actions">
        ${grief
          ? `<p>If you tell someone, this is enough: <em>“I don’t need fixing. I need company. Can you sit with me, or check on me tomorrow?”</em></p><a class="btn secondary" href="#crisis">If it is darker than grief</a>`
          : `<a class="btn" href="#words">Write it only if your hands are warmer</a> <a class="btn secondary" href="#near">Someone is on the other side</a>`}
      </div>
    </section>`
}

function viewNear(route) {
  const drill = currentDrill()
  const opts = drill.options.map((o, i) => `
    <button type="button" class="line ${state.drillChoice === i ? "is-chosen" : ""} ${state.drillChoice !== null && state.drillChoice !== i ? "is-dimmed" : ""}" data-act="drill" data-i="${i}">
      <span class="key">${i + 1}</span>${esc(o.say)}
    </button>`).join("")
  const chosen = state.drillChoice !== null ? drill.options[state.drillChoice] : null
  shell(`
    <article class="page-intro">
      <p class="kicker">Near · the person in the room</p>
      <h1>The break you can still reach.</h1>
      <p class="lede">Most harm that ruins an ordinary week is not malice. It is a rupture nobody knew how to repair — or a repair attempted from pride, panic, or a need to be comforted for having caused pain.</p>
      <div class="callout">
        <p><strong>If you are afraid of them, do not polish the apology.</strong> A cleaner “sorry” is the wrong tool in a house where the truth is punished. <a href="#safety">Go to safety, not to phrasing.</a></p>
      </div>
      <p class="small">If they have less power than you — a child, an employee, anyone who cannot leave — add one sentence to whatever you say: you are allowed to be upset with me, and you are safe.</p>
    </article>
    <section aria-labelledby="drill-title">
      <p class="kicker" id="drill-title">Thirty seconds · ${esc(drill.title)}</p>
      <p class="lede">${esc(drill.setup)}</p>
      <div class="lines">${opts}</div>
      ${chosen ? `<div class="consequence" id="consequence" tabindex="-1"><p class="kind ${chosen.kind}">${KIND[chosen.kind]}</p><p>${esc(chosen.note)}</p></div>` : `<p class="small">Press 1–3. None of these is a grade. They are weather you can learn to recognize.</p>`}
      <p><button type="button" class="btn secondary" data-act="drill-another">Another situation</button></p>
    </section>
    <ul class="catalog">
      <li><a href="#practice/joke"><span class="tag">Practice</span><span><strong>The joke</strong><span>You spent them for a laugh, in front of other people.</span></span></a></li>
      <li><a href="#practice/silence"><span class="tag">Practice</span><span><strong>The silence</strong><span>They asked you to talk. You saw the message. You waited four days.</span></span></a></li>
      <li><a href="#practice/couch"><span class="tag">Stay</span><span><strong>The couch</strong><span>Someone is hurting, and advice would be a way of leaving.</span></span></a></li>
      <li><a href="#words"><span class="tag">Use it</span><span><strong>The words</strong><span>Write the real one. The page will warn you when a phrase undoes it.</span></span></a></li>
      <li><a href="#crisis"><span class="tag">Danger</span><span><strong>If they might die</strong><span>Ask plainly. Stay. Get more help than you. Do not swear secrecy.</span></span></a></li>
    </ul>
  `, route, "Near")
}

function currentDrill() {
  const i = (dayIndex() + state.drillOffset) % DRILLS.length
  return DRILLS[i]
}

function syncPractice(id) {
  if (state.practice.id !== id) {
    state.practice = { id, beat: 0, choice: null, picks: [], started: false }
  }
}

function viewPractice(route) {
  const id = route.parts[1]
  const scene = SCENES[id]
  if (!scene) {
    viewMissing(route)
    return
  }
  syncPractice(id)
  const p = state.practice
  if (!p.started) {
    shell(`
      <article class="scene">
        <p class="kicker">Near · ${esc(scene.title)} · about ${scene.minutes} minutes</p>
        <h1>${esc(scene.title)}.</h1>
        <p class="lede">${esc(scene.setting)}</p>
        <p>Three things you might say, then the next moment. The stronger sentence is not marked. Choose the one you would actually say with your pulse up — then look at what it does.</p>
        <p class="actions"><button type="button" class="btn" data-act="practice-start">Begin</button> <a class="btn secondary" href="#moves">Remind me of the moves</a></p>
      </article>
    `, route, scene.title)
    return
  }
  if (p.beat >= scene.beats.length) {
    const strong = p.picks.filter((k) => k === "strong").length
    const all = strong === p.picks.length
    const couch = id === "couch"
    shell(`
      <article class="scene">
        <p class="kicker">Near · ${esc(scene.title)}</p>
        <h1>${all ? "You had the sentences." : "You reached for the defense."}</h1>
        <p class="lede">${all
          ? "The practice is using them when you want relief more than you want a better outcome. Wanting relief is human. Sending it is optional."
          : "Everyone reaches. The skill is noticing the reach — the joke, the “but,” the self-portrait — and choosing the other sentence before it leaves your mouth."}</p>
        ${couch ? `<div class="callout"><p>If any of that was real, stop practicing. <a href="#crisis">Ask, stay, and get more help than you.</a></p></div>` : ""}
        <div class="row">
          <a class="btn" href="#words">Write the real one</a>
          <button type="button" class="btn secondary" data-act="practice-reset">Practice again</button>
          <a class="btn secondary" href="#near">Other scenes</a>
        </div>
      </article>
    `, route, scene.title)
    return
  }
  const beat = scene.beats[p.beat]
  const chosen = p.choice === null ? null : beat.options[p.choice]
  const options = beat.options.map((o, i) => `
    <button type="button" class="line ${p.choice === i ? "is-chosen" : ""} ${p.choice !== null && p.choice !== i ? "is-dimmed" : ""}" data-act="choose-line" data-i="${i}" ${p.choice !== null ? "disabled" : ""}>
      <span class="key">${i + 1}</span>${esc(o.say)}
    </button>`).join("")
  shell(`
    <article class="scene">
      <p class="kicker">Near · ${esc(scene.title)} · ${p.beat + 1} of ${scene.beats.length}</p>
      <h1>${esc(beat.prompt)}</h1>
      ${p.beat === 0 ? `<p class="muted">${esc(scene.setting)}</p>` : ""}
      <div class="lines" id="options">${options}</div>
      ${chosen ? `
        <div class="consequence" id="consequence" tabindex="-1">
          <p class="kind ${chosen.kind}">${KIND[chosen.kind]}</p>
          ${chosen.response ? `<blockquote class="said">${esc(chosen.response)}</blockquote>` : ""}
          <p>${esc(chosen.note)}</p>
          <div class="row">
            <button type="button" class="btn secondary" data-act="retry">Try another sentence</button>
            <button type="button" class="btn" data-act="next-beat">${p.beat === scene.beats.length - 1 ? "See where this lands" : "Continue"}</button>
          </div>
        </div>` : `<p class="small">Press 1, 2, or 3. You can try another sentence after.</p>`}
    </article>
  `, route, scene.title)
}

function viewWords(route) {
  const d = state.draft
  shell(`
    <div class="split">
      <section>
        <p class="kicker">The words · a repair you can say</p>
        <h1>Be specific. Then stop.</h1>
        <p>You do not have to feel ready. You have to be specific. Drafting is not sending. Read it aloud once. If your hands are still cold, do not send it — <a class="inline" href="#here">steady first</a>.</p>
        <label class="field">
          <span class="lbl">The fact <em>What a camera would have seen. One or two sentences.</em></span>
          <textarea data-field="fact" rows="2" autocomplete="off" placeholder="I left your message unread for four days.">${esc(d.fact)}</textarea>
          <span data-flag-for="fact"></span>
        </label>
        <label class="field">
          <span class="lbl">Your part <em>The choice, not the costume. No “but.”</em></span>
          <textarea data-field="own" rows="2" autocomplete="off" placeholder="I saw it, and I chose my fear over your wait.">${esc(d.own)}</textarea>
          <span data-flag-for="own"></span>
        </label>
        <label class="field">
          <span class="lbl">What you want to hear <em>A question about their experience. Then you stop talking.</em></span>
          <textarea data-field="hear" rows="2" autocomplete="off" placeholder="What was the hardest part of those four days?">${esc(d.hear)}</textarea>
          <span data-flag-for="hear"></span>
        </label>
        <label class="field">
          <span class="lbl">One request <em>A next behavior. Not forgiveness.</em></span>
          <textarea data-field="one" rows="2" autocomplete="off" placeholder="Next time I will answer the same day, even if only to say I saw it.">${esc(d.one)}</textarea>
          <span data-flag-for="one"></span>
        </label>
        <label class="check">
          <input type="checkbox" data-act="power" ${state.lessPower ? "checked" : ""}>
          <span>They have less power than I do — a child, an employee, someone who cannot easily leave.</span>
        </label>
        <p class="small"><a href="#safety">If you are afraid of them, this is the wrong page.</a> <a href="#check">I already wrote a draft — check it.</a></p>
      </section>
      <aside class="letter" aria-live="polite">
        <p class="kicker">Said slowly</p>
        <h2>The repair</h2>
        <div id="letter-body"></div>
        <p class="small" id="say-time"></p>
        <div class="row">
          <a class="btn" href="#speak">Make it large enough to say</a>
          <button type="button" class="btn secondary" data-act="copy">Copy</button>
        </div>
        <p class="small" id="copy-status"></p>
      </aside>
    </div>
  `, route, "The words")
}

function viewCheck(route) {
  shell(`
    <article class="page-intro">
      <p class="kicker">The words · check a draft</p>
      <h1>Read it as they will.</h1>
      <p class="lede">Paste what you were about to send. This does not store it, and it does not leave the page. It looks for the phrases that usually undo a mend, and for the signs you already own the thing.</p>
      <label class="field">
        <span class="lbl">The draft</span>
        <textarea id="paste" rows="8" autocomplete="off" placeholder="I’m sorry if you felt ignored, but I was slammed…">${esc(state.paste)}</textarea>
      </label>
      <div id="paste-notes"></div>
      <p class="actions"><a class="btn" href="#words">Build a cleaner one</a> <a class="btn secondary" href="#moves">The five moves</a></p>
    </article>
  `, route, "Check a draft")
}

function viewSpeak(route) {
  const parts = composeParts(state.draft, state.lessPower)
  const body = parts.empty
    ? `<p class="muted">There is nothing drafted yet. Go back and write the fact, or say only this: “I want to repair something. I will be specific. I will listen before I explain.”</p>`
    : parts.paragraphs.map((p) => `<p>${esc(p)}</p>`).join("")
  shell(`
    <article>
      <p class="kicker">Say it, then stop</p>
      <h1>Aloud.</h1>
      <div class="tele" id="letter-body">${body}</div>
      <p class="small" id="say-time">${parts.empty ? "" : `About ${parts.seconds} seconds, said slowly.`}</p>
      <div class="row">
        <a class="btn" href="#words">Edit</a>
        <button type="button" class="btn secondary" data-act="copy">Copy</button>
      </div>
      <p class="small" id="copy-status"></p>
      <p class="small">If they cry, or go quiet, or say you always do this — that is Hear, arriving. Do not fill it. If you are afraid of them, do not use this script. <a href="#safety">Leave the phrasing.</a></p>
    </article>
  `, route, "Say it")
}

function viewFar(route) {
  const a = state.alloc
  const wells = [
    ["near", "Near", "People you can touch. Presence, care, showing up. Real good. Usually small in scale. Do not empty this.", a.near, Math.round(a.near * 8), ""],
    ["story", "The story", "A cause that found you with a photograph. Sometimes wonderful. Often unmeasured. Drawn dashed, because the reach is a guess.", a.story, Math.round(a.story * 8), "dashed"],
    ["measured", "Measured", "Common, deadly, preventable: malaria, missing vaccines, extreme poverty, lead in children’s blood. Drawn long on purpose.", a.measured, Math.min(100, Math.round(a.measured * 8 * 5)), "far"]
  ]
  const wellHtml = wells.map(([id, name, copy, n, w, cls]) => `
    <div class="well">
      <h3>${name}</h3>
      <p class="small">${copy}</p>
      <div class="bar ${cls}" aria-hidden="true"><i style="width:${w}%"></i></div>
      <div class="stepper">
        <button type="button" data-act="alloc" data-well="${id}" data-dir="-1" aria-label="Less ${name}">−</button>
        <strong>${n}</strong>
        <button type="button" data-act="alloc" data-well="${id}" data-dir="1" aria-label="More ${name}">+</button>
      </div>
    </div>`).join("")
  const orgs = ORGS.map((o) => `<li><strong>${esc(o.name)}.</strong> ${esc(o.what)}</li>`).join("")
  const weeks = [
    ["blood", "Find out whether I can give blood, and book it if I can."],
    ["money", "When I next have a connection, look up one measured group and set an amount I will not miss."],
    ["skill", "Teach Steady, Fact, Own, Hear, One to one person who will use it."],
    ["sick", "Stay home the next time I am infectious, even if it is inconvenient."],
    ["across", "Have one conversation with someone I think is wrong, using Hear — not to convert them."]
  ]
  const checks = weeks.map(([id, label]) => `
    <label class="check"><input type="checkbox" data-week="${id}" ${state.week[id] ? "checked" : ""}><span>${label}</span></label>`).join("")
  shell(`
    <article class="page-intro">
      <p class="kicker">Far · what you can spare</p>
      <h1>The other half of the same impulse.</h1>
      <p class="lede">The person in front of you is not a distraction from the world. The world is not a distraction from them. People forget one or the other and call it virtue.</p>
    </article>
    <section class="wells" aria-label="Where a spare unit goes">${wellHtml}</section>
    <p id="alloc-copy" class="lede"></p>
    <p class="small">Ten spare units — an hour, a gift, a monthly amount. The third bar is a picture, not a measurement: researchers who compare outcomes per dollar often find gaps wider than this drawing. Not holier. Larger.</p>
    <div class="split" style="margin-top:2rem">
      <section>
        <h2>Blood, if you can.</h2>
        <p>A donation is one of the few hours that becomes someone else’s continuation — in surgery, in childbirth, in cancer care. One donation is often separated so more than one person is helped. Eligibility is a medical question, not a moral one. If you are deferred, you are deferred. Encouraging someone ineligible to try anyway protects no one.</p>
        <h2>Money you will not miss.</h2>
        <label class="field">
          <span class="lbl">A monthly amount <em>Any currency. The number is for you, not for a leaderboard.</em></span>
          <input id="monthly" type="number" min="0" step="1" inputmode="numeric" placeholder="30" value="${esc(state.monthly)}">
        </label>
        <p id="monthly-copy"></p>
        <p>Some suffering is vast and oddly cheap to reduce. Groups that publish their numbers and invite scrutiny have tended to do far more per dollar than causes chosen for how the giver feels. Rankings move. The existence of a large gap does not.</p>
        <ul class="orgs">${orgs}</ul>
        <p class="small">Naming them is not a claim that they are perfect, or that they will lead next year’s list. It is a claim that “measured, transparent, aimed at severe suffering” is a better habit than “whoever found me with a photograph.” Local giving can still be solidarity, which is a real good. Do not confuse it with the most suffering reduced per dollar. If you can, do both.</p>
      </section>
      <section>
        <h2>This week, one kept promise.</h2>
        <p class="small">Five intentions are a mood. One kept promise changes a week. Mark what you will actually do.</p>
        ${checks}
        <p id="week-copy"></p>
        <h2>Also far, and free.</h2>
        <p>Stay home when you are infectious. Sign an organ-donor registry if your country has one, and tell your family what you chose. Keep your own vaccines current. Use the near-skill on one person you think is wrong about the world — not to win, to keep them human in your mouth. Societies come apart when that stops.</p>
        <p><a class="btn" href="#card">Carry the card</a></p>
      </section>
    </div>
  `, route, "Far")
}

function viewCard(route) {
  shell(`
    <article class="card" id="card">
      ${stitch()}
      <p class="kicker">Sixty seconds · carry this</p>
      <h1>Mend</h1>
      <p class="mnemonic">Steady <i>·</i> Fact <i>·</i> Own <i>·</i> Hear <i>·</i> One</p>
      <section>
        <h2>Here</h2>
        <p>Two inhales, the second one short. One long exhale. Three times. Name the state. Wait for warmer hands before you send anything.</p>
      </section>
      <section>
        <h2>Near</h2>
        <p>Fact a camera would agree with. Your part, without “but,” “if,” or “I’m the worst.” Their account, all the way through. One next behavior. Permission for them to need nothing tonight.</p>
        <p>If they have less power: they are allowed to be upset with you, and they are safe.</p>
      </section>
      <section>
        <h2>If they might die</h2>
        <p>Ask plainly. Stay. Call for more help than you. Do not swear secrecy. Local emergency number, or 988 in the US and Canada, 116 123 in the UK and Ireland, 13 11 14 in Australia.</p>
      </section>
      <section>
        <h2>Far</h2>
        <p>Blood, if you are eligible. Money you will not miss, toward what is common, deadly, and measured. The skill, given to one other person.</p>
      </section>
      <section>
        <h2>Not this</h2>
        <p>but · sorry you feel · sorry if · you always · at least · just a joke · are we okay?</p>
      </section>
      <section>
        <h2>Visible</h2>
        <p>The break may stay visible. That is how a mend is different from a denial.</p>
      </section>
    </article>
    <p class="actions no-print">
      <a class="btn" href="#words">Use it now</a>
      <a class="btn secondary" href="#moves">Learn the moves</a>
      <button type="button" class="btn secondary" data-act="print">Print the card</button>
    </p>
  `, route, "The card")
}

function numbersList(list) {
  return `<ul class="numbers">${list.map((n) => `
    <li><div><span class="where">${esc(n.where)}</span><span class="small">${esc(n.note)}</span></div><b>${esc(n.number)}</b></li>`).join("")}</ul>`
}

function viewCrisis(route) {
  const self = route.parts[1] === "me"
  shell(`
    <article class="page-intro">
      <p class="kicker">In danger · stay</p>
      <h1>${self ? "You only have to get through the next hour." : "Stay. Ask. Get more help than you."}</h1>
      <p class="lede">${self
        ? "You do not have to be sure you mean it. You do not have to have a better reason. If you are thinking about suicide, the next move is another person whose job this is — or emergency services, if the danger is close."
        : "If someone might be thinking about suicide, ordinary conversation is over. You do not have to be their only help. You do have to stay long enough to get more."}</p>
      <div class="row">
        <a class="btn ${self ? "" : "secondary"}" href="#crisis/me">I am not okay</a>
        <a class="btn ${self ? "secondary" : ""}" href="#crisis">Someone else</a>
      </div>
    </article>
    ${self ? `
      <ol class="steps">
        <li>If you have a plan and the means are nearby, this is an emergency. Contact local emergency services now. If you can, put distance between yourself and the means while you call — another room, another person, a place where people are.</li>
        <li>You can call even if the sentence is unfinished. The people who answer have heard unfinished sentences before. Say: “I am thinking about suicide. I need help with the next hour.”</li>
        <li>If a friend is safe and close, you may say: “I don’t need advice. I need you to stay while I call.” That is a complete request.</li>
        <li>After the acute hour: one person who knows about tomorrow morning, and a follow-up you do not have to invent alone.</li>
      </ol>` : `
      <ol class="steps">
        <li>Ask the plain question. “Are you thinking about killing yourself?” Asking does not put the idea in someone’s head. Hinting leaves them alone with it.</li>
        <li>If yes, stay. Do not leave them alone if the danger is near. You can be quiet. You do not have to be interesting.</li>
        <li>Ask if they have a plan, and if the means are nearby. You are not interviewing them. You are finding out whether tonight is dangerous.</li>
        <li>Help them reach a person whose job this is. “I will stay while we call.” If danger is immediate, use the local emergency number.</li>
        <li>Do not promise secrecy about suicide. You can promise respect. You cannot promise silence if they might die. If they are a child, tell another responsible adult the same day. Do not carry it alone.</li>
        <li>After the acute hour: food, a person for tomorrow morning, a follow-up you actually do.</li>
      </ol>
      <h2>What not to say</h2>
      <ul class="dont-list">
        <li>“You have so much to live for.” It argues with their pain.</li>
        <li>“That’s selfish.” It teaches them to edit the truth.</li>
        <li>“I know exactly how you feel,” followed by your story. Your story can wait.</li>
        <li>“Promise me you won’t,” as a substitute for help.</li>
      </ul>`}
    <h2>Numbers</h2>
    <p class="small">Lines change. If one fails, use your local emergency number. Elsewhere, the International Association for Suicide Prevention keeps a directory: www.iasp.info/suicidalthoughts</p>
    ${numbersList(CRISIS_LINES)}
    <p class="small">This page is not itself a crisis service. If you are helping and you are out of your depth, that is the moment to call, not the moment to be braver alone.</p>
  `, route, "In danger")
}

function viewSafety(route) {
  shell(`
    <article class="page-intro">
      <p class="kicker">Near · when repair is the wrong tool</p>
      <h1>If you are afraid, do not polish the apology.</h1>
      <p class="lede">A repair script is for a relationship where the truth is survivable. If honesty is punished — if they hurt you and then demand a cleaner sorry — the next skill is not phrasing. It is an outside person, and a way to get safe.</p>
    </article>
    <ol class="steps">
      <li>If you are in danger now, contact local emergency services. If it is not safe to speak freely, you can try again from a neighbor, a shop, a workplace, a school. You do not owe the person in the room an explanation of the call.</li>
      <li>You do not owe them a better version of “I’m sorry.” Pressure to apologize, especially after they hurt you, is part of the harm.</li>
      <li>This page saves nothing you type. A browser history, a shared account, or a preview on a lock screen still might. If that is a risk, use a device they cannot open, or a phone call.</li>
      <li>You do not have to have an exit planned before you call a hotline. Planning is what the call is for. A friend who is safe is enough for the next hour. You do not have to narrate everything to deserve company.</li>
    </ol>
    <h2>Hotlines</h2>
    <p class="small">If a number fails, local emergency services can still reach you. In many places, 211 connects to local shelter resources.</p>
    ${numbersList(SAFETY_LINES)}
    <p class="actions"><a class="btn" href="#crisis">If there is also a risk of suicide</a> <a class="btn secondary" href="#home">Back</a></p>
  `, route, "Safety")
}

function viewMissing(route) {
  shell(`
    <article class="page-intro">
      <p class="kicker">Mend</p>
      <h1>That page isn’t here.</h1>
      <p class="lede">The practice is. Five moves, three distances, and a way to ask for help if someone might die.</p>
      <p class="actions"><a class="btn" href="#home">Begin</a> <a class="btn secondary" href="#card">The card</a></p>
    </article>
  `, route, "Not found")
}

function updateLetter() {
  const el = document.getElementById("letter-body")
  if (!el || parse().name === "speak") return
  const parts = composeParts(state.draft, state.lessPower)
  el.replaceChildren()
  if (parts.empty) {
    const p = document.createElement("p")
    p.className = "muted"
    p.textContent = "Write on the left. A speakable repair will gather here — fact, your part, their account, one request."
    el.appendChild(p)
  } else {
    for (const para of parts.paragraphs) {
      const p = document.createElement("p")
      p.textContent = para
      el.appendChild(p)
    }
  }
  const time = document.getElementById("say-time")
  if (time) {
    time.textContent = parts.empty ? "" : `About ${parts.seconds} seconds, said slowly.${parts.seconds > 50 ? " If it is over a minute, you are explaining. Cut." : ""}`
  }
}

function updateFlags() {
  for (const key of ["fact", "own", "hear", "one"]) {
    const slot = document.querySelector(`[data-flag-for="${key}"]`)
    if (!slot) continue
    slot.replaceChildren()
    for (const f of flagsFor(state.draft[key] || "")) {
      const p = document.createElement("p")
      p.className = "flagnote"
      p.textContent = f.text
      slot.appendChild(p)
    }
  }
}

function updatePaste() {
  const slot = document.getElementById("paste-notes")
  if (!slot) return
  const { found, goods, words } = analyze(state.paste)
  slot.replaceChildren()
  if (!state.paste.trim()) {
    const p = document.createElement("p")
    p.className = "small"
    p.textContent = "The notes appear as you paste or type."
    slot.appendChild(p)
    return
  }
  const meta = document.createElement("p")
  meta.className = "small"
  meta.textContent = `${words} words.`
  slot.appendChild(meta)
  if (!found.length && !goods.length) {
    const p = document.createElement("p")
    p.textContent = "Too short to judge. A repair usually needs a fact and a part that was yours."
    slot.appendChild(p)
  }
  const ul = document.createElement("ul")
  ul.className = "note-list"
  for (const f of found) {
    const li = document.createElement("li")
    li.innerHTML = `<strong>${esc(f.match)}</strong> — ${esc(f.text)}`
    ul.appendChild(li)
  }
  for (const g of goods) {
    const li = document.createElement("li")
    li.className = "good"
    li.textContent = g
    ul.appendChild(li)
  }
  slot.appendChild(ul)
}

function allocComment() {
  const { near, story, measured } = state.alloc
  if (near === 0) return "You emptied the people you can touch. Give something back. A life that only loves humanity in the abstract will fail the first real test, and then stop giving at all."
  if (measured === 0) return "Nothing in the third column. That is allowed. It is also how preventable deaths stay unfunded while moving stories are fully subscribed."
  if (measured >= 3 && near >= 2) return "This is a shape a life can keep. Near enough to stay human. Far enough to matter past the people who know your name."
  if (story > near + measured) return "Most of the spare is following a feeling. Feelings are information. They are not a compass for where a dollar prevents the most harm."
  return "Move what you will not miss. Leave what your actual relationships need. The drawing gets less lopsided before the world does."
}

function monthlyComment() {
  const n = Number(state.monthly)
  if (!state.monthly || Number.isNaN(n) || n <= 0) {
    return "Put in an amount you would not miss. Even a small one, kept, matters more than a heroic one you abandon."
  }
  const year = Math.round(n * 12)
  return `About ${year.toLocaleString()} a year, in whatever currency you meant. You will not feel heroic. Pooled with other unromantic choices, this is how nets, vaccines, cash, and lead removal actually get paid for. The point is not to be moved. The point is to be consistent.`
}

function weekComment() {
  const labels = {
    blood: "book a blood donation if you are eligible",
    money: "set one measured gift you will not miss",
    skill: "teach the five moves to one person",
    sick: "stay home the next time you are infectious",
    across: "have one hard conversation using Hear"
  }
  const marked = Object.entries(state.week).filter(([, v]) => v).map(([k]) => labels[k])
  if (!marked.length) return "Nothing marked. That is an honest start. Mark one, if one is all you will do."
  if (marked.length === 1) return `One: ${marked[0]}. A kept promise. That is the week.`
  return `You marked ${marked.length}. If you keep all of them, good. If you keep one, let it be the one you are most likely to skip: ${marked[0]}.`
}

function updateFarCopy() {
  const a = document.getElementById("alloc-copy")
  const m = document.getElementById("monthly-copy")
  const w = document.getElementById("week-copy")
  if (a) a.textContent = allocComment()
  if (m) m.textContent = monthlyComment()
  if (w) w.textContent = weekComment()
}

function threadPath(slack) {
  const y = 26 + slack * 48
  return `M16 26 Q260 ${y.toFixed(1)} 504 26`
}

function setThread(slack) {
  const path = document.getElementById("thread-path")
  if (path) path.setAttribute("d", threadPath(slack))
}

function stopBreath() {
  cancelAnimationFrame(breathRAF)
  clearTimeout(breathTimer)
  state.breath.running = false
}

function startBreath() {
  if (parse().name !== "here") return
  stopBreath()
  state.breath.running = true
  state.breath.cycle = 0
  state.breath.phase = 0
  if (state.sound) ensureAudio()
  runPhase()
}

function runPhase() {
  if (!state.breath.running) return
  const phase = PHASES[state.breath.phase]
  const name = document.querySelector("[data-phase-name]")
  const detail = document.querySelector("[data-phase-detail]")
  if (name) name.textContent = phase.name
  if (detail) detail.textContent = phase.detail
  paintDots()
  if (state.sound) playPhase(phase)
  const start = performance.now()
  const tick = (now) => {
    if (!state.breath.running) return
    const t = Math.min(1, (now - start) / phase.dur)
    const slack = phase.from + (phase.to - phase.from) * ease(t)
    setThread(slack)
    if (t < 1) breathRAF = requestAnimationFrame(tick)
    else breathTimer = setTimeout(advancePhase, 280)
  }
  breathRAF = requestAnimationFrame(tick)
}

function ease(t) {
  return t * t * (3 - 2 * t)
}

function advancePhase() {
  if (!state.breath.running) return
  state.breath.phase += 1
  if (state.breath.phase >= PHASES.length) {
    state.breath.phase = 0
    state.breath.cycle += 1
    state.breath.manual = Math.max(state.breath.manual, state.breath.cycle)
    if (state.breath.cycle >= 3) {
      finishBreath()
      return
    }
  }
  runPhase()
}

function finishBreath() {
  state.breath.running = false
  state.breath.manual = 3
  const name = document.querySelector("[data-phase-name]")
  const detail = document.querySelector("[data-phase-detail]")
  const feeling = FEELINGS[state.feeling]
  if (name) name.textContent = "Enough for now."
  if (detail && feeling) detail.textContent = feeling.after
  setThread(0.55)
  paintDots()
  const status = document.getElementById("breath-status")
  if (status) status.textContent = "Three is enough. If you are still flooded, do three more before you type anything you cannot unsend."
}

function paintDots() {
  const dots = document.querySelectorAll(".dots i")
  const n = Math.max(state.breath.manual, state.breath.cycle)
  dots.forEach((dot, i) => dot.classList.toggle("on", i < n))
}

function ensureAudio() {
  const AC = window.AudioContext || window.webkitAudioContext
  if (!AC) return null
  if (!audioCtx) audioCtx = new AC()
  if (audioCtx.state === "suspended") audioCtx.resume()
  return audioCtx
}

function playPhase(phase) {
  const ctx = ensureAudio()
  if (!ctx) return
  const o = ctx.createOscillator()
  const g = ctx.createGain()
  o.type = "sine"
  const up = phase.name !== "Let it go"
  o.frequency.setValueAtTime(up ? 196 : 330, ctx.currentTime)
  o.frequency.linearRampToValueAtTime(up ? 330 : 146, ctx.currentTime + phase.dur / 1000)
  g.gain.setValueAtTime(0.0001, ctx.currentTime)
  g.gain.exponentialRampToValueAtTime(0.03, ctx.currentTime + 0.08)
  g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + phase.dur / 1000)
  o.connect(g)
  g.connect(ctx.destination)
  o.start()
  o.stop(ctx.currentTime + phase.dur / 1000 + 0.05)
}

function scriptText() {
  const parts = composeParts(state.draft, state.lessPower)
  if (parts.empty) return "I want to repair something. I will be specific. I will listen before I explain."
  return parts.text
}

async function copyScript() {
  const text = scriptText()
  const status = document.getElementById("copy-status")
  let ok = false
  try {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(text)
      ok = true
    }
  } catch {
    ok = false
  }
  if (!ok) {
    const body = document.getElementById("letter-body")
    if (body) {
      const range = document.createRange()
      range.selectNodeContents(body)
      const sel = getSelection()
      sel.removeAllRanges()
      sel.addRange(range)
    }
  }
  if (status) {
    status.textContent = ok
      ? "Copied. It is still yours to say — or not to send."
      : "Clipboard is blocked here. The words are selected, if the page allows it. Otherwise, just read them."
  }
}

function onClick(e) {
  const el = e.target.closest("[data-act]")
  if (!el) return
  const act = el.dataset.act
  if (act === "banned") {
    state.banned = el.dataset.id
    const why = BANNED.find((b) => b.id === state.banned)
    const panel = document.getElementById("why-panel")
    if (panel && why) panel.textContent = why.why
    document.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", c.dataset.id === state.banned ? "true" : "false"))
    return
  }
  if (act === "breath-start") {
    startBreath()
    return
  }
  if (act === "breath-manual") {
    if (state.breath.manual >= 3) state.breath.manual = 0
    state.breath.manual += 1
    paintDots()
    if (state.breath.manual >= 3) finishBreath()
    else {
      const name = document.querySelector("[data-phase-name]")
      if (name) name.textContent = `${state.breath.manual} of 3.`
    }
    return
  }
  if (act === "sound") {
    state.sound = !state.sound
    el.setAttribute("aria-pressed", state.sound ? "true" : "false")
    el.textContent = state.sound ? "Sound on" : "Sound off"
    if (state.sound) ensureAudio()
    return
  }
  if (act === "drill") {
    state.drillChoice = Number(el.dataset.i)
    render("stay")
    document.getElementById("consequence")?.scrollIntoView({ block: "nearest", behavior: reduce ? "auto" : "smooth" })
    return
  }
  if (act === "drill-another") {
    state.drillOffset += 1
    state.drillChoice = null
    render("stay")
    return
  }
  if (act === "practice-start") {
    state.practice.started = true
    render("route")
    return
  }
  if (act === "practice-reset") {
    state.practice = { id: state.practice.id, beat: 0, choice: null, picks: [], started: true }
    render("route")
    return
  }
  if (act === "choose-line") {
    state.practice.choice = Number(el.dataset.i)
    render("choice")
    return
  }
  if (act === "retry") {
    state.practice.choice = null
    render("stay")
    return
  }
  if (act === "next-beat") {
    const scene = SCENES[state.practice.id]
    const beat = scene.beats[state.practice.beat]
    const opt = beat.options[state.practice.choice]
    if (opt) state.practice.picks.push(opt.kind)
    state.practice.choice = null
    state.practice.beat += 1
    render("route")
    return
  }
  if (act === "alloc") {
    const well = el.dataset.well
    const dir = Number(el.dataset.dir)
    const keys = ["near", "story", "measured"]
    if (dir > 0) {
      const other = keys.filter((k) => k !== well && state.alloc[k] > 0).sort((a, b) => state.alloc[b] - state.alloc[a])[0]
      if (!other) return
      state.alloc[other] -= 1
      state.alloc[well] += 1
    } else if (state.alloc[well] > 0) {
      const other = keys.filter((k) => k !== well)[0]
      state.alloc[well] -= 1
      state.alloc[other] += 1
    }
    render("stay")
    return
  }
  if (act === "copy") {
    copyScript()
    return
  }
  if (act === "print") {
    window.print()
  }
}

function onInput(e) {
  const t = e.target
  if (t.dataset.field) {
    state.draft[t.dataset.field] = t.value
    updateLetter()
    updateFlags()
  }
  if (t.id === "paste") {
    state.paste = t.value
    updatePaste()
  }
  if (t.id === "monthly") {
    state.monthly = t.value
    const m = document.getElementById("monthly-copy")
    if (m) m.textContent = monthlyComment()
  }
  if (t.dataset.week) {
    state.week[t.dataset.week] = t.checked
    const w = document.getElementById("week-copy")
    if (w) w.textContent = weekComment()
  }
}

function onChange(e) {
  if (e.target.dataset.act === "power") {
    state.lessPower = e.target.checked
    updateLetter()
  }
}

function onKey(e) {
  if (e.metaKey || e.ctrlKey || e.altKey) return
  if (e.target.matches("textarea, input")) return
  if (e.key === "1" || e.key === "2" || e.key === "3") {
    const btn = document.querySelector(`[data-act="choose-line"][data-i="${Number(e.key) - 1}"], [data-act="drill"][data-i="${Number(e.key) - 1}"]`)
    if (btn && !btn.disabled) btn.click()
  }
}

function init() {
  if (!location.hash) history.replaceState(null, "", "#home")
  window.addEventListener("hashchange", () => render("route"))
  document.body.addEventListener("click", onClick)
  document.body.addEventListener("input", onInput)
  document.body.addEventListener("change", onChange)
  document.body.addEventListener("keydown", onKey)
  render("route")
}

init()
