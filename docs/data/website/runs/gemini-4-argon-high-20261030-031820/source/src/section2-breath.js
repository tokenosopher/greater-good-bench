// ==========================================================================
// SCALE II: THE FIRST 60 SECONDS — Steady a Mind (Autonomic & Cognitive Reset)
// ==========================================================================

import { sound } from './audio.js';

const BREATH_MODES = {
  sigh: {
    name: 'Physiological Sigh (Double Inhale + Long Exhale)',
    desc: 'Two consecutive inhales through the nose (1st deep inhale fills ~80% of lungs; 2nd sharp top-up pops open collapsed alveoli), followed by a long, unhurried exhale through the mouth.',
    phases: [
      { id: 'inhale1', label: '1. DEEP INHALE (NOSE)', duration: 2.2, startVol: 0.15, endVol: 0.78 },
      { id: 'inhale2', label: '2. SHARP TOP-UP INHALE (NOSE)', duration: 1.1, startVol: 0.78, endVol: 1.0 },
      { id: 'exhale',  label: '3. LONG SLOW EXHALE (MOUTH)', duration: 5.7, startVol: 1.0, endVol: 0.15 }
    ]
  },
  box: {
    name: 'Box Breathing (4–4–4–4 Tactical Equilibrium)',
    desc: 'Equal 4-second phases stabilize arterial CO2 levels and restore prefrontal executive control during high-stress decision-making.',
    phases: [
      { id: 'inhale1', label: '1. INHALE (4 SEC)', duration: 4.0, startVol: 0.15, endVol: 0.95 },
      { id: 'hold',    label: '2. HOLD FULL (4 SEC)', duration: 4.0, startVol: 0.95, endVol: 0.95 },
      { id: 'exhale',  label: '3. EXHALE SMOOTHLY (4 SEC)', duration: 4.0, startVol: 0.95, endVol: 0.15 },
      { id: 'hold',    label: '4. HOLD EMPTY (4 SEC)', duration: 4.0, startVol: 0.15, endVol: 0.15 }
    ]
  },
  downshift: {
    name: '4–7–8 Parasympathetic Brake',
    desc: 'Extended breath retention increases blood CO2 mildly to dilate cerebral vessels, followed by an 8-second vagal exhale.',
    phases: [
      { id: 'inhale1', label: '1. QUIET INHALE (4 SEC)', duration: 4.0, startVol: 0.15, endVol: 0.95 },
      { id: 'hold',    label: '2. STEADY HOLD (7 SEC)', duration: 7.0, startVol: 0.95, endVol: 0.95 },
      { id: 'exhale',  label: '3. COMPLETE EXHALE (8 SEC)', duration: 8.0, startVol: 0.95, endVol: 0.15 }
    ]
  }
};

const COGNITIVE_TRAPS = [
  {
    id: 'mindreading',
    title: '01 / Mind-Reading & Hostile Attribution',
    trap: '"They didn’t reply to my message—they’re disrespecting me on purpose."',
    reality: 'In 85%+ of cases, silence or brevity is caused by the other person’s own overwhelm, distraction, or stress—not malice toward you.',
    reframe: 'DEFUSION REFRAME: "I notice I am telling myself a story about their intent. What are 3 benign explanations for their behavior?"'
  },
  {
    id: 'catastrophizing',
    title: '02 / Catastrophizing (Fortune-Telling)',
    trap: '"If this meeting goes badly, my career is ruined and I’ll never recover."',
    reality: 'The amygdala treats an uncertain future threat as an active physical predator, collapsing your time horizon to zero.',
    reframe: 'DEFUSION REFRAME: "What is the realistic worst-case outcome, how would I cope with it practically, and will this matter in 3 years?"'
  },
  {
    id: 'allornothing',
    title: '03 / All-or-Nothing (Binary Splitting)',
    trap: '"I lost my temper once today—I’m a failure and all my progress is wasted."',
    reality: 'Human change is statistical, not binary. Treating a slip as total defeat causes the "what-the-hell effect" where people abandon good habits.',
    reframe: 'DEFUSION REFRAME: "One miss is a data point, not an identity. Never miss twice in a row."'
  },
  {
    id: 'emotional',
    title: '04 / Emotional Reasoning',
    trap: '"I feel intense dread or guilt right now, so something terrible must be true."',
    reality: 'Feelings are real physiological weather patterns (often triggered by sleep debt, hunger, or old memories), not reliable courtroom evidence.',
    reframe: 'DEFUSION REFRAME: "My nervous system is sounding a loud alarm right now, but an alarm is not a fire. Let me check H.A.L.T. (Hungry, Angry, Lonely, Tired)."'
  }
];

