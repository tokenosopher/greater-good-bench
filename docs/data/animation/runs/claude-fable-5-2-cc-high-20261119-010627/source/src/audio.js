// Soundtrack synth for "Be the Heartbeat": monitor beeps, a fall, three dial tones,
// then a 110-bpm compression beat under a slow I-IV-I swell. Writes a 16-bit stereo WAV.
'use strict';
const fs = require('fs');
const R = require('./render.js');
const SR = 44100, DUR = R.NFRAMES / R.FPS, N = Math.round(DUR * SR);
const Lc = new Float32Array(N), Rc = new Float32Array(N);
const TAU = Math.PI * 2;
const add = (t0, len, fn, pan = 0) => {
  const i0 = Math.max(0, Math.round(t0 * SR)), i1 = Math.min(N, Math.round((t0 + len) * SR));
  const gl = Math.cos((pan + 1) * Math.PI / 4), gr = Math.sin((pan + 1) * Math.PI / 4);
  for (let i = i0; i < i1; i++) { const v = fn((i - i0) / SR); Lc[i] += v * gl * 1.414; Rc[i] += v * gr * 1.414; }
};
const env = (t, a, len, r) => Math.min(1, t / a) * Math.min(1, Math.max(0, (len - t) / r));
const hz = m => 440 * Math.pow(2, (m - 69) / 12);
let seed = 7; const noise = () => { seed = (seed * 1664525 + 1013904223) >>> 0; return seed / 2147483648 - 1; };

// 1. heart monitor: two beeps, then the tone that doesn't stop
for (const q of R.QRS_X) add((q - R.SWEEP_X0) / R.SWEEP_V, 0.09, t => 0.10 * Math.sin(TAU * 988 * t) * env(t, 0.004, 0.09, 0.03), -0.2);
add(0.80, 0.95, t => 0.055 * Math.sin(TAU * 988 * t) * env(t, 0.03, 0.95, 0.6), -0.2);
// 2. the fall
add(R.T_FALL1 - 0.02, 0.4, t => 0.5 * Math.sin(TAU * (42 * t + 60 * 0.05 * (1 - Math.exp(-t / 0.05)))) * Math.exp(-t / 0.09) + 0.10 * noise() * Math.exp(-t / 0.02));
// 3. dialling: 1-1-2
[[697, 1209], [697, 1209], [697, 1336]].forEach(([f1, f2], i) =>
  add(R.T_CALL0 + 0.04 + i * 0.17, 0.11, t => 0.05 * (Math.sin(TAU * f1 * t) + Math.sin(TAU * f2 * t)) * env(t, 0.004, 0.11, 0.02), -0.35));
// 4. compressions: one thump per beat, 110 a minute
const chords = [[50, 57, 62, 66], [50, 55, 62, 67], [50, 57, 62, 66]];      // D, G/D, D
const lead = [[74, 78, 81, 78], [74, 79, 83, 79], [74, 78, 81, 86]];
for (let k = R.FIRST_BEAT; k < 18; k++) {
  const t0 = k * R.BEAT, n = k - R.FIRST_BEAT, bar = Math.min(2, Math.floor(n / 4));
  const lift = 0.75 + 0.25 * Math.min(1, n / 4);
  add(t0 - 0.004, 0.45, t => lift * (0.62 * Math.sin(TAU * (48 * t + 95 * 0.035 * (1 - Math.exp(-t / 0.035)))) * Math.exp(-t / 0.13)
    + 0.20 * Math.sin(TAU * 190 * t) * Math.exp(-t / 0.035) + 0.07 * noise() * Math.exp(-t / 0.006)));
  // a small bell on each push, climbing through the chord
  const f = hz(lead[bar][n % 4]);
  add(t0, 0.9, t => 0.075 * lift * (Math.sin(TAU * f * t) + 0.3 * Math.sin(TAU * 2 * f * t) * Math.exp(-t / 0.08)) * Math.exp(-t / 0.28) * Math.min(1, t / 0.003), (n % 2 ? 0.35 : -0.35));
}
// 5. the swell underneath
for (let bar = 0; bar < 3; bar++) {
  const t0 = (R.FIRST_BEAT + bar * 4) * R.BEAT - 0.25, len = 4 * R.BEAT + 0.5;
  chords[bar].forEach((m, j) => {
    const f = hz(m), det = 1 + (j % 2 ? 0.003 : -0.003), g = 0.030 + 0.018 * bar;
    add(t0, len, t => g * (Math.sin(TAU * f * det * t) + 0.35 * Math.sin(TAU * 2 * f * t) + 0.12 * Math.sin(TAU * 3 * f * det * t)) * env(t, 0.35, len, 0.5), j % 2 ? 0.5 : -0.5);
  });
}
// master: soft clip, tiny fades so the loop point is clean
const buf = Buffer.alloc(44 + N * 4);
buf.write('RIFF', 0); buf.writeUInt32LE(36 + N * 4, 4); buf.write('WAVEfmt ', 8); buf.writeUInt32LE(16, 16);
buf.writeUInt16LE(1, 20); buf.writeUInt16LE(2, 22); buf.writeUInt32LE(SR, 24); buf.writeUInt32LE(SR * 4, 28);
buf.writeUInt16LE(4, 32); buf.writeUInt16LE(16, 34); buf.write('data', 36); buf.writeUInt32LE(N * 4, 40);
for (let i = 0; i < N; i++) {
  const t = i / SR, fade = Math.min(1, t / 0.01) * Math.min(1, (DUR - t) / 0.05);
  buf.writeInt16LE(Math.round(Math.tanh(Lc[i] * 1.15) * fade * 30000), 44 + i * 4);
  buf.writeInt16LE(Math.round(Math.tanh(Rc[i] * 1.15) * fade * 30000), 46 + i * 4);
}
fs.writeFileSync(process.argv[2] || 'audio.wav', buf);
