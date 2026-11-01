// 8 Billion Neighbors — all state is in-memory only. Nothing is stored or sent anywhere.

const $ = (s, el = document) => el.querySelector(s);
const $$ = (s, el = document) => [...el.querySelectorAll(s)];
const rand = (arr) => arr[Math.floor(Math.random() * arr.length)];
const fmt = (n) => new Intl.NumberFormat("en", { notation: "compact", maximumFractionDigits: 1 }).format(n);
let selWord = "Kindness";

/* ---------- journey progress ---------- */
const milestones = new Set();
function markJourney(key) {
  if (milestones.has(key)) return;
  milestones.add(key);
  const lights = $$("#journeyLights i");
  lights.forEach((l, i) => l.classList.toggle("on", i < milestones.size));
  $("#journeyCount").textContent = `${Math.min(milestones.size, 5)} / 5`;
  if (milestones.size === 5) toast("Journey complete — village, neighbor, ground, breath, action. Now go be someone's good day. 🌍");
}
let toastTimer;
function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.remove("hidden");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => t.classList.add("hidden"), 4200);
}

/* ---------- hero globe (canvas dot sphere) ---------- */
(() => {
  const cv = $("#globe"), ctx = cv.getContext("2d");
  let W, H, mx = 0, my = 0, t = 0;
  const N = 950, pts = [];
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), th = i * 2.399963;
    pts.push({ x: Math.cos(th) * r, y, z: Math.sin(th) * r, c: ["#ffb627", "#ff5c39", "#0e7c6b", "#182233"][i % 17 === 0 ? 1 : i % 23 === 0 ? 2 : i % 5 === 0 ? 3 : 0] });
  }
  function size() { const s = cv.getBoundingClientRect(); const d = Math.min(devicePixelRatio || 1, 2); W = s.width; H = s.height; cv.width = W * d; cv.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0); }
  size(); addEventListener("resize", size);
  addEventListener("pointermove", (e) => { mx = (e.clientX / innerWidth - .5); my = (e.clientY / innerHeight - .5); });
  (function draw() {
    t += 0.0022;
    ctx.clearRect(0, 0, W, H);
    const R = Math.min(W, H) * 0.42, cx = W / 2, cy = H / 2;
    const rotY = t + mx * 1.4, rotX = my * 0.7;
    for (const p of pts) {
      let { x, y, z } = p;
      let x1 = x * Math.cos(rotY) - z * Math.sin(rotY), z1 = x * Math.sin(rotY) + z * Math.cos(rotY);
      let y1 = y * Math.cos(rotX) - z1 * Math.sin(rotX), z2 = y * Math.sin(rotX) + z1 * Math.cos(rotX);
      const a = 0.18 + 0.82 * Math.max(0, (z2 + 1) / 2);
      ctx.globalAlpha = a; ctx.fillStyle = p.c;
      ctx.beginPath(); ctx.arc(cx + x1 * R, cy + y1 * R, 1.4 + a * 2.1, 0, 7); ctx.fill();
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  })();
})();

/* hero rotating "right now" line */
const nowLines = [
  "A nurse in Nairobi is starting a night shift.",
  "A grandfather in Oaxaca is teaching a card trick.",
  "A teenager in Dhaka is revising for an exam she intends to ace.",
  "A baker in Beirut pulled the first bread from the oven an hour ago.",
  "A bus driver in Warsaw is humming along to the radio.",
  "A new parent in Toronto is asleep standing up, almost.",
  "A fisherman in Kerala is reading the sky like a newspaper.",
  "A grandmother in Hanoi saved you the good seat. She doesn't know it yet.",
];
let nowI = 0;
setInterval(() => { nowI = (nowI + 1) % nowLines.length; const el = $("#nowText"); if (el) el.textContent = nowLines[nowI]; }, 4200);