export function initSection2(onComplete) {
  const modeTabs = document.querySelectorAll('[data-breath-mode]');
  const canvas = document.getElementById('breath-canvas');
  const audioToggleBtn = document.getElementById('breath-audio-btn');
  const cycleCountEl = document.getElementById('breath-cycles-val');
  const hrValEl = document.getElementById('breath-hr-val');
  const vagalValEl = document.getElementById('breath-vagal-val');
  const modeDescEl = document.getElementById('breath-mode-desc');

  // 90-second timer elements
  const timerStartBtn = document.getElementById('amygdala-timer-btn');
  const timerReadout = document.getElementById('amygdala-timer-val');
  const timerBar = document.getElementById('amygdala-timer-bar');
  const timerStatus = document.getElementById('amygdala-timer-status');

  // Cognitive trap elements
  const trapBtnsContainer = document.getElementById('trap-tabs-container');
  const trapDetailContainer = document.getElementById('trap-detail-container');

  let currentModeKey = 'sigh';
  let audioCuesEnabled = false;
  let completed = false;

  let phaseIndex = 0;
  let phaseElapsed = 0;
  let cyclesCompleted = 0;
  let simulatedHR = 86;
  const hrHistory = new Array(110).fill(86);
  let lastFrameTime = performance.now();

  // Render cognitive traps
  let activeTrapIdx = 0;
  function renderTraps() {
    if (!trapBtnsContainer || !trapDetailContainer) return;
    trapBtnsContainer.innerHTML = COGNITIVE_TRAPS.map((t, idx) => `
      <button class="tab-btn ${idx === activeTrapIdx ? 'active' : ''}" data-trap-idx="${idx}">
        ${t.title.split('/')[1].trim()}
      </button>
    `).join('');

    const t = COGNITIVE_TRAPS[activeTrapIdx];
    trapDetailContainer.innerHTML = `
      <div style="background: var(--bg-subtle); border: 1px solid var(--border-hairline); border-radius: var(--radius-sm); padding: 0.9rem;">
        <div style="font-family: var(--font-mono); font-size: 0.72rem; font-weight: 700; color: var(--accent-cobalt); margin-bottom: 0.35rem;">
          ${t.title}
        </div>
        <div style="font-family: var(--font-display); font-style: italic; font-size: 0.98rem; color: var(--status-danger); margin-bottom: 0.5rem;">
          Automatic Hijack: ${t.trap}
        </div>
        <p style="font-size: 0.83rem; color: var(--ink-secondary); margin-bottom: 0.65rem;">
          <strong>Neurobiology:</strong> ${t.reality}
        </p>
        <div style="background: var(--bg-elevated); border-left: 3px solid var(--accent-cobalt); padding: 0.55rem 0.75rem; font-size: 0.83rem; font-weight: 600;">
          ${t.reframe}
        </div>
      </div>
    `;

    trapBtnsContainer.querySelectorAll('[data-trap-idx]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeTrapIdx = parseInt(btn.getAttribute('data-trap-idx'), 10);
        sound.playClick(680);
        renderTraps();
        if (!completed) {
          completed = true;
          if (onComplete) onComplete(2);
        }
      });
    });
  }
  renderTraps();

  // 90-second chemical flush timer
  let flushTimerActive = false;
  let flushRemaining = 90;
  let flushInterval = null;

  if (timerStartBtn) {
    timerStartBtn.addEventListener('click', () => {
      sound.playClick(600);
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(2);
      }
      if (flushTimerActive) {
        clearInterval(flushInterval);
        flushTimerActive = false;
        flushRemaining = 90;
        timerStartBtn.textContent = 'Start 90s Chemical Wave Timer';
        timerReadout.textContent = '90s';
        timerBar.style.width = '100%';
        timerStatus.textContent = 'Ready: When triggered by anger or panic, observe the physical sensation for 90s without feeding the story.';
        return;
      }

      flushTimerActive = true;
      flushRemaining = 90;
      timerStartBtn.textContent = 'Reset 90s Timer';
      flushInterval = setInterval(() => {
        flushRemaining = Math.max(0, flushRemaining - 1);
        timerReadout.textContent = `${flushRemaining}s`;
        const pct = (flushRemaining / 90) * 100;
        timerBar.style.width = `${pct}%`;

        if (flushRemaining > 65) {
          timerStatus.textContent = 'PHASE 1 (90s–65s): Catecholamine Surge — Notice heart rate & heat in chest/face. Do not speak or type yet.';
        } else if (flushRemaining > 30) {
          timerStatus.textContent = 'PHASE 2 (65s–30s): Peak Bloodstream Wave — Breathe out slowly. Liver enzymes (COMT/MAO) are breaking down adrenaline.';
        } else if (flushRemaining > 0) {
          timerStatus.textContent = 'PHASE 3 (30s–0s): Autonomic Clearance — Prefrontal cortex bandwidth is returning. Wait for 0s.';
        } else {
          clearInterval(flushInterval);
          flushTimerActive = false;
          sound.playSuccessChord();
          timerStartBtn.textContent = 'Restart 90s Timer';
          timerStatus.textContent = 'WAVE CLEARED (0s) — The initial hormone surge has dissipated. You now have executive choice.';
        }
      }, 1000);
    });
  }

  modeTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      modeTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      currentModeKey = btn.getAttribute('data-breath-mode');
      phaseIndex = 0;
      phaseElapsed = 0;
      sound.playClick(540);
      if (modeDescEl) {
        modeDescEl.textContent = BREATH_MODES[currentModeKey].desc;
      }
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(2);
      }
    });
  });

  if (audioToggleBtn) {
    audioToggleBtn.addEventListener('click', () => {
      audioCuesEnabled = !audioCuesEnabled;
      audioToggleBtn.classList.toggle('active-toggle', audioCuesEnabled);
      audioToggleBtn.textContent = audioCuesEnabled ? 'Harmonic Breath Audio: ON' : 'Harmonic Breath Audio: OFF';
      if (audioCuesEnabled) {
        const currentPhase = BREATH_MODES[currentModeKey].phases[phaseIndex];
        sound.playBreathCue(currentPhase.id);
        if (!completed) {
          completed = true;
          if (onComplete) onComplete(2);
        }
      }
    });
  }

  const ctx = canvas.getContext('2d');
  let frameTick = 0;

  function animateBreath(now) {
    const dt = Math.min(0.1, (now - lastFrameTime) / 1000);
    lastFrameTime = now;
    frameTick++;

    const modeObj = BREATH_MODES[currentModeKey];
    const phase = modeObj.phases[phaseIndex];
    phaseElapsed += dt;

    if (phaseElapsed >= phase.duration) {
      phaseElapsed = 0;
      phaseIndex = (phaseIndex + 1) % modeObj.phases.length;
      if (phaseIndex === 0) {
        cyclesCompleted++;
        if (cycleCountEl) cycleCountEl.textContent = `${cyclesCompleted} cycles`;
        if (cyclesCompleted >= 1 && !completed) {
          completed = true;
          if (onComplete) onComplete(2);
        }
      }
      if (audioCuesEnabled) {
        sound.playBreathCue(modeObj.phases[phaseIndex].id);
      }
    }

    const activePhase = modeObj.phases[phaseIndex];
    const progress = Math.min(1, phaseElapsed / activePhase.duration);
    // Smooth cosine interpolation for lung volume
    const smoothT = 0.5 - 0.5 * Math.cos(progress * Math.PI);
    const lungVolume = activePhase.startVol + (activePhase.endVol - activePhase.startVol) * smoothT;

    // Simulate Respiratory Sinus Arrhythmia:
    // Inhale slightly increases HR; long exhale strongly activates vagal brake & reduces HR
    const baselineTarget = Math.max(62, 78 - Math.min(14, cyclesCompleted * 3));
    if (activePhase.id === 'inhale1' || activePhase.id === 'inhale2') {
      simulatedHR += ((baselineTarget + 8) - simulatedHR) * dt * 1.4;
    } else if (activePhase.id === 'exhale') {
      simulatedHR += ((baselineTarget - 9) - simulatedHR) * dt * 1.6;
    } else {
      simulatedHR += (baselineTarget - simulatedHR) * dt * 0.8;
    }

    if (frameTick % 3 === 0) {
      hrHistory.push(simulatedHR);
      if (hrHistory.length > 110) hrHistory.shift();
      if (hrValEl) hrValEl.textContent = `${Math.round(simulatedHR)} BPM`;
      if (vagalValEl) {
        vagalValEl.textContent = activePhase.id === 'exhale' ? 'HIGH (Vagus Active)' : 'MODERATE';
        vagalValEl.style.color = activePhase.id === 'exhale' ? '#34D399' : '#60A5FA';
      }
    }

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Subtle grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.04)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 28) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
    }
    for (let y = 0; y < h; y += 28) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    const splitX = Math.floor(w * 0.48);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
    ctx.beginPath();
    ctx.moveTo(splitX, 12);
    ctx.lineTo(splitX, h - 12);
    ctx.stroke();

    // --- LEFT: ALVEOLAR LUNG VOLUME PACER ---
    const cx = splitX * 0.5;
    const cy = h * 0.52;
    const minR = 26;
    const maxR = 76;
    const currentR = minR + lungVolume * (maxR - minR);

    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 11px monospace';
    ctx.fillText('ALVEOLAR EXPANSION PACER', 16, 24);

    // Outer target ring (100% alveolar recruitment)
    ctx.strokeStyle = 'rgba(96, 165, 250, 0.28)';
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    ctx.arc(cx, cy, maxR, 0, Math.PI * 2);
    ctx.stroke();
    ctx.setLineDash([]);

    // 12 surrounding alveolar lobes that bloom open especially during top-up inhale
    const numLobes = 12;
    for (let i = 0; i < numLobes; i++) {
      const angle = (i / numLobes) * Math.PI * 2 + now * 0.0003;
      const lx = cx + Math.cos(angle) * (currentR * 0.72);
      const ly = cy + Math.sin(angle) * (currentR * 0.72);
      const lobeR = 8 + lungVolume * 14;
      ctx.fillStyle = activePhase.id === 'exhale'
        ? 'rgba(52, 211, 153, 0.22)'
        : 'rgba(59, 130, 246, 0.26)';
      ctx.beginPath();
      ctx.arc(lx, ly, lobeR, 0, Math.PI * 2);
      ctx.fill();
    }

    // Core lung circle
    ctx.fillStyle = activePhase.id === 'exhale'
      ? 'rgba(16, 185, 129, 0.35)'
      : 'rgba(37, 99, 235, 0.42)';
    ctx.strokeStyle = activePhase.id === 'exhale' ? '#34D399' : '#60A5FA';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(cx, cy, currentR, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Volume % inside circle
    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 15px monospace';
    ctx.textAlign = 'center';
    ctx.fillText(`${Math.round(lungVolume * 100)}%`, cx, cy + 5);

    // Phase label & countdown at bottom of left pane
    ctx.fillStyle = activePhase.id === 'exhale' ? '#34D399' : '#93C5FD';
    ctx.font = 'bold 11px monospace';
    ctx.fillText(activePhase.label, cx, h - 16);
    ctx.textAlign = 'left';

    // --- RIGHT: VAGAL TONE & HEART RATE SINUS ARRHYTHMIA ---
    const gx = splitX + 18;
    const gw = w - gx - 16;
    const gTop = 46;
    const gBot = h - 32;
    const gH = gBot - gTop;

    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 11px monospace';
    ctx.fillText('HEART RATE & VAGUS NERVE RESPONSE (RSA)', gx, 24);

    // Draw HR curve (range 55 to 95 BPM)
    ctx.strokeStyle = activePhase.id === 'exhale' ? '#34D399' : '#60A5FA';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let i = 0; i < hrHistory.length; i++) {
      const px = gx + (i / (hrHistory.length - 1)) * gw;
      const norm = (hrHistory[i] - 55) / 42;
      const py = gBot - Math.max(0.05, Math.min(0.95, norm)) * gH;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // Explanatory annotation
    ctx.fillStyle = '#9BA3B0';
    ctx.font = '10px monospace';
    ctx.fillText(
      activePhase.id === 'exhale'
        ? '▼ EXHALE: Vagus nerve active → Heart rate slows'
        : '▲ INHALE: Alveoli expand to absorb O2 & offload CO2',
      gx,
      h - 14
    );

    requestAnimationFrame(animateBreath);
  }

  requestAnimationFrame(animateBreath);
}
