// ==========================================================================
// Procedural Web Audio Engine (Zero external assets, 100% offline safe)
// ==========================================================================

class SoundEngine {
  constructor() {
    this.ctx = null;
    this.enabled = true;
  }

   ensureContext() {
    if (!this.enabled) return null;
    try {
      if (!this.ctx) {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx) {
          this.ctx = new AudioCtx();
        }
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {});
      }
      return this.ctx;
    } catch {
      return null;
    }
  }

  toggle() {
    this.enabled = !this.enabled;
    if (this.enabled) {
      this.playClick(720);
    }
    return this.enabled;
  }

  // Crisp woodblock / clinical pulse for 110 BPM CPR metronome & compressions
  playCprBeat(isGoodZone = true, isGuideTick = false) {
    const ctx = this.ensureContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = isGuideTick ? 'triangle' : 'sine';
      const baseFreq = isGuideTick ? 587.33 : (isGoodZone ? 523.25 : 370.0);
      osc.frequency.setValueAtTime(baseFreq * 1.35, now);
      osc.frequency.exponentialRampToValueAtTime(baseFreq, now + 0.045);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(isGuideTick ? 0.14 : 0.22, now + 0.006);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.095);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.1);
    } catch {
      // Ignore audio errors in restricted sandboxes
    }
  }

  // Gentle harmonic cue for breath phases
  playBreathCue(phase) {
    const ctx = this.ensureContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();

      osc.type = 'sine';
      if (phase === 'inhale1') {
        osc.frequency.setValueAtTime(261.63, now); // C4
        osc.frequency.exponentialRampToValueAtTime(329.63, now + 0.35); // E4
      } else if (phase === 'inhale2') {
        osc.frequency.setValueAtTime(392.00, now); // G4
        osc.frequency.exponentialRampToValueAtTime(523.25, now + 0.25); // C5 (top-up pop)
      } else if (phase === 'hold') {
        osc.frequency.setValueAtTime(392.00, now);
      } else {
        // Exhale downshift
        osc.frequency.setValueAtTime(329.63, now);
        osc.frequency.exponentialRampToValueAtTime(196.00, now + 0.55); // G3
      }

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(0.09, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.6);

      osc.connect(gain);
      gain.connect(ctx.destination);

      osc.start(now);
      osc.stop(now + 0.65);
    } catch {
      // Ignore
    }
  }

  playClick(freq = 640) {
    const ctx = this.ensureContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime;
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, now);
      gain.gain.setValueAtTime(0.06, now);
      gain.gain.exponentialRampToValueAtTime(0.001, now + 0.035);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start(now);
      osc.stop(now + 0.04);
    } catch {
      // Ignore
    }
  }

  playSuccessChord() {
    const ctx = this.ensureContext();
    if (!ctx) return;
    try {
      const now = ctx.currentTime;
      const freqs = [261.63, 329.63, 392.00, 523.25];
      freqs.forEach((f, idx) => {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(f, now + idx * 0.045);
        gain.gain.setValueAtTime(0.001, now + idx * 0.045);
        gain.gain.linearRampToValueAtTime(0.07, now + idx * 0.045 + 0.02);
        gain.gain.exponentialRampToValueAtTime(0.001, now + idx * 0.045 + 0.45);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start(now + idx * 0.045);
        osc.stop(now + idx * 0.045 + 0.5);
      });
    } catch {
      // Ignore
    }
  }
}

export const sound = new SoundEngine();