/* ---------- 01 village of 100 ---------- */
const FACTS = [
  { label: "💧 Clean water", n: 74, color: "teal", on: "has safely managed drinking water", off: "doesn’t yet", text: "74 of our 100 neighbors can turn a tap and trust what comes out.", hope: "The hopeful part: in 2000 it was 61. Pipes, wells and boring infrastructure quietly saved millions of childhoods.", src: "Rounded estimate · WHO/UNICEF Joint Monitoring Programme" },
  { label: "💡 Electricity", n: 91, color: "", on: "has electricity at home", off: "doesn’t yet", text: "91 of 100 can light a room, charge a phone and keep food cold.", hope: "The hopeful part: a billion people gained power in a single generation — solar is now reaching the last villages first.", src: "Rounded estimate · World Bank / IEA access-to-electricity data" },
  { label: "🌐 Internet", n: 68, color: "coral", on: "uses the internet", off: "isn’t online yet", text: "68 of 100 are online — including, probably, several people who will see a photo of your lunch.", hope: "The hopeful part: connection means a farmer can check prices, a student can find a library, a diaspora can call home for free.", src: "Rounded estimate · International Telecommunication Union" },
  { label: "📚 Can read", n: 87, color: "teal", on: "can read and write", off: "can’t yet", text: "87 of 100 adults can read these words — or their own language’s version of them.", hope: "The hopeful part: in 1970 it was barely 60. Among young people today it’s over 92. The readers are winning.", src: "Rounded estimate · UNESCO literacy data" },
  { label: "💉 Vaccinated", n: 84, color: "", on: "of infants get basic vaccines", off: "miss out", text: "About 84 of every 100 babies get the basic vaccines that turned deadly childhood diseases into rare ones.", hope: "The hopeful part: smallpox killed hundreds of millions and now exists only in labs. This is what ‘we did it together’ looks like.", src: "Rounded estimate · WHO/UNICEF immunisation coverage" },
];
const grid = $("#peopleGrid");
for (let i = 0; i < 100; i++) { const d = document.createElement("div"); d.className = "person"; grid.appendChild(d); }
const factTabs = $("#factTabs");
FACTS.forEach((f, i) => {
  const b = document.createElement("button");
  b.className = "chip" + (i === 0 ? " active" : ""); b.textContent = f.label; b.setAttribute("role", "tab");
  b.onclick = () => selectFact(i);
  factTabs.appendChild(b);
});
function selectFact(i) {
  const f = FACTS[i];
  $$(".chip", factTabs).forEach((c, j) => c.classList.toggle("active", j === i));
  $$(".person", grid).forEach((p, j) => {
    p.className = "person" + (j < f.n ? ` on ${f.color}` : "");
    if (j < f.n) setTimeout(() => { p.classList.add("pop"); setTimeout(() => p.classList.remove("pop"), 220); }, j * 6);
  });
  $("#factNumber").textContent = f.n;
  $("#factText").textContent = f.text;
  $("#factHope").textContent = f.hope;
  $("#factSource").textContent = f.src;
  $("#legendOn").textContent = f.on; $("#legendOff").textContent = f.off;
}
selectFact(0);
$("#villageDone").onclick = (e) => { markJourney("village"); e.target.textContent = "Village seen ✓ — 100 neighbors, not 8 billion strangers"; toast("01 ✓ The village: most of humanity has light, water, words and signal. The rest is our shared to-do list."); };

