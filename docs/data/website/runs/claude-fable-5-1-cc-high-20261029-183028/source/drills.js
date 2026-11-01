// Interactive drills. Each export returns a DOM element and may register a cleanup via ctx.onLeave.
import { el, fmt } from "./util.js";

/* ---------- CPR metronome + tap-rate test ---------- */
export function metronome(ctx) {
  const BPM = 110;
  let audio = null, timer = null, running = false, beats = 0, startedAt = 0;

  const svg = el("div", { class: "heart", "aria-hidden": "true" });
  svg.innerHTML = `
  <svg viewBox="0 0 150 150" width="150" height="150">
    <!-- torso seen from above -->
    <path class="torso" d="M30 150 L30 70 Q30 52 48 50 L102 50 Q120 52 120 70 L120 150 Z"/>
    <path class="sternum" d="M75 58 V110 M50 72 Q75 66 100 72 M48 86 Q75 80 102 86 M50 100 Q75 94 100 100"/>
    <!-- downward arrow -->
    <path class="arrow" d="M75 6 L75 34 M63 24 L75 36 L87 24" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round" fill="none" style="stroke:var(--red)"/>
    <!-- stacked hands -->
    <g class="hands">
      <rect class="hand" x="52" y="78" width="46" height="22" rx="11"/>
      <rect class="hand" x="58" y="68" width="34" height="18" rx="9"/>
    </g>
  </svg>`;
  const bpmEl = el("div", { class: "bpm" }, `${BPM}`);
  const sub = el("div", { class: "count" }, "pushes per minute · press start and push along");
  const startBtn = el("button", { class: "btn big" }, "Start the beat");
  const stopBtn = el("button", { class: "btn secondary", style: "display:none" }, "Stop");
  const metro = el("div", { class: "metro" }, [svg, bpmEl, sub, el("div", { class: "row", style: "justify-content:center;margin-top:8px" }, [startBtn, stopBtn])]);

  function click() {
    try {
      if (!audio) audio = new (window.AudioContext || window.webkitAudioContext)();
      const o = audio.createOscillator(), g = audio.createGain();
      o.type = "square"; o.frequency.value = beats % 30 === 0 ? 1100 : 820;
      g.gain.setValueAtTime(0.0001, audio.currentTime);
      g.gain.exponentialRampToValueAtTime(0.25, audio.currentTime + 0.004);
      g.gain.exponentialRampToValueAtTime(0.0001, audio.currentTime + 0.06);
      o.connect(g).connect(audio.destination);
      o.start(); o.stop(audio.currentTime + 0.07);
    } catch (e) { /* audio unavailable; visual still works */ }
  }
  function tick() {
    beats++;
    click();
    metro.classList.add("beat");
    setTimeout(() => metro.classList.remove("beat"), 120);
    const secs = Math.round((Date.now() - startedAt) / 1000);
    const cycle = Math.floor(beats / 30) % 2 === 0 ? "" : "";
    sub.textContent = `${beats} pushes · ${fmt(secs)} ${beats >= 220 ? "— swap with someone if you can" : cycle}`;
    if (beats % 30 === 0 && beats > 0) ctx.toast(`${beats} compressions — keep going`);
  }
  function start() {
    if (running) return;
    running = true; beats = 0; startedAt = Date.now();
    if (audio && audio.state === "suspended") audio.resume();
    tick();
    timer = setInterval(tick, 60000 / BPM);
    startBtn.style.display = "none"; stopBtn.style.display = "";
  }
  function stop() {
    running = false; clearInterval(timer); timer = null;
    startBtn.style.display = ""; stopBtn.style.display = "none";
    startBtn.textContent = "Start again";
    sub.textContent = `You did ${beats} pushes in ${fmt(Math.round((Date.now() - startedAt) / 1000))}. Real CPR goes on until help arrives — often 8–15 minutes.`;
  }
  startBtn.onclick = start; stopBtn.onclick = stop;
  ctx.onLeave(() => { clearInterval(timer); if (audio) { try { audio.close(); } catch (e) {} } });

  /* tap test */
  let taps = [];
  const res = el("span", { class: "result" }, "—");
  const verdict = el("span", { class: "verdict" }, "Tap this box (or press space) at the speed you'd push. 10 taps gives a reading.");
  const zone = el("div", { class: "tap-zone", tabindex: "0", role: "button", "aria-label": "Tap area for compression rate test" }, [
    "Tap here at your CPR speed", res, verdict,
  ]);
  function tap() {
    const now = performance.now();
    if (taps.length && now - taps[taps.length - 1] > 2500) taps = [];
    taps.push(now);
    if (taps.length > 12) taps.shift();
    zone.classList.remove("good", "slow", "fast");
    if (taps.length >= 4) {
      const ms = (taps[taps.length - 1] - taps[0]) / (taps.length - 1);
      const bpm = Math.round(60000 / ms);
      res.textContent = `${bpm} / min`;
      if (taps.length < 10) { verdict.textContent = `${taps.length} taps… keep going`; return; }
      if (bpm < 100) { zone.classList.add("slow"); verdict.textContent = "Too slow. Speed up — think “Stayin’ Alive”."; }
      else if (bpm > 120) { zone.classList.add("fast"); verdict.textContent = "Too fast — the heart can't refill. Ease off a touch."; }
      else { zone.classList.add("good"); verdict.textContent = "Perfect. That's the rate. Now push 5 cm deep and don't stop."; ctx.credit("tap"); }
    } else {
      res.textContent = "…"; verdict.textContent = `${taps.length} taps`;
    }
  }
  zone.addEventListener("pointerdown", (e) => { e.preventDefault(); tap(); });
  zone.addEventListener("keydown", (e) => { if (e.code === "Space" || e.key === "Enter") { e.preventDefault(); tap(); } });

  return el("div", {}, [
    el("p", {}, "Push along with the beat. Push with locked arms and your body weight — on a sofa cushion or a firm pillow if you want to feel the depth. Real compressions are tiring; that's a sign you're doing them right."),
    metro,
    el("h3", { style: "margin-top:22px" }, "Check your own rhythm"),
    zone,
  ]);
}

