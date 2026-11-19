// All sound is synthesised with Web Audio: a metronome, a chest "thump", and small feedback tones.
import { state } from "./state.js";

let ctx = null;
let master = null;

/** Create (or resume) the audio context. Must be called from a user gesture. */
export function wake() {
  try {
    if (!ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return null;
      ctx = new AC();
      master = ctx.createGain();
      master.gain.value = 0.9;
      master.connect(ctx.destination);
    }
    if (ctx.state === "suspended") ctx.resume();
  } catch (e) {
    ctx = null;
  }
  return ctx;
}

function tone({ freq = 440, to = null, dur = 0.12, type = "sine", gain = 0.2, at = 0 }) {
  if (!state.sound) return;
  const c = wake();
  if (!c) return;
  try {
    const t = Math.max(c.currentTime, at || c.currentTime);
    const osc = c.createOscillator();
    const g = c.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, t);
    if (to) osc.frequency.exponentialRampToValueAtTime(to, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + 0.006);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    osc.connect(g).connect(master);
    osc.start(t);
    osc.stop(t + dur + 0.03);
  } catch (e) {
    /* audio is a bonus, never a requirement */
  }
}

export const sfx = {
  /** The dull thud of a chest compression. */
  thump() {
    tone({ freq: 120, to: 46, dur: 0.14, type: "sine", gain: 0.5 });
  },
  tap() {
    tone({ freq: 520, to: 380, dur: 0.06, type: "triangle", gain: 0.14 });
  },
  good() {
    tone({ freq: 660, dur: 0.11, type: "triangle", gain: 0.16 });
    const c = wake();
    if (c) tone({ freq: 990, dur: 0.2, type: "triangle", gain: 0.16, at: c.currentTime + 0.09 });
  },
  bad() {
    tone({ freq: 170, to: 120, dur: 0.2, type: "square", gain: 0.07 });
  },
  shock() {
    tone({ freq: 1400, to: 80, dur: 0.35, type: "sawtooth", gain: 0.16 });
  },
  hit() {
    tone({ freq: 210, to: 70, dur: 0.11, type: "triangle", gain: 0.4 });
  },
  win() {
    const c = wake();
    if (!c) return;
    [523, 659, 784, 1047].forEach((f, i) =>
      tone({ freq: f, dur: 0.22, type: "triangle", gain: 0.15, at: c.currentTime + i * 0.09 })
    );
  },
  click(at, accent) {
    tone({ freq: accent ? 1320 : 990, dur: 0.05, type: "square", gain: accent ? 0.16 : 0.1, at });
  },
};

/**
 * A drift-free metronome. Audio clicks are scheduled ahead on the audio clock;
 * `onBeat(n)` fires on (roughly) the same instant for visuals. If audio is not
 * available it falls back to a wall-clock timer so the visual beat still works.
 */
export function metronome({ bpm = 110, onBeat, audible = () => true, accentEvery = 0 }) {
  const period = 60 / bpm;
  let running = false;
  let timer = null;
  let beat = 0;
  let nextAudio = 0;
  let startWall = 0;

  function loop() {
    if (!running) return;
    const c = ctx && ctx.state === "running" ? ctx : null;
    if (c) {
      while (nextAudio < c.currentTime + 0.12) {
        const n = beat++;
        const delay = Math.max(0, (nextAudio - c.currentTime) * 1000);
        if (audible()) sfx.click(nextAudio, accentEvery && n % accentEvery === 0);
        setTimeout(() => running && onBeat && onBeat(n), delay);
        nextAudio += period;
      }
    } else {
      const now = performance.now() / 1000;
      while (startWall + beat * period <= now) {
        const n = beat++;
        if (onBeat) onBeat(n);
      }
    }
  }

  return {
    get running() {
      return running;
    },
    start() {
      if (running) return;
      running = true;
      beat = 0;
      const c = wake();
      nextAudio = c ? c.currentTime + 0.08 : 0;
      startWall = performance.now() / 1000 + 0.08;
      timer = setInterval(loop, 25);
      loop();
    },
    stop() {
      running = false;
      clearInterval(timer);
    },
  };
}