/* ---------- 02 another life ---------- */
const LIVES = [
  { name: "Amara, 34", meta: "Nurse · Kisumu, Kenya", morning: "Tea, matatu ride, ward rounds by 7.", work: "Delivers babies and very firm advice.", joy: "Her daughter’s laugh when the power blinks back on.", worry: "School fees next term — nearly there.", offer: "Mandazis, still warm.", shared: ["has laughed at a joke that doesn’t translate", "is saving for something that matters", "knows one person’s phone number by heart"] },
  { name: "Tomasz, 61", meta: "Bus driver · Gdańsk, Poland", morning: "Black coffee, route 6, same wave to the florist.", work: "Knows every pothole and most passengers’ stops by heart.", joy: "Sunday pierogi production line with his grandkids.", worry: "His knees. And whether the grandkids call enough. (They do.)", offer: "The good seat by the window, pretends he didn’t.", shared: ["has a route through life worn smooth by repetition", "worries about people who worry about him", "keeps snacks for other people, just in case"] },
  { name: "Priya, 19", meta: "Engineering student · Patna, India", morning: "5 a.m. revision while the house is quiet.", work: "First in her family at university. Carries that carefully.", joy: "Solving the problem nobody else in the tutorial could.", worry: "The exam in June. She’s ready. Mostly. She’s ready.", offer: "Notes — colour-coded, legendary, freely shared.", shared: ["has been underestimated and kept receipts", "studies a future into existence", "has a family group chat on mute and checks it constantly"] },
  { name: "Diego, 42", meta: "Carpenter · Oaxaca, Mexico", morning: "Market coffee, measures yesterday’s mistakes honestly.", work: "Turns fallen cedar into tables that outlive him.", joy: "His son sanding a board straight for the first time.", worry: "Timber prices. Rain on unfinished work.", offer: "A stool. Sit. Nobody talks business sitting down hungry.", shared: ["makes something with their hands that will outlast a mood", "was taught by someone patient", "measures twice — in work, and tries to in words"] },
  { name: "Fatima, 28", meta: "Teacher · Amman, Jordan", morning: "Packs 31 lunches’ worth of patience.", work: "Teaches maths to girls who teach her slang back.", joy: "The quiet kid who finally puts a hand up.", worry: "Whether her best student’s family can keep her in school.", offer: "Mint tea and the correct answer, gently.", shared: ["remembers a teacher who changed the temperature of a room", "does emotional labour nobody logs", "believes in someone who doesn’t yet"] },
  { name: "Kenji, 77", meta: "Retired stationmaster · rural Honshu, Japan", morning: "Radio exercises in the garden, tomatoes inspected.", work: "Now tends a community garden with strong opinions about daikon.", joy: "The 7:12 train — still waves. The driver still waves back.", worry: "The village getting quieter each spring.", offer: "Tomatoes. Too many tomatoes. Take tomatoes.", shared: ["has outlived a version of the world", "keeps a ritual that keeps him", "gives away more than he keeps"] },
  { name: "Sofia, 15", meta: "Student & goalkeeper · Recife, Brazil", morning: "Training before school if the pitch isn’t flooded.", work: "Homework, footwork, and a highlight reel in her head.", joy: "Saving a penalty from the striker everyone fears.", worry: "Balancing trials with grades. Coach says both. She says both.", offer: "Last slice energy — she’ll fight you for it, then split it.", shared: ["has replayed a triumph in their head this week", "is braver at one specific thing than people know", "runs on encouragement more than they admit"] },
  { name: "Lars, 49", meta: "Ferry mechanic · Bergen, Norway", morning: "Checks the fjord weather like it owes him money.", work: "Keeps the boat that keeps three villages connected.", joy: "Engine turning over first try on a February morning.", worry: "His daughter leaving for university in August.", offer: "Coffee strong enough to count as a tool.", shared: ["fixes things other people just replace", "is proud and pretends not to be", "measures love partly in showing up on time"] },
  { name: "Mei, 26", meta: "Night-market vendor · Taipei, Taiwan", morning: "Sleeps in. Her morning is your lunch hour.", work: "Sells scallion pancakes with a queue that reviews itself.", joy: "Regulars bringing their parents. That’s the real five stars.", worry: "Rent, and a landlord who knows the queue exists.", offer: "An extra pancake ‘that came out wrong’. It did not.", shared: ["feeds people for a living or for love — same motion", "has a regular they’d miss", "works when the rest of the world is winding down"] },
  { name: "Samuel, 37", meta: "Pastor & taxi driver · Kampala, Uganda", morning: "Two jobs, one alarm clock, zero snoozing.", work: "Preaches Sundays, drives weeknights, counsels in traffic.", joy: "Choir rehearsal when the harmony lands.", worry: "Fuel prices and everybody’s everything — he hears it all.", offer: "A prayer, a shortcut, or silence — he’ll match your need.", shared: ["carries other people’s news carefully", "works more than one job, counting the invisible ones", "knows listening is a form of labour and love"] },
];
let lifeIdx = [], lifePos = 0, livesVisited = 0;
function nextLife() {
  if (lifePos >= lifeIdx.length) { lifeIdx = LIVES.map((_, i) => i).sort(() => Math.random() - .5); lifePos = 0; }
  const L = LIVES[lifeIdx[lifePos++]];
  livesVisited++;
  const card = $("#lifeCard");
  card.classList.remove("shake"); void card.offsetWidth; card.classList.add("shake");
  $("#lifeAvatar").textContent = L.name[0];
  $("#lifeAvatar").style.background = rand(["#0e7c6b", "#ff5c39", "#6c5ce7", "#ffb627", "#182233"]);
  $("#lifeName").textContent = L.name;
  $("#lifeMeta").textContent = L.meta;
  $("#lifeMorning").textContent = L.morning;
  $("#lifeWork").textContent = L.work;
  $("#lifeJoy").textContent = L.joy;
  $("#lifeWorry").textContent = L.worry;
  $("#lifeOffer").textContent = L.offer;
  $("#sharedList").innerHTML = L.shared.map(s => `<li>${s}</li>`).join("");
  $("#sharedBox").classList.add("hidden");
  $("#shareBtn").classList.remove("hidden");
  $("#lifeCount").textContent = livesVisited;
  const pct = Math.min(96, 6 + livesVisited * 18);
  $("#empathyBar").style.width = pct + "%";
  $("#empathyLabel").textContent = livesVisited >= 4 ? "right next door" : livesVisited >= 2 ? "getting closer" : livesVisited >= 1 ? "a short walk away" : "very far away";
  if (livesVisited === 1) toast("Notice: their worries have the same shape as yours. Different weather, same sky.");
  updatePlan();
}
$("#lifeBtn").onclick = nextLife;
$("#shareBtn").onclick = () => { $("#sharedBox").classList.remove("hidden"); $("#shareBtn").classList.add("hidden"); markJourney("life"); };