/* ---------- Branching scenario ---------- */
export function flow(ctx, spec) {
  const wrap = el("div", { class: "flow" });
  let mistakes = 0, node = spec.start;
  function render() {
    wrap.innerHTML = "";
    const n = spec.nodes[node];
    if (n.done) {
      wrap.append(el("div", { class: "explain ok" }, [
        el("b", {}, mistakes === 0 ? "Perfect run. " : `Done, with ${mistakes} wrong turn${mistakes > 1 ? "s" : ""} — now you know. `),
        ctx.sub(n.done),
      ]));
      const again = el("button", { class: "btn secondary", style: "margin-top:10px" }, "Run it again");
      again.onclick = () => { mistakes = 0; node = spec.start; render(); };
      wrap.append(again);
      ctx.credit("flow");
      return;
    }
    if (n.explain) {
      wrap.append(el("div", { class: "explain no" }, ctx.sub(n.explain)));
      const b = el("button", { class: "btn", style: "margin-top:10px" }, "Got it — continue");
      b.onclick = () => { node = n.next; render(); };
      wrap.append(b);
      return;
    }
    wrap.append(el("div", { class: "q" }, ctx.sub(n.q)));
    const choices = el("div", { class: "choices" });
    n.choices.forEach((c) => {
      const b = el("button", { class: "choice" }, ctx.sub(c.t));
      b.onclick = () => {
        [...choices.children].forEach((x) => (x.disabled = true));
        b.classList.add(c.ok ? "picked-right" : "picked-wrong");
        if (!c.ok) mistakes++;
        setTimeout(() => { node = c.next; render(); }, c.ok ? 450 : 350);
      };
      choices.append(b);
    });
    wrap.append(choices);
  }
  render();
  return wrap;
}

