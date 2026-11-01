// ==========================================================================
// SCALE I: THE FIRST 4 MINUTES — Save a Body (CPR & Emergency Triage)
// ==========================================================================

import { sound } from './audio.js';

const PROTOCOLS = {
  cpr: {
    tag: 'PROTOCOL 01 / CARDIAC ARREST',
    title: 'Hands-Only CPR & AED Sequence',
    summary: 'Brain neurons begin irreversible hypoxic injury 4 minutes after cardiac arrest. Immediate chest compressions act as an external mechanical pump, maintaining coronary and cerebral perfusion until defibrillation.',
    steps: [
      {
        title: 'Check Responsiveness & Breathing (10 sec max)',
        desc: 'Shake shoulders firmly and shout. Look for normal breathing. Note: Occasional gasping or snorting ("agonal breathing") occurs in 40% of cardiac arrests—it is NOT normal breathing. Start CPR immediately.'
      },
      {
        title: 'Call Emergency Services & Send for an AED',
        desc: 'Point to a specific bystander: "You in the blue jacket, call 911/112 on speakerphone and bring the nearest AED." If alone, dial on speakerphone while kneeling beside the chest.'
      },
      {
        title: 'Push Hard & Fast at Center of Chest (100–120 BPM)',
        desc: 'Place the heel of one hand on the lower half of the sternum (between the nipples), other hand on top, fingers interlaced. Lock your elbows directly over the chest. Push 5–6 cm (2–2.4 in) deep.'
      },
      {
        title: 'Allow Full Chest Recoil & Minimize Pauses',
        desc: 'Let the chest rise completely between pushes so the heart refills with blood. Never pause compressions for more than 10 seconds—stopping drops cerebral perfusion pressure to zero.'
      }
    ],
    note: 'It takes 5 to 8 consecutive compressions just to build enough aortic pressure to perfuse the brain. Every unnecessary pause forces you to rebuild that pressure from zero.'
  },
  choking: {
    tag: 'PROTOCOL 02 / AIRWAY OBSTRUCTION',
    title: 'Severe Choking: The 5-and-5 Red Cross / ERC Protocol',
    summary: 'If a person can cough forcefully or speak, do not interfere—encourage coughing. If they cannot speak, cough, or breathe (universal clutch of the throat), act immediately:',
    steps: [
      {
        title: 'Deliver 5 Sharp Back Blows',
        desc: 'Stand slightly behind and to the side. Support their chest with one arm and bend them forward at the waist so gravity assists. Strike firmly 5 times between the shoulder blades with the heel of your hand.'
      },
      {
        title: 'Deliver 5 Abdominal Thrusts (Heimlich Maneuver)',
        desc: 'Stand behind them, wrap arms around waist. Make a fist and place the thumb side against the middle of the abdomen—just ABOVE the navel and well BELOW the tip of the breastbone (xiphoid process).'
      },
      {
        title: 'Grasp Fist & Pull Inward and Upward',
        desc: 'Press sharply inward and upward 5 times as if trying to lift the person slightly, forcing residual air from the lungs like a piston to expel the obstruction.'
      },
      {
        title: 'Alternate 5 Back Blows & 5 Thrusts (Special Cases)',
        desc: 'Pregnant or unable to reach around abdomen: Perform chest thrusts at center of sternum. Infant (<1 yr): 5 back slaps face-down along forearm + 5 two-finger chest thrusts. Alone: Thrust abdomen over the back of a sturdy chair.'
      }
    ],
    note: 'CRITICAL LANDMARK: Never press directly on the sharp lower tip of the sternum (xiphoid process). Place your fist strictly in the soft midline above the belly button.'
  },
  stroke: {
    tag: 'PROTOCOL 03 / ACUTE ISCHEMIC OR HEMORRHAGIC STROKE',
    title: 'B.E.F.A.S.T. Recognition & Time-Window Protocol',
    summary: 'During a typical large-vessel ischemic stroke, 1.9 million neurons die every single minute. Clot-busting therapy (tPA/tenecteplase) and mechanical thrombectomy depend on the exact minute symptoms began.',
    steps: [
      {
        title: 'B — Balance & E — Eyes',
        desc: 'Did the person experience a sudden loss of balance, coordination, or dizziness? Did they experience sudden blurred, double, or lost vision in one or both eyes?'
      },
      {
        title: 'F — Face Drooping (Smile Test)',
        desc: 'Ask the person to smile or show their teeth. Does one side of the face droop or remain flat? (Note: Stroke spares the forehead; paralysis of the entire side including forehead may indicate Bell’s palsy, but treat as emergency).'
      },
      {
        title: 'A — Arm Weakness (10-Second Drift Test)',
        desc: 'Ask them to close their eyes and hold both arms straight out in front with palms up for 10 seconds. Does one arm drift downward or pronate (palm turns inward)?'
      },
      {
        title: 'S — Speech Difficulty & T — Time Stamp',
        desc: 'Ask them to repeat a simple phrase ("The sky is blue in Cincinnati"). Is speech slurred, garbled, or unable to find words? Call emergency services immediately and write down the EXACT "Last Known Well" time.'
      }
    ],
    note: 'DO NOT GIVE ASPIRIN: Unlike a heart attack, ~15% of strokes are hemorrhagic (brain bleed). Giving aspirin before a hospital CT scan can fatally worsen a hemorrhagic stroke. Give nothing by mouth.'
  },
  bleeding: {
    tag: 'PROTOCOL 04 / LIFE-THREATENING HEMORRHAGE',
    title: 'Stop the Bleed: Direct Pressure, Packing & Tourniquet',
    summary: 'A person can bleed to death from a severed femoral or brachial artery in 3 to 5 minutes—faster than many ambulances can arrive. You are the first responder.',
    steps: [
      {
        title: 'Identify Life-Threatening Bleeding',
        desc: 'Look for bright red blood spurting with the heartbeat, blood pooling rapidly on the ground, clothing soaked through with blood, or a traumatic amputation.'
      },
      {
        title: 'Apply Firm, Continuous Direct Pressure (Don’t Peek!)',
        desc: 'Cover the wound with clean gauze or cloth and push down hard with both hands directly on the bleeding source. Hold uninterrupted pressure for at least 3–5 full minutes. Peeking breaks forming platelet clots.'
      },
      {
        title: 'If Cloth Soaks Through, Add More On Top',
        desc: 'Never remove the bottom layer of gauze—doing so rips away clotting factors. Stack fresh cloth on top and press harder. For deep junctional wounds (groin/armpit/neck), pack gauze tightly into the wound cavity.'
      },
      {
        title: 'Limb Arterial Bleed: Apply Tourniquet High & Tight',
        desc: 'For life-threatening arm or leg bleeding, place a commercial tourniquet 5–8 cm (2–3 inches) above the wound (never directly over a joint). Twist windlass until bleeding stops completely, lock it, and write the time ("TK 14:22") on the strap.'
      }
    ],
    note: 'MYTH BUSTED: Modern trauma data shows tourniquets left on for under 2 hours almost never cause limb loss, while hesitation to tighten a tourniquet costs lives. A working tourniquet hurts—do not loosen it.'
  }
};