/* ---------- 03 common ground quiz ---------- */
const QUIZ = [
  { s: "“Every child deserves clean water, enough food and a safe way to learn.”", a: 94, note: "Nearly everyone, in nearly every country surveyed. Child wellbeing is humanity’s least controversial opinion." },
  { s: "“No one who works hard should be unable to feed their family.”", a: 91, note: "Across rich and poor countries alike, fairness at work polls like gravity: assumed, universal, only argued about at the edges." },
  { s: "“Leaders should be honest, even when the truth is uncomfortable.”", a: 89, note: "We argue fiercely about who is honest. Almost none of us argue that honesty doesn’t matter." },
  { s: "“I want my neighborhood to be safe, clean and friendly to grow old in.”", a: 93, note: "The politics of place turns out to be mostly this: safety, dignity, and somewhere decent to sit in the sun at 80." },
];
let qi = 0, quizRevealed = [], quizLocked = false;
function loadQuiz() {
  quizLocked = false;
  $("#quizStep").textContent = `QUESTION ${qi + 1} OF ${QUIZ.length}`;
  $("#quizStatement").textContent = QUIZ[qi].s;
  $("#quizSlider").value = 50; $("#quizGuess").textContent = "50%";
  $("#quizReveal").classList.add("hidden");
  $("#quizCheck").classList.remove("hidden"); $("#quizNext").classList.add("hidden");
}
$("#quizSlider").addEventListener("input", (e) => $("#quizGuess").textContent = e.target.value + "%");
$("#quizCheck").onclick = () => {
  if (quizLocked) return; quizLocked = true;
  const guess = +$("#quizSlider").value, q = QUIZ[qi];
  quizRevealed.push(q.a);
  $("#quizReveal").classList.remove("hidden");
  requestAnimationFrame(() => { $("#barYou").style.width = guess + "%"; $("#barReal").style.width = q.a + "%"; });
  $("#barYouVal").textContent = guess + "%"; $("#barRealVal").textContent = q.a + "%";
  const diff = guess - q.a;
  $("#quizNote").textContent = (diff < -12 ? "You underestimated your neighbors — most people do. That gap is where cynicism lives. " : diff > 8 ? "You’re more trusting than average — keep that, it’s load-bearing. " : "Close. You read humanity well. ") + q.note;
  $("#quizScore").textContent = `Common ground found: ${quizRevealed.length} of ${QUIZ.length}`;
  $("#agreeAvg").textContent = Math.round(quizRevealed.reduce((a, b) => a + b, 0) / quizRevealed.length) + "%";
  $("#quizCheck").classList.add("hidden");
  const next = $("#quizNext");
  next.classList.remove("hidden");
  next.textContent = qi === QUIZ.length - 1 ? "Finish — I found the ground ✓" : "Next hope →";
};
$("#quizNext").onclick = () => {
  if (qi === QUIZ.length - 1) { markJourney("ground"); toast("03 ✓ Common ground: we were never as divided as the loudest hour suggested."); $("#quizNext").textContent = "Done ✓ scroll on — breathe with us ↓"; return; }
  qi++; loadQuiz();
};
loadQuiz();