/* ---------- Press and hold (bleeding) ---------- */
export function pressure(ctx) {
  const GOAL = 20;
  let held = false, t0 = 0, raf = null, done = false;
  const big = el("div", { class: "big" }, "0.0 s");
  const phase = el("div", { class: "phase" }, "Press and hold the button. Don't let go.");
  const btn = el("button", { class: "btn big", style: "width:100%;max-width:420px;padding:34px 20px;font-size:1.3rem", "aria-label": "Press and hold to apply pressure" }, "PRESS HARD — HOLD");
  const bar = el("div", { class: "bar", style: "max-width:420px;margin:12px auto 0" }, [el("i")]);
  function loop() {
    if (!held) return;
    const s = (performance.now() - t0) / 1000;
    big.textContent = `${s.toFixed(1)} s`;
    bar.firstChild.style.width = `${Math.min(100, (s / GOAL) * 100)}%`;
    if (s >= 5 && s < 5.5) phase.textContent = "It should hurt them. Lean your body weight in.";
    if (s >= 10 && s < 10.5) phase.textContent = "Soaking through? Add more cloth on TOP. Keep pressing.";
    if (s >= 15 && s < 15.5) phase.textContent = "Don't peek. Looking restarts the bleeding.";
    if (s >= GOAL) { done = true; held = false; phase.textContent = `${GOAL} seconds. In real life you hold this for 10 minutes or more, until help takes over. You can.`; btn.textContent = "Done — that's the skill"; btn.classList.add("green"); ctx.credit("pressure"); return; }
    raf = requestAnimationFrame(loop);
  }
  function down(e) { if (done) return; e.preventDefault(); held = true; t0 = performance.now(); phase.textContent = "Keep holding…"; btn.textContent = "KEEP PRESSING"; raf = requestAnimationFrame(loop); }
  function up() { if (!held || done) return; held = false; cancelAnimationFrame(raf); big.textContent = "0.0 s"; bar.firstChild.style.width = "0%"; phase.textContent = "You let go — the bleeding restarts. Press again, and this time don't release."; btn.textContent = "PRESS HARD — HOLD"; }
  btn.addEventListener("pointerdown", down);
  btn.addEventListener("pointerup", up);
  btn.addEventListener("pointerleave", up);
  btn.addEventListener("pointercancel", up);
  btn.addEventListener("keydown", (e) => { if ((e.code === "Space" || e.key === "Enter") && !e.repeat) down(e); });
  btn.addEventListener("keyup", (e) => { if (e.code === "Space" || e.key === "Enter") up(); });
  ctx.onLeave(() => cancelAnimationFrame(raf));
  return el("div", { class: "timer" }, [
    el("p", { style: "text-align:left" }, "The hardest part of stopping bleeding isn't technique. It's not letting go. Hold for 20 seconds without releasing."),
    big, phase, btn, bar,
  ]);
}

/* ---------- Select-the-signs (heart attack) ---------- */
export function signs(ctx, spec) {
  const wrap = el("div", { class: "flow" });
  const picked = new Set();
  wrap.append(el("div", { class: "q" }, spec.intro));
  const choices = el("div", { class: "choices" });
  spec.items.forEach((it, i) => {
    const b = el("button", { class: "choice", "aria-pressed": "false" }, it.t);
    b.onclick = () => { if (picked.has(i)) picked.delete(i); else picked.add(i); b.style.borderColor = picked.has(i) ? "var(--blue)" : ""; b.style.background = picked.has(i) ? "var(--blue-soft)" : ""; b.setAttribute("aria-pressed", String(picked.has(i))); };
    choices.append(b);
  });
  const out = el("div");
  const check = el("button", { class: "btn", style: "margin-top:12px" }, "Check my answers");
  check.onclick = () => {
    let right = 0;
    out.innerHTML = "";
    spec.items.forEach((it, i) => {
      const b = choices.children[i]; b.disabled = true; b.style.background = ""; b.style.borderColor = "";
      const ok = picked.has(i) === it.yes;
      if (ok) right++;
      b.classList.add(ok ? "picked-right" : "picked-wrong");
      if (!ok && it.why) out.append(el("div", { class: "explain no", style: "margin-top:8px" }, [el("b", {}, it.yes ? "Call for this one. " : "Not this one. "), it.why]));
    });
    out.prepend(el("div", { class: `explain ${right === spec.items.length ? "ok" : ""}` }, right === spec.items.length ? "All correct. When in doubt, call — dispatchers would far rather send an ambulance to indigestion than miss a heart attack." : `${right} of ${spec.items.length}. Rule of thumb: chest discomfort plus sweating, breathlessness, nausea or dread — or exertional pain that keeps coming back — call.`));
    check.disabled = true;
    ctx.credit("signs");
  };
  wrap.append(choices, check, out);
  return wrap;
}

/* ---------- Tap-in-order (recovery position) ---------- */
export function order(ctx, spec) {
  const wrap = el("div", { class: "flow" });
  wrap.append(el("div", { class: "q" }, spec.intro));
  const idx = spec.items.map((_, i) => i);
  // deterministic shuffle so it's always jumbled the same way
  const shuffled = [2, 4, 0, 3, 1].filter((i) => i < idx.length);
  const choices = el("div", { class: "choices" });
  let expect = 0, wrong = 0;
  const msg = el("div", { class: "explain", style: "display:none" });
  shuffled.forEach((i) => {
    const b = el("button", { class: "choice" }, spec.items[i]);
    b.onclick = () => {
      if (i === expect) { b.classList.add("picked-right"); b.disabled = true; b.textContent = `${expect + 1}. ${spec.items[i]}`; expect++; }
      else { wrong++; b.classList.add("picked-wrong"); setTimeout(() => b.classList.remove("picked-wrong"), 500); msg.style.display = ""; msg.textContent = `Not yet — what comes at step ${expect + 1}? Think: arm, hand, knee, roll, head.`; }
      if (expect === spec.items.length) { msg.style.display = ""; msg.className = "explain ok"; msg.textContent = wrong ? `All five in order (after ${wrong} slip${wrong > 1 ? "s" : ""}). Arm — hand — knee — roll — head.` : "Perfect. Arm — hand — knee — roll — head. You could do this in the dark."; ctx.credit("order"); }
    };
    choices.append(b);
  });
  wrap.append(choices, msg);
  return wrap;
}

