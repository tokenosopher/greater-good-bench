'use strict';

const fs = require('fs');

function clamp(x, a, b) {
  return Math.min(b, Math.max(a, x));
}

function smoothstep(e0, e1, x) {
  const t = clamp((x - e0) / (e1 - e0 + 1e-9), 0, 1);
  return t * t * (3 - 2 * t);
}

/**
 * Generate a 10.0-second stereo 44.1kHz WAV file synchronized to the three acts
 */
function generateAudioWav(outPath, duration = 10.0, sampleRate = 44100) {
  const numSamples = Math.floor(duration * sampleRate);
  const dataSize = numSamples * 4; // 2 channels * 2 bytes (16-bit PCM)
  const buf = Buffer.alloc(44 + dataSize);

  // WAV Header
  buf.write('RIFF', 0);
  buf.writeUInt32LE(36 + dataSize, 4);
  buf.write('WAVE', 8);
  buf.write('fmt ', 12);
  buf.writeUInt32LE(16, 16);      // PCM chunk size
  buf.writeUInt16LE(1, 20);       // PCM format
  buf.writeUInt16LE(2, 22);       // 2 channels (Stereo)
  buf.writeUInt32LE(sampleRate, 24);
  buf.writeUInt32LE(sampleRate * 4, 28);
  buf.writeUInt16LE(4, 32);
  buf.writeUInt16LE(16, 34);      // 16 bits per sample
  buf.write('data', 36);
  buf.writeUInt32LE(dataSize, 40);

  // Pre-seed pink/airy noise state for realistic breath sound
  let b0 = 0, b1 = 0, b2 = 0;

  for (let i = 0; i < numSamples; i++) {
    const t = i / sampleRate;
    let left = 0.0;
    let right = 0.0;

    // White -> filtered soft noise for breath and crackle
    const white = (Math.sin(i * 12.9898 + 78.233) * 43758.5453) % 1.0 - 0.5;
    b0 = 0.99 * b0 + white * 0.05;
    b1 = 0.96 * b1 + white * 0.12;
    b2 = 0.85 * b2 + white * 0.25;
    const airy = b1 - b0;

    // --- ACT I (0.0s .. 2.65s): Tense rapid heartbeat + electric crackle ---
    if (t < 3.0) {
      const act1Env = smoothstep(0.05, 0.25, t) * (1.0 - smoothstep(2.55, 2.85, t));
      // Rapid heartbeat thump (3.2 Hz)
      const beatPhase = (t * 3.0) % 1.0;
      const thump = Math.exp(-beatPhase * 14.0) * Math.sin(2 * Math.PI * 58 * beatPhase);
      // Low tense drone (D2 + Ab2 tritone tension)
      const drone = 0.12 * Math.sin(2 * Math.PI * 73.42 * t) + 0.08 * Math.sin(2 * Math.PI * 103.83 * t);
      // Bolt impact crackles at t=0.2s, t=0.8s, t=1.25s
      const c1 = Math.exp(-Math.max(0, t - 0.20) * 9) * (t >= 0.20 ? 1 : 0);
      const c2 = Math.exp(-Math.max(0, t - 0.80) * 8) * (t >= 0.80 ? 1 : 0);
      const c3 = Math.exp(-Math.max(0, t - 1.25) * 7) * (t >= 1.25 ? 1 : 0);
      const crackle = (c1 + c2 + c3) * (b2 * 0.65);

      left += act1Env * (thump * 0.35 + drone + crackle);
      right += act1Env * (thump * 0.35 + drone * 0.9 + crackle * 0.85);
    }

    // --- THE PAUSE CHIME (t = 2.60s): Tibetan singing bowl resonance ---
    if (t >= 2.58 && t < 6.5) {
      const dt = t - 2.58;
      const bowlEnv = smoothstep(0.0, 0.03, dt) * Math.exp(-dt * 1.15);
      const bowl = 0.22 * Math.sin(2 * Math.PI * 528.0 * dt)
        + 0.10 * Math.sin(2 * Math.PI * 1056.0 * dt + 0.3)
        + 0.06 * Math.sin(2 * Math.PI * 792.0 * dt);
      left += bowlEnv * bowl;
      right += bowlEnv * bowl * 0.95;
    }

    // --- ACT II (3.0s .. 7.25s): THE PHYSIOLOGICAL SIGH (Inhale 1 -> Top-Up Inhale 2 -> Long Slow Exhale) ---
    // 1. Inhale 1 (3.00s .. 4.15s)
    if (t >= 2.98 && t < 4.25) {
      const u = clamp((t - 3.00) / 1.15, 0, 1);
      const env = Math.sin(u * Math.PI);
      const pitch = 261.63 + u * 65.0; // Rising C4 -> E4 warm air
      const breathSound = airy * 1.6 + 0.14 * Math.sin(2 * Math.PI * pitch * t);
      left += env * breathSound * 0.55;
      right += env * breathSound * 0.60;
    }

    // 2. Inhale 2 Top-Up Sniff (4.18s .. 4.88s) + Alveolar Sparkle Chime
    if (t >= 4.16 && t < 5.20) {
      const u = clamp((t - 4.18) / 0.68, 0, 1);
      const env = Math.sin(u * Math.PI);
      const dt = t - 4.20;
      const chimeEnv = dt > 0 ? Math.exp(-dt * 3.5) : 0;
      const topUp = env * (airy * 2.0) + chimeEnv * (
        0.18 * Math.sin(2 * Math.PI * 659.25 * t) +
        0.14 * Math.sin(2 * Math.PI * 783.99 * t) +
        0.10 * Math.sin(2 * Math.PI * 1046.50 * t)
      );
      left += topUp * 0.65;
      right += topUp * 0.70;
    }

    // 3. Long Slow Exhale (4.95s .. 7.25s): Warm Vagal Release & Firefly Shimmer
    if (t >= 4.92 && t < 7.50) {
      const u = clamp((t - 4.95) / 2.30, 0, 1);
      const env = Math.sin(u * Math.PI);
      // Warm Fmaj7 -> Cmaj9 harmonic pad + gentle airy exhale
      const pad = 0.14 * Math.sin(2 * Math.PI * 174.61 * t) // F3
        + 0.12 * Math.sin(2 * Math.PI * 261.63 * t)         // C4
        + 0.10 * Math.sin(2 * Math.PI * 329.63 * t)         // E4
        + 0.08 * Math.sin(2 * Math.PI * 392.00 * t);        // G4
      // Pentatonic firefly chimes as the red bolt shatters (t = 5.2 .. 6.8)
      let sparkles = 0.0;
      const notes = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.50];
      for (let k = 0; k < 6; k++) {
        const nt = t - (5.20 + k * 0.24);
        if (nt > 0 && nt < 0.9) {
          sparkles += Math.exp(-nt * 5.5) * 0.07 * Math.sin(2 * Math.PI * notes[k] * nt);
        }
      }
      left += env * (airy * 1.1 + pad) + sparkles;
      right += env * (airy * 1.0 + pad * 1.05) + sparkles * 0.9;
    }

    // --- ACT III (7.20s .. 10.0s): Warm Co-Regulation Chord & Global Ripple ---
    if (t >= 7.10) {
      const env = smoothstep(7.10, 7.75, t) * (1.0 - smoothstep(9.55, 10.0, t));
      // Warm Cmaj9 / G6 celestial resolution chord
      const chord = 0.16 * Math.sin(2 * Math.PI * 130.81 * t) // C3
        + 0.13 * Math.sin(2 * Math.PI * 196.00 * t)           // G3
        + 0.11 * Math.sin(2 * Math.PI * 246.94 * t)           // B3
        + 0.12 * Math.sin(2 * Math.PI * 293.66 * t)           // D4
        + 0.10 * Math.sin(2 * Math.PI * 329.63 * t)           // E4
        + 0.07 * Math.sin(2 * Math.PI * 392.00 * t);          // G4

      // Gentle calm coherent heartbeat (1.0 Hz = 60 BPM)
      const calmBeatPhase = ((t - 7.2) * 1.05) % 1.0;
      const calmBeat = Math.exp(-calmBeatPhase * 10.0) * Math.sin(2 * Math.PI * 52 * calmBeatPhase) * 0.18;

      left += env * (chord + calmBeat);
      right += env * (chord * 0.98 + calmBeat);
    }

    // Soft master limiter
    const sL = Math.tanh(left * 0.95);
    const sR = Math.tanh(right * 0.95);

    const pcmL = Math.max(-32767, Math.min(32767, Math.round(sL * 32767)));
    const pcmR = Math.max(-32767, Math.min(32767, Math.round(sR * 32767)));

    const offset = 44 + i * 4;
    buf.writeInt16LE(pcmL, offset);
    buf.writeInt16LE(pcmR, offset + 2);
  }

  fs.writeFileSync(outPath, buf);
}

module.exports = { generateAudioWav };