/* ---------- 04 breathe together ---------- */
let breathing = false, breathTimeouts = [], cycles = 0, worldBreaths = 0;
setInterval(() => { worldBreaths += 205_000_000; const el = $("#worldBreaths"); if (el) el.textContent = fmt(worldBreaths); }, 100);
function breathLoop() {
  if (!breathing) return;
  const ring = $("#breathRing"), word = $("#breathWord");
  word.textContent = "breathe in…"; ring.className = "breath-ring in";
  breathTimeouts.push(setTimeout(() => { if (!breathing) return; word.textContent = "hold, gently"; ring.className = "breath-ring in"; }, 4000));
  breathTimeouts.push(setTimeout(() => { if (!breathing) return; word.textContent = "and let it go"; ring.className = "breath-ring out"; }, 6000));
  breathTimeouts.push(setTimeout(() => {
    if (!breathing) return;
    cycles++; $("#cycleCount").textContent = cycles;
    if (cycles === 1) { markJourney("breathe"); toast("04 ✓ One breath, taken slowly, on purpose. That’s the whole technique — repeat as needed for being alive."); }
    breathLoop();
  }, 12000));
}
$("#breathBtn").onclick = (e) => {
  breathing = !breathing;
  breathTimeouts.forEach(clearTimeout); breathTimeouts = [];
  const ring = $("#breathRing");
  if (breathing) { e.target.textContent = "Rest here (stop)"; breathLoop(); }
  else { e.target.textContent = "Start breathing together"; ring.className = "breath-ring"; $("#breathWord").textContent = "ready?"; }
};