/* ---------- Pick-the-better-response (crisis) ---------- */
export function respond(ctx, spec) {
  const wrap = el("div", { class: "flow" });
  let i = 0, wrong = 0;
  function render() {
    wrap.innerHTML = "";
    if (i >= spec.items.length) {
      wrap.append(el("div", { class: "explain ok" }, [el("b", {}, wrong ? `Finished, ${wrong} to rethink. ` : "Every response right. "), "Ask. Listen. Keep safe. Connect. Follow up. You don't need the perfect words — you need to stay."]));
      ctx.credit("respond");
      return;
    }
    const it = spec.items[i];
    wrap.append(el("div", { class: "trail" }, `${i + 1} of ${spec.items.length} · ${spec.intro}`));
    wrap.append(el("div", { class: "q" }, it.said));
    const choices = el("div", { class: "choices" });
    const out = el("div");
    it.a.forEach((t, k) => {
      const b = el("button", { class: "choice" }, t);
      b.onclick = () => {
        [...choices.children].forEach((x) => (x.disabled = true));
        const ok = k === it.correct;
        if (!ok) wrong++;
        b.classList.add(ok ? "picked-right" : "picked-wrong");
        if (!ok) choices.children[it.correct].classList.add("picked-right");
        out.append(el("div", { class: `explain ${ok ? "ok" : "no"}` }, it.why));
        const next = el("button", { class: "btn", style: "margin-top:10px" }, i + 1 < spec.items.length ? "Next" : "Finish");
        next.onclick = () => { i++; render(); };
        out.append(next);
      };
      choices.append(b);
    });
    wrap.append(choices, out);
  }
  render();
  return wrap;
}

/* ---------- Multiple choice quiz (lesson check and final) ---------- */
export function quiz(ctx, questions, { onDone, title } = {}) {
  const wrap = el("div", { class: "quiz" });
  let i = 0, score = 0;
  function render() {
    wrap.innerHTML = "";
    if (i >= questions.length) {
      const pct = Math.round((score / questions.length) * 100);
      wrap.append(el("div", { class: "score" }, [
        el("div", { class: "big" }, `${score} / ${questions.length}`),
        el("p", {}, pct === 100 ? "Perfect. You're the person everyone hopes is standing nearby." : pct >= 70 ? "Solid. Re-read the ones you missed — they're the ones that come up at 2 am." : "Go back through the skills; each takes two minutes. Then try again."),
      ]));
      const again = el("button", { class: "btn secondary" }, "Try again");
      again.onclick = () => { i = 0; score = 0; render(); };
      wrap.append(again);
      if (onDone) onDone(score, questions.length);
      return;
    }
    const q = questions[i];
    wrap.append(el("div", { class: "qnum" }, `${title ? title + " · " : ""}Question ${i + 1} of ${questions.length}`));
    wrap.append(el("div", { class: "scenario" }, ctx.sub(q.q)));
    const choices = el("div", { class: "choices flow" });
    const out = el("div");
    q.a.forEach((t, k) => {
      const b = el("button", { class: "choice" }, ctx.sub(t));
      b.onclick = () => {
        [...choices.children].forEach((x) => (x.disabled = true));
        const ok = k === q.correct;
        if (ok) score++;
        b.classList.add(ok ? "picked-right" : "picked-wrong");
        if (!ok) choices.children[q.correct].classList.add("picked-right");
        out.append(el("div", { class: `explain ${ok ? "ok" : "no"}`, style: "margin-top:10px" }, ctx.sub(q.why)));
        const next = el("button", { class: "btn", style: "margin-top:10px" }, i + 1 < questions.length ? "Next" : "See result");
        next.onclick = () => { i++; render(); wrap.scrollIntoView({ block: "nearest", behavior: "smooth" }); };
        out.append(next);
      };
      choices.append(b);
    });
    choices.style.display = "grid"; choices.style.gap = "8px";
    wrap.append(choices, out);
  }
  render();
  return wrap;
}