export function initSection1(onComplete) {
  const protocolTabs = document.querySelectorAll('[data-protocol-tab]');
  const protocolContainer = document.getElementById('protocol-content-area');
  const canvas = document.getElementById('cpr-canvas');
  const compressBtn = document.getElementById('cpr-compress-btn');
  const guideBtn = document.getElementById('cpr-guide-btn');
  const metronomeBtn = document.getElementById('cpr-metronome-btn');

  const bpmReadout = document.getElementById('cpr-bpm-val');
  const perfusionReadout = document.getElementById('cpr-perfusion-val');
  const countReadout = document.getElementById('cpr-count-val');
  const feedbackBanner = document.getElementById('cpr-feedback-banner');

  let activeProtocol = 'cpr';
  let mode = 'guide'; // 'guide' (auto 110 BPM demo) or 'practice' (user tapping)
  let audioMetronome = false;
  let completed = false;

  // Simulation state
  let tapTimestamps = [];
  let currentBpm = 110;
  let perfusion = 78; // 0 to 100%
  let compressionDepth = 0; // 0 to 6.0 cm animated
  let goodCompressionsCount = 0;
  let lastCompressionTime = performance.now();
  let lastGuideBeatTime = performance.now();
  const historyPoints = new Array(120).fill(75);

  function renderProtocol(key) {
    const p = PROTOCOLS[key];
    if (!p || !protocolContainer) return;
    protocolContainer.innerHTML = `
      <div style="margin-bottom: 0.75rem;">
        <span class="speaker-tag" style="color: var(--accent-rescue); font-weight: 700;">${p.tag}</span>
        <h3 style="font-size: 1.15rem; font-weight: 700; margin-bottom: 0.35rem;">${p.title}</h3>
        <p style="font-size: 0.86rem; color: var(--ink-secondary);">${p.summary}</p>
      </div>
      <div class="protocol-steps">
        ${p.steps.map((s, i) => `
          <div class="protocol-step">
            <div class="step-num">${i + 1}</div>
            <div class="step-body">
              <h4>${s.title}</h4>
              <p>${s.desc}</p>
            </div>
          </div>
        `).join('')}
      </div>
      <div class="clinical-note">
        <strong>FIELD RULE:</strong> ${p.note}
      </div>
    `;
  }

  protocolTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      protocolTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeProtocol = btn.getAttribute('data-protocol-tab');
      sound.playClick(620);
      renderProtocol(activeProtocol);
    });
  });

  renderProtocol('cpr');

  function triggerCompression(isUserAction = false) {
    const now = performance.now();
    lastCompressionTime = now;
    compressionDepth = 5.6;

    if (isUserAction) {
      if (mode !== 'practice') {
        mode = 'practice';
        guideBtn.classList.remove('active-toggle');
        guideBtn.textContent = 'Auto-Demo: OFF (Hands-On Mode)';
      }

      tapTimestamps.push(now);
      if (tapTimestamps.length > 6) tapTimestamps.shift();

      if (tapTimestamps.length >= 2) {
        const intervals = [];
        for (let i = 1; i < tapTimestamps.length; i++) {
          intervals.push(tapTimestamps[i] - tapTimestamps[i - 1]);
        }
        const avgMs = intervals.reduce((a, b) => a + b, 0) / intervals.length;
        currentBpm = Math.round(60000 / Math.max(220, Math.min(2000, avgMs)));
      } else {
        currentBpm = 108;
      }

      const inTarget = currentBpm >= 100 && currentBpm <= 120;
      sound.playCprBeat(inTarget, false);

      if (inTarget) {
        perfusion = Math.min(98, perfusion + 8.5);
        goodCompressionsCount++;
        feedbackBanner.textContent = `EXCELLENT CADENCE (${currentBpm} BPM) — Maintaining optimal cerebral perfusion (5.5 cm depth)`;
        feedbackBanner.style.color = '#34D399';
      } else if (currentBpm < 100) {
        perfusion = Math.min(72, perfusion + 4.0);
        feedbackBanner.textContent = `TOO SLOW (${currentBpm} BPM) — Speed up slightly to 100–120 BPM ("Stayin' Alive" tempo)`;
        feedbackBanner.style.color = '#FBBF24';
      } else {
        perfusion = Math.min(75, perfusion + 3.5);
        feedbackBanner.textContent = `TOO FAST (${currentBpm} BPM) — Slow slightly so the heart chambers have time to refill`;
        feedbackBanner.style.color = '#F87171';
      }

      if (goodCompressionsCount >= 8 && !completed) {
        completed = true;
        sound.playSuccessChord();
        if (onComplete) onComplete(1);
      }
    } else {
      // Auto-guide beat at 110 BPM (every 545.45 ms)
      currentBpm = 110;
      perfusion = Math.min(92, perfusion + 7.5);
      if (audioMetronome) {
        sound.playCprBeat(true, true);
      }
    }

    updateTelemetryDOM();
  }

  function updateTelemetryDOM() {
    if (!bpmReadout) return;
    bpmReadout.textContent = `${currentBpm} BPM`;
    bpmReadout.style.color = (currentBpm >= 100 && currentBpm <= 120) ? '#34D399' : '#FBBF24';
    perfusionReadout.textContent = `${Math.round(perfusion)}%`;
    perfusionReadout.style.color = perfusion >= 60 ? '#34D399' : '#F87171';
    countReadout.textContent = mode === 'practice'
      ? `${goodCompressionsCount} good ${goodCompressionsCount === 1 ? 'push' : 'pushes'}`
      : '110 BPM Guide';
  }

  if (compressBtn) {
    compressBtn.addEventListener('pointerdown', (e) => {
      e.preventDefault();
      triggerCompression(true);
    });
  }

  // Allow spacebar when Scale 1 is visible and user is not typing in an input
  window.addEventListener('keydown', (e) => {
    if (e.code === 'Space' && !['INPUT', 'TEXTAREA', 'SELECT', 'BUTTON'].includes(document.activeElement?.tagName)) {
      const rect = canvas.getBoundingClientRect();
      if (rect.top < window.innerHeight * 0.85 && rect.bottom > 100) {
        e.preventDefault();
        triggerCompression(true);
      }
    }
  });

  if (guideBtn) {
    guideBtn.addEventListener('click', () => {
      if (mode === 'guide') {
        mode = 'practice';
        currentBpm = 0;
        tapTimestamps = [];
        guideBtn.classList.remove('active-toggle');
        guideBtn.textContent = 'Auto-Demo: OFF (Tap Pad)';
        feedbackBanner.textContent = 'HANDS-ON DRILL: Tap "PUSH CHEST" or press SPACEBAR at 100–120 BPM. Watch perfusion drop if you pause!';
        feedbackBanner.style.color = '#FBBF24';
      } else {
        mode = 'guide';
        guideBtn.classList.add('active-toggle');
        guideBtn.textContent = 'Auto-Demo: ON (110 BPM)';
        feedbackBanner.textContent = '110 BPM GUIDE ACTIVE — Notice how steady compressions keep brain perfusion above the 60% survival line.';
        feedbackBanner.style.color = '#34D399';
      }
      sound.playClick(580);
    });
  }

  if (metronomeBtn) {
    metronomeBtn.addEventListener('click', () => {
      audioMetronome = !audioMetronome;
      metronomeBtn.classList.toggle('active-toggle', audioMetronome);
      metronomeBtn.textContent = audioMetronome ? '110 BPM Audio Click: ON' : '110 BPM Audio Click: OFF';
      if (audioMetronome) {
        mode = 'guide';
        guideBtn.classList.add('active-toggle');
        guideBtn.textContent = 'Auto-Demo: ON (110 BPM)';
        sound.playCprBeat(true, true);
        if (!completed) {
          completed = true;
          if (onComplete) onComplete(1);
        }
      }
    });
  }

  // Canvas animation loop
  const ctx = canvas.getContext('2d');
  let frameCount = 0;

  function renderCanvas(now) {
    frameCount++;

    // In guide mode, trigger 110 BPM (545.45ms per beat)
    if (mode === 'guide' && now - lastGuideBeatTime >= 545.45) {
      lastGuideBeatTime = now;
      triggerCompression(false);
    }

    // Natural recoil of chest
    compressionDepth *= 0.84;
    if (compressionDepth < 0.05) compressionDepth = 0;

    // Decay perfusion if no compressions happen
    const timeSinceLast = now - lastCompressionTime;
    if (timeSinceLast > 750) {
      // Rapid decay when compressions stop!
      perfusion = Math.max(0, perfusion - 0.42);
      if (timeSinceLast > 2200 && mode === 'practice') {
        currentBpm = 0;
        feedbackBanner.textContent = 'WARNING: Compressions paused! Cerebral Perfusion Pressure is collapsing toward 0%. Push now!';
        feedbackBanner.style.color = '#F87171';
      }
      updateTelemetryDOM();
    } else {
      perfusion = Math.max(0, perfusion - 0.08);
    }

    if (frameCount % 2 === 0) {
      historyPoints.push(perfusion + compressionDepth * 1.8);
      if (historyPoints.length > 120) historyPoints.shift();
    }

    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Subtle dark clinical grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let x = 0; x < w; x += 28) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += 28) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Divider between Anatomy View (left) and Perfusion Waveform (right)
    const splitX = Math.floor(w * 0.46);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.14)';
    ctx.beginPath();
    ctx.moveTo(splitX, 12);
    ctx.lineTo(splitX, h - 12);
    ctx.stroke();

    // --- LEFT SIDE: THORACIC CROSS-SECTION & STERNUM DEPTH ---
    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 11px monospace';
    ctx.fillText('THORACIC MECHANICS (5–6 CM DEPTH)', 16, 24);

    const centerX = splitX * 0.48;
    const baseChestY = 82;
    const spineY = 205;
    const pressPx = (compressionDepth / 6.0) * 34; // max ~34px downward displacement
    const currentSternumY = baseChestY + pressPx;

    // Spine / Backboard
    ctx.fillStyle = '#2A3342';
    ctx.fillRect(centerX - 85, spineY, 170, 14);
    ctx.fillStyle = '#6C7686';
    ctx.font = '10px monospace';
    ctx.fillText('SPINE / FIRM SURFACE', centerX - 58, spineY + 26);

    // Ribcage arch (deforms dynamically with compressionDepth)
    ctx.strokeStyle = '#64748B';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.ellipse(centerX, (currentSternumY + spineY) / 2, 76 + pressPx * 0.35, (spineY - currentSternumY) / 2, 0, 0, Math.PI * 2);
    ctx.stroke();

    // Heart chamber between sternum and spine
    const heartCenterY = (currentSternumY + spineY) / 2 + 4;
    const heartRadiusY = Math.max(16, 34 - pressPx * 0.48);
    const heartRadiusX = 28 + pressPx * 0.35;

    // Oxygenated blood pulse aura when compressed
    if (compressionDepth > 1.2) {
      ctx.fillStyle = `rgba(239, 68, 68, ${Math.min(0.45, compressionDepth / 10)})`;
      ctx.beginPath();
      ctx.ellipse(centerX, heartCenterY, heartRadiusX + 14, heartRadiusY + 10, 0, 0, Math.PI * 2);
      ctx.fill();
    }

    ctx.fillStyle = '#EF4444';
    ctx.beginPath();
    ctx.ellipse(centerX, heartCenterY, heartRadiusX, heartRadiusY, 0, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#FFF';
    ctx.font = 'bold 10px monospace';
    ctx.fillText('HEART', centerX - 16, heartCenterY + 3);

    // Sternum plate & Hands pushing down
    ctx.fillStyle = '#F8FAFC';
    ctx.fillRect(centerX - 36, currentSternumY - 6, 72, 8);

    // Force arrow downward
    ctx.strokeStyle = compressionDepth > 2 ? '#34D399' : '#F05238';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(centerX, 38);
    ctx.lineTo(centerX, currentSternumY - 12);
    ctx.stroke();
    ctx.fillStyle = compressionDepth > 2 ? '#34D399' : '#F05238';
    ctx.beginPath();
    ctx.moveTo(centerX - 7, currentSternumY - 18);
    ctx.lineTo(centerX + 7, currentSternumY - 18);
    ctx.lineTo(centerX, currentSternumY - 8);
    ctx.closePath();
    ctx.fill();

    // Depth gauge ruler on right of thorax
    const rulerX = splitX - 38;
    ctx.strokeStyle = 'rgba(255,255,255,0.25)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(rulerX, baseChestY);
    ctx.lineTo(rulerX, baseChestY + 40);
    ctx.stroke();

    // Target 5-6cm zone highlight
    ctx.fillStyle = 'rgba(52, 211, 153, 0.25)';
    ctx.fillRect(rulerX - 6, baseChestY + 26, 12, 12);
    ctx.fillStyle = '#34D399';
    ctx.font = '10px monospace';
    ctx.fillText('5-6cm', rulerX - 18, baseChestY + 52);

    // --- RIGHT SIDE: CEREBRAL PERFUSION PRESSURE WAVEFORM ---
    const graphX = splitX + 18;
    const graphW = w - graphX - 16;
    const graphTop = 42;
    const graphBottom = h - 28;
    const graphH = graphBottom - graphTop;

    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 11px monospace';
    ctx.fillText('CEREBRAL PERFUSION PRESSURE (BRAIN O2 FLOW)', graphX, 24);

    // Survival threshold zone (>60% CPP)
    const thresholdY = graphBottom - 0.6 * graphH;
    ctx.fillStyle = 'rgba(52, 211, 153, 0.08)';
    ctx.fillRect(graphX, graphTop, graphW, thresholdY - graphTop);

    ctx.strokeStyle = 'rgba(52, 211, 153, 0.5)';
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(graphX, thresholdY);
    ctx.lineTo(graphX + graphW, thresholdY);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = '#34D399';
    ctx.font = '10px monospace';
    ctx.fillText('MIN SURVIVAL PERFUSION (60%)', graphX + 6, thresholdY - 5);

    // Draw perfusion history line
    ctx.strokeStyle = perfusion >= 60 ? '#34D399' : '#F87171';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let i = 0; i < historyPoints.length; i++) {
      const px = graphX + (i / (historyPoints.length - 1)) * graphW;
      const clamped = Math.max(0, Math.min(100, historyPoints[i]));
      const py = graphBottom - (clamped / 100) * graphH;
      if (i === 0) ctx.moveTo(px, py);
      else ctx.lineTo(px, py);
    }
    ctx.stroke();

    // Fill under curve
    ctx.lineTo(graphX + graphW, graphBottom);
    ctx.lineTo(graphX, graphBottom);
    ctx.closePath();
    ctx.fillStyle = perfusion >= 60 ? 'rgba(52, 211, 153, 0.14)' : 'rgba(248, 113, 113, 0.14)';
    ctx.fill();

    requestAnimationFrame(renderCanvas);
  }

  requestAnimationFrame(renderCanvas);
}