/* ---------- 05 kindness missions ---------- */
const WHERES = [["home", "🏠 At home"], ["work", "💼 Work / school"], ["out", "🚶 Out & about"], ["online", "📱 Online / phone"]];
const TIMES = [[2, "⚡ 2 minutes"], [10, "🌿 10 minutes"], [999, "☀️ Today"]];
const MISSIONS = [
  { w: "home", t: 2, title: "The specific thank-you", body: "Vague gratitude evaporates. Specific gratitude lands and stays for days.", steps: ["Pick one person under this roof (or one text away).", "Say or send: “Thank you for [specific thing] — it mattered because [reason].”", "Stop there. Don’t dilute it with a request."] },
  { w: "home", t: 2, title: "Leave a landmine of delight", body: "A note where they’ll find it later is a time-release act of kindness.", steps: ["Write 2 honest lines on any scrap: what you like about them.", "Hide it: lunchbox, mirror, book page 40, coat pocket.", "Say nothing. Let the future do the work."] },
  { w: "home", t: 10, title: "Take one invisible job off someone", body: "Every household runs on invisible labour. Do one piece without announcing it.", steps: ["Spot a job someone else usually silently does.", "Do it fully — bin out, form filled, thing fixed, surface cleared.", "If asked, say: “It was just there.” Because now it isn’t."] },
  { w: "home", t: 999, title: "Cook (or order) their favorite, on a Tuesday", body: "Celebration food on an ordinary day rewires what the day means.", steps: ["Choose their reliably-happy meal.", "Make or order it today — no occasion cited or needed.", "Eat together, phones in another room for the first ten minutes."] },
  { w: "work", t: 2, title: "Public credit, precisely aimed", body: "Praise in public, specifics in the sentence, their name spelled right.", steps: ["Think of one thing a colleague did that actually helped.", "Say it where others can hear, or write it in the shared channel.", "Include the detail only an eyewitness would know."] },
  { w: "work", t: 2, title: "The 2-minute unblock", body: "Somewhere near you, someone is stuck on something you could solve in minutes.", steps: ["Ask: “What’s one small thing in your way today?”", "If you can clear it in 2 minutes — the file, the intro, the answer — do it now.", "No follow-up favour owed. That’s the point."] },
  { w: "work", t: 10, title: "Write the recommendation nobody asked for", body: "Unsolicited, specific endorsement is career kindness with compound interest.", steps: ["Pick someone good who is overlooked or early-career.", "Write 5 specific lines where it counts: message, review, intro email.", "Send it today, while it’s warm."] },
  { w: "work", t: 999, title: "Mentor for exactly one coffee", body: "You know something a beginner would trade a week to learn. It costs you 30 minutes.", steps: ["Invite one junior person for coffee/tea — your treat.", "Ask what they’re stuck on before offering anything.", "Give one honest lesson and one encouraging truth."] },
  { w: "out", t: 2, title: "The genuine compliment, delivered", body: "You already notice nice things about strangers. Today, one of them gets to hear it.", steps: ["Notice something specific: the coat, the calm, the skill.", "Say: “Excuse me — [specific thing] is great.” Smile, keep walking.", "No lingering. A compliment with no hook is a gift with no string."] },
  { w: "out", t: 2, title: "Thank the invisible shift", body: "Cleaners, drivers, cashiers and guards hold the day together, mostly unthanked.", steps: ["Catch one person’s eye mid-task.", "Say: “Thanks for keeping this place running.” Mean the eye contact.", "Add their name if they wear one. Names multiply thanks."] },
  { w: "out", t: 10, title: "Leave the place better, visibly", body: "Ten minutes of unowned care quietly re-norms a whole space.", steps: ["Pick up the litter near the bench / beach / platform edge.", "Return the stray cart, chair, or gate to where it helps.", "Let yourself be seen, a little. Witnessed care is contagious care."] },
  { w: "out", t: 999, title: "Pay it backward & forward", body: "Cover a coffee behind you and tip like someone whose day was made easier — because it was, by someone.", steps: ["Pay for the next person’s coffee or fare, quietly.", "Tip one service worker noticeably more than habit today.", "Tell nobody except, now, this garden. It still happened."] },
  { w: "online", t: 2, title: "Send the ‘thinking of you’ with no occasion", body: "The message everyone treasures and nobody sends without a birthday prompt.", steps: ["Scroll contacts until a face makes you smile. Stop there.", "Send: “No reason — just thought of you and it improved my minute. Hope you’re well.”", "Don’t end with a question that creates homework."] },
  { w: "online", t: 2, title: "Be the first kind comment", body: "First comments set the weather of a thread. Set it fair.", steps: ["Find a small creator / new poster / brave question.", "Write one specific, encouraging, true comment.", "Leave before reading replies. You planted; don’t hover."] },
  { w: "online", t: 10, title: "The long-overdue appreciation post", body: "Publicly thank someone who shaped you — teacher, friend, stranger with a blog.", steps: ["Name them (or describe them) and the specific difference they made.", "Post it where they might actually see it; tag gently if welcome.", "Expect nothing back. Sometimes everything comes back."] },
  { w: "online", t: 999, title: "One-hour digital doorman", body: "Hold the door of the internet open: welcome newcomers like a host, not a guard.", steps: ["Spend spare minutes today answering one beginner question kindly.", "Upvote / share one good-faith post from outside your usual circle.", "Correct one error (yours counts double) without a victory lap."] },
];
let selWhere = "home", selTime = 2, currentMission = null, missionAccepted = false;
function chips(el, items, activeVal, cb) {
  el.innerHTML = "";
  items.forEach(([val, label]) => {
    const b = document.createElement("button");
    b.className = "chip" + (val === activeVal ? " active" : ""); b.textContent = label;
    b.onclick = () => cb(val);
    el.appendChild(b);
  });
}
function renderChips() {
  chips($("#whereChips"), WHERES, selWhere, (v) => { selWhere = v; renderChips(); newMission(); });
  chips($("#timeChips"), TIMES, selTime, (v) => { selTime = v; renderChips(); newMission(); });
}
let timerInt = null, timerSecs = 0;
function newMission() {
  const pool = MISSIONS.filter(m => m.w === selWhere && m.t === selTime);
  currentMission = pool.length ? rand(pool) : rand(MISSIONS);
  missionAccepted = false;
  $("#missionTag").textContent = "YOUR MISSION · " + WHERES.find(w => w[0] === currentMission.w)[1].toUpperCase();
  $("#missionTime").textContent = currentMission.t === 2 ? "⏱ 2 minutes" : currentMission.t === 10 ? "⏱ 10 minutes" : "☀️ sometime today";
  $("#missionTitle").textContent = currentMission.title;
  $("#missionBody").textContent = currentMission.body;
  $("#missionSteps").innerHTML = currentMission.steps.map(s => `<li>${s}</li>`).join("");
  $("#doneMission").classList.add("hidden");
  $("#acceptMission").classList.remove("hidden");
  $("#missionAccepted").classList.add("hidden");
  const showTimer = currentMission.t !== 999;
  $("#timerBox").classList.toggle("hidden", !showTimer);
  clearInterval(timerInt); timerSecs = currentMission.t * 60;
  renderTimer(); $("#timerBtn").textContent = "Start timer";
  updatePlan();
}
function renderTimer() { $("#timerDisplay").textContent = `${String(Math.floor(timerSecs / 60)).padStart(2, "0")}:${String(timerSecs % 60).padStart(2, "0")}`; }
$("#timerBtn").onclick = (e) => {
  if (timerInt) { clearInterval(timerInt); timerInt = null; e.target.textContent = "Resume timer"; return; }
  e.target.textContent = "Pause";
  timerInt = setInterval(() => {
    timerSecs--; renderTimer();
    if (timerSecs <= 0) { clearInterval(timerInt); timerInt = null; toast("Time! However it went, showing up was the mission. Mark it done below 🌱"); $("#timerBtn").textContent = "Start timer"; }
  }, 1000);
};
$("#shuffleMission").onclick = newMission;
$("#acceptMission").onclick = () => {
  missionAccepted = true;
  $("#acceptMission").classList.add("hidden");
  $("#doneMission").classList.remove("hidden");
  $("#missionAccepted").classList.remove("hidden");
  toast("Mission accepted. The world just got put on notice. (Gently.)");
  updatePlan();
};
let seeds = 0;
const FLOWERS = ["🌻", "🌷", "🌼", "🌸", "🪻", "🌺", "🍀", "🌹"];
$("#doneMission").onclick = () => {
  seeds++; markJourney("mission");
  const bed = $("#gardenBed");
  $("#gardenEmpty")?.remove();
  const f = document.createElement("span"); f.className = "flower"; f.textContent = rand(FLOWERS); f.title = currentMission.title;
  bed.appendChild(f);
  $("#gardenCount").textContent = `${seeds} seed${seeds > 1 ? "s" : ""} planted — latest: “${currentMission.title}”`;
  $("#doneMission").classList.add("hidden");
  toast(`Seed ${seeds} planted 🌱 One real act > a thousand intentions. Pick another whenever you’re ready.`);
  newMission();
  updatePlan();
};
$("#heroMission").onclick = () => { selWhere = rand(WHERES)[0]; selTime = 2; renderChips(); newMission(); document.querySelector("#mission").scrollIntoView({ behavior: "smooth" }); toast("A fresh 2-minute mission is waiting below ↓"); };
renderChips(); newMission();

/* ripple calculator */
function ripple() {
  const pct = +$("#rippleSlider").value;
  const people = 8.2e9 * pct / 100;
  $("#ripplePeople").textContent = fmt(people) + " people";
  $("#rippleActs").textContent = fmt(people * 52);
  $("#rippleReach").textContent = "~3 each";
  $("#rippleDays").textContent = fmt(people * 52 / 365);
}
$("#rippleSlider").addEventListener("input", ripple); ripple();

/* ---------- 06 constellation ---------- */
const WORDS = ["Kindness", "Courage", "Enough", "Wonder", "Patience", "Laughter", "Shelter", "Forgiveness", "Curiosity", "Peace"];
let lightsAdded = 0, baseLights = 12408;
function renderWordChips() { chips($("#wordChips"), WORDS.map(w => [w, "✦ " + w]), selWord, (v) => { selWord = v; renderWordChips(); updatePlan(); }); }
renderWordChips();

const stars = [];
(() => {
  const cv = $("#constellation"), ctx = cv.getContext("2d");
  let W, H;
  function size() { const r = cv.getBoundingClientRect(), d = Math.min(devicePixelRatio || 1, 2); W = r.width; H = r.height; cv.width = W * d; cv.height = H * d; ctx.setTransform(d, 0, 0, d, 0, 0); }
  size(); addEventListener("resize", size);
  for (let i = 0; i < 130; i++) stars.push({ x: Math.random(), y: Math.random(), r: Math.random() * 1.6 + .4, p: Math.random() * 7, mine: false, word: "" });
  window.__addStar = (word) => stars.push({ x: .15 + Math.random() * .7, y: .15 + Math.random() * .7, r: 3.2, p: 0, mine: true, word });
  (function draw(t) {
    ctx.clearRect(0, 0, W, H);
    for (const s of stars) {
      const tw = .55 + .45 * Math.sin(t / 900 + s.p);
      ctx.globalAlpha = s.mine ? 1 : tw * .8;
      ctx.fillStyle = s.mine ? "#ffb627" : "#dbe7ff";
      ctx.beginPath(); ctx.arc(s.x * W, s.y * H, s.r * (s.mine ? 1 + .2 * Math.sin(t / 300) : 1), 0, 7); ctx.fill();
      if (s.mine) { ctx.globalAlpha = .18; ctx.beginPath(); ctx.arc(s.x * W, s.y * H, s.r * 4, 0, 7); ctx.fill(); }
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  })(0);
})();
$("#lightBtn").onclick = () => {
  lightsAdded++; baseLights++;
  window.__addStar(selWord);
  $("#lightCount").textContent = baseLights.toLocaleString();
  $("#myWordEcho").textContent = `yours says “${selWord}”`;
  toast(`✦ Your light is on: “${selWord}” — for all 8.2 billion of us.`);
  updatePlan();
};

/* ---------- take-away plan ---------- */
function updatePlan() {
  const bits = [];
  if (livesVisited) bits.push(`I met ${livesVisited} neighbor${livesVisited > 1 ? "s" : ""} I’ll never meet`);
  if (currentMission) bits.push(`my mission is “${currentMission.title}” (${currentMission.t === 999 ? "today" : currentMission.t + " minutes"})`);
  if (seeds) bits.push(`I’ve planted ${seeds} kindness seed${seeds > 1 ? "s" : ""}`);
  bits.push(`my word for the world is “${selWord}”`);
  $("#planText").textContent = bits.length > 1
    ? `Today: ${bits.join("; ")}. Small, specific, done — at planetary scale, that’s everything.`
    : "Meet a neighbor above, take a breath, and do one small kind act today. That’s it. That’s the plan.";
}
$("#copyPlan").onclick = async () => {
  const text = `🌍 My 8-Billion-Neighbors plan — ${$("#planText").textContent}`;
  try { await navigator.clipboard.writeText(text); $("#copyNote").textContent = "Copied ✓ Send it to one person. Plans, like kindness, propagate."; }
  catch { $("#copyNote").textContent = text; toast("Copy blocked here — your plan is printed above the button instead."); }
};
updatePlan();
