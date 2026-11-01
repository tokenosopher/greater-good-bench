// ==========================================================================
// SCALE III: THE 5-MINUTE BRIDGE — De-escalate Conflict & Build Trust
// ==========================================================================

import { sound } from './audio.js';

const SCENARIOS = [
  {
    id: 'partner',
    tabLabel: '01 / Partner & Home',
    speaker: 'EXHAUSTED PARTNER OR HOUSEMATE',
    quote: '"You never help around here unless I beg! You said you’d handle dinner by 6:00 and I’m still the one cleaning up."',
    options: [
      {
        type: 'attack',
        tag: 'REACTIVE INSTINCT A: COUNTER-ATTACK ("ALWAYS/NEVER" TRAP)',
        color: '#EF4444',
        text: '"Oh, I never help? Who spent three hours fixing the sink on Sunday while you were on the couch?"',
        cortisol: 94,
        bandwidth: 8,
        outcome: 'ESCALATION SPIRAL: Matching an "always/never" generalization with a counter-accusation triggers mutual amygdala threat. Neither person hears the other; the argument shifts to historical score-keeping.'
      },
      {
        type: 'defend',
        tag: 'REACTIVE INSTINCT B: DEFENSIVE EXCUSE / MINIMIZING',
        color: '#F59E0B',
        text: '"Calm down, you’re overreacting. My meeting ran 20 minutes late—it’s not a big deal."',
        cortisol: 78,
        bandwidth: 22,
        outcome: 'INVALIDATION LOCK: Telling an overwhelmed person to "calm down" or that their stress "isn’t a big deal" signals that their exhaustion is invisible to you, intensifying resentment.'
      },
      {
        type: 'repair',
        tag: 'HIGH-LEVERAGE REPAIR: VALIDATE NEED + CONCRETE ACTION (NVC)',
        color: '#10B981',
        text: '"You’re right that I missed the 6:00 handoff and didn’t text. You’re exhausted and needed to count on me tonight. Sit down for 20 minutes—I’m taking over the kitchen right now."',
        cortisol: 18,
        bandwidth: 92,
        outcome: 'DE-ESCALATION ACHIEVED: By separating the exaggeration ("never") from the real unmet need (reliability & rest) and offering an immediate concrete repair, threat drops rapidly and trust is restored.'
      }
    ]
  },
  {
    id: 'work',
    tabLabel: '02 / Workplace Blame',
    speaker: 'STRESSED COLLEAGUE OR MANAGER',
    quote: '"Your update broke the staging report 15 minutes before the client review. Did you even test this before pushing?"',
    options: [
      {
        type: 'attack',
        tag: 'REACTIVE INSTINCT A: SHIFT BLAME PUBLICLY',
        color: '#EF4444',
        text: '"The only reason I rushed it is because you changed the requirements at 4 PM yesterday without documentation!"',
        cortisol: 89,
        bandwidth: 14,
        outcome: 'STATUS THREAT: Public counter-blame turns a technical bug into a territorial status fight. The client problem remains unsolved while psychological safety plummets.'
      },
      {
        type: 'defend',
        tag: 'REACTIVE INSTINCT B: WITHDRAWAL / OVER-APOLOGIZING',
        color: '#F59E0B',
        text: '"I guess I’m just terrible at this. Fine, roll everything back, I won’t touch the report again."',
        cortisol: 74,
        bandwidth: 25,
        outcome: 'PASSIVE-AGGRESSIVE FREEZE: Making the crisis about your personal worth forces the team to manage your emotions instead of solving the 15-minute deadline.'
      },
      {
        type: 'repair',
        tag: 'HIGH-LEVERAGE REPAIR: JOINT FOCUS ON FIX + PROCESS LATER',
        color: '#10B981',
        text: '"I see the broken chart—that’s stressful right before the call. Let’s revert to the 10 AM snapshot right now so your demo is rock-solid (takes 90 seconds), then I’ll add an automated check so this can’t recur."',
        cortisol: 21,
        bandwidth: 94,
        outcome: 'SHARED AGENCY: Moving physically and linguistically from "Me vs. You" to "Us vs. The Problem" immediately lowers adrenaline and demonstrates high competence.'
      }
    ]
  },
  {
    id: 'civic',
    tabLabel: '03 / Polarized Belief',
    speaker: 'NEIGHBOR OR RELATIVE AT DINNER',
    quote: '"Anyone who supports that policy is either brainwashed or actively trying to ruin this community."',
    options: [
      {
        type: 'attack',
        tag: 'REACTIVE INSTINCT A: MORAL CONDEMNATION & FACT-DUMP',
        color: '#EF4444',
        text: '"That’s completely ignorant. Every actual economist says the exact opposite of what you just read on social media."',
        cortisol: 96,
        bandwidth: 5,
        outcome: 'BACKFIRE EFFECT: Neuroimaging shows that attacking a core identity belief activates the same insular cortex regions as physical threat. They double down to protect dignity.'
      },
      {
        type: 'defend',
        tag: 'REACTIVE INSTINCT B: SARCASTIC DISMISSAL',
        color: '#F59E0B',
        text: '"Sure, whatever you say. Let’s just not talk about anything real."',
        cortisol: 65,
        bandwidth: 19,
        outcome: 'SILENT POLARIZATION: Contemptuous withdrawal preserves surface quiet for 5 minutes while cementing mutual dehumanization.'
      },
      {
        type: 'repair',
        tag: 'HIGH-LEVERAGE REPAIR: STEELMAN + CURIOUS CALIBRATED QUESTION',
        color: '#10B981',
        text: '"It sounds like you’re really worried about local families getting priced out—I care a lot about that too. What personal experience made you feel this policy would hurt rather than help?"',
        cortisol: 24,
        bandwidth: 88,
        outcome: 'STREET EPISTEMOLOGY / BRIDGE: Naming the shared underlying moral value (protecting local families) and asking for lived experience instead of trading slogans unlocks genuine dialogue.'
      }
    ]
  }
];

export function initSection3(onComplete) {
  const scenarioTabs = document.querySelectorAll('[data-scenario-tab]');
  const speakerEl = document.getElementById('conflict-speaker');
  const quoteEl = document.getElementById('conflict-quote');
  const optionsContainer = document.getElementById('conflict-options');
  const cortisolVal = document.getElementById('cortisol-val');
  const cortisolBar = document.getElementById('cortisol-bar');
  const bandwidthVal = document.getElementById('bandwidth-val');
  const bandwidthBar = document.getElementById('bandwidth-bar');
  const outcomeBox = document.getElementById('conflict-outcome-box');

  // Game Theory controls
  const noiseSlider = document.getElementById('trust-noise-slider');
  const noiseValEl = document.getElementById('trust-noise-val');
  const strategyTabs = document.querySelectorAll('[data-trust-strategy]');
  const runSimBtn = document.getElementById('trust-sim-btn');
  const canvas = document.getElementById('trust-canvas');
  const trustSummaryEl = document.getElementById('trust-summary-text');

  let activeScenarioIdx = 0;
  let activeOptionIdx = 2; // Show the repair contrast or let user click
  let completed = false;

  function renderScenario() {
    const sc = SCENARIOS[activeScenarioIdx];
    if (!sc || !quoteEl) return;
    speakerEl.textContent = sc.speaker;
    quoteEl.textContent = sc.quote;

    optionsContainer.innerHTML = sc.options.map((opt, idx) => `
      <button class="response-option-btn ${idx === activeOptionIdx ? 'selected' : ''}" data-opt-idx="${idx}">
        <span class="response-strategy-tag" style="color: ${opt.color};">${opt.tag}</span>
        <span class="response-text">${opt.text}</span>
      </button>
    `).join('');

    const chosen = sc.options[activeOptionIdx];
    cortisolVal.textContent = `${chosen.cortisol}%`;
    cortisolBar.style.width = `${chosen.cortisol}%`;
    cortisolBar.style.backgroundColor = chosen.cortisol > 50 ? '#EF4444' : '#10B981';

    bandwidthVal.textContent = `${chosen.bandwidth}%`;
    bandwidthBar.style.width = `${chosen.bandwidth}%`;
    bandwidthBar.style.backgroundColor = chosen.bandwidth > 60 ? '#10B981' : '#F59E0B';

    outcomeBox.innerHTML = `<strong>NEUROBIOLOGICAL OUTCOME:</strong> ${chosen.outcome}`;

    optionsContainer.querySelectorAll('[data-opt-idx]').forEach(btn => {
      btn.addEventListener('click', () => {
        activeOptionIdx = parseInt(btn.getAttribute('data-opt-idx'), 10);
        sound.playClick(activeOptionIdx === 2 ? 760 : 420);
        renderScenario();
        if (!completed) {
          completed = true;
          if (onComplete) onComplete(3);
        }
      });
    });
  }

  scenarioTabs.forEach((btn, idx) => {
    btn.addEventListener('click', () => {
      scenarioTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeScenarioIdx = idx;
      activeOptionIdx = 0; // Start on reactive instinct so user can feel the shift to Repair!
      sound.playClick(600);
      renderScenario();
    });
  });

  renderScenario();

  // --- PART B: GAME THEORY OF NOISY TRUST ---
  let noiseRate = 0.10; // 10% misunderstanding rate
  let selectedStrategy = 'generous'; // 'tft' | 'generous' | 'grudger' | 'always_coop'
  let simRounds = [];
  let tournamentScores = { generous: 88, tft: 54, always_coop: 68, grudger: 32 };

  // Deterministic pseudo-random with seed shift so user can re-run and see realistic sequences
  let simSeed = 42;
  function nextRand() {
    simSeed = (simSeed * 1664525 + 1013904223) % 4294967296;
    return simSeed / 4294967296;
  }

  function simulatePair(strategyType, noise, roundsCount = 28) {
    const history = [];
    let aMove = 'C';
    let bMove = 'C';
    let aGrudge = false;
    let bGrudge = false;
    let coopCount = 0;

    for (let r = 0; r < roundsCount; r++) {
      // Actual intent
      const intentA = aMove;
      const intentB = bMove;

      // Noise may corrupt how intent is perceived by the partner!
      // Make sure at least one noise event occurs around round 4 if noise > 0 so visual is educational
      const forceNoise = (noise > 0 && r === 4);
      const perceivedByB = (forceNoise || (r > 1 && nextRand() < noise)) ? (intentA === 'C' ? 'D' : 'C') : intentA;
      const perceivedByA = (r > 1 && nextRand() < noise * 0.6) ? (intentB === 'C' ? 'D' : 'C') : intentB;

      const hadNoise = (perceivedByB !== intentA) || (perceivedByA !== intentB);
      if (intentA === 'C' && intentB === 'C') coopCount++;

      history.push({
        round: r + 1,
        intentA,
        intentB,
        perceivedByB,
        perceivedByA,
        hadNoise
      });

      // Next move logic
      if (strategyType === 'tft') {
        // Strict Tit-for-Tat copies whatever it perceived the partner did last
        aMove = perceivedByA;
        bMove = perceivedByB;
      } else if (strategyType === 'generous') {
        // Generous Tit-for-Tat + Explicit Repair:
        // Forgives isolated noise/defection ~65% of the time and repairs immediately
        aMove = perceivedByA === 'D' ? (nextRand() < 0.68 ? 'C' : 'D') : 'C';
        bMove = perceivedByB === 'D' ? (nextRand() < 0.68 ? 'C' : 'D') : 'C';
      } else if (strategyType === 'grudger') {
        if (perceivedByA === 'D') aGrudge = true;
        if (perceivedByB === 'D') bGrudge = true;
        aMove = aGrudge ? 'D' : 'C';
        bMove = bGrudge ? 'D' : 'C';
      } else {
        // Always cooperate (vulnerable to exploiters, though fine with self)
        aMove = 'C';
        bMove = (r % 5 === 3) ? 'D' : 'C'; // Show occasional exploitation if doormat
      }
    }
    return { history, coopRate: Math.round((coopCount / roundsCount) * 100) };
  }

  function runSimulation() {
    const res = simulatePair(selectedStrategy, noiseRate, 28);
    simRounds = res.history;

    // Calculate expected tournament cooperation stability across all 4 strategies at current noise
    const n = noiseRate;
    tournamentScores = {
      generous: Math.round(Math.max(58, 98 - n * 95)),
      tft: Math.round(Math.max(18, 99 - n * 310)),
      always_coop: Math.round(Math.max(40, 74 - n * 40)),
      grudger: Math.round(Math.max(8, 96 - n * 420))
    };

    if (trustSummaryEl) {
      if (selectedStrategy === 'tft' && noiseRate >= 0.05) {
        trustSummaryEl.innerHTML = `<strong style="color: #F87171;">VENDETTA TRAP (${res.coopRate}% Mutual Trust):</strong> At ${Math.round(noiseRate * 100)}% misunderstanding noise, Strict Tit-for-Tat locks two decent people into an endless cycle of retaliation after a single misread action (Round 5).`;
      } else if (selectedStrategy === 'generous') {
        trustSummaryEl.innerHTML = `<strong style="color: #34D399;">RESILIENT COOPERATION (${res.coopRate}% Mutual Trust):</strong> Even with ${Math.round(noiseRate * 100)}% noise, Generous Tit-for-Tat absorbs accidental misunderstandings without becoming a doormat—keeping human cooperation alive.`;
      } else if (selectedStrategy === 'grudger') {
        trustSummaryEl.innerHTML = `<strong style="color: #F87171;">PERMANENT RUPTURE (${res.coopRate}% Mutual Trust):</strong> "One strike and you’re dead to me" destroys every relationship as soon as noise > 0%.`;
      } else {
        trustSummaryEl.innerHTML = `<strong style="color: #FBBF24;">UNBOUNDED PERMISSIVENESS:</strong> Forgiving everything without boundaries works with saints, but invites exploitation by bad-faith actors.`;
      }
    }

    drawTrustCanvas();
  }

  function drawTrustCanvas() {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // Top half: 28-Round Interaction Timeline (Person A & Person B)
    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 11px monospace';
    ctx.fillText(`28-ROUND RELATIONSHIP TIMELINE (NOISE: ${Math.round(noiseRate * 100)}%)`, 16, 22);

    const startX = 76;
    const availW = w - startX - 18;
    const cellW = availW / simRounds.length;

    ctx.fillStyle = '#CBD5E1';
    ctx.font = '10px monospace';
    ctx.fillText('PERSON A', 14, 52);
    ctx.fillText('PERSON B', 14, 84);

    simRounds.forEach((r, idx) => {
      const x = startX + idx * cellW;
      // Person A move box
      ctx.fillStyle = r.intentA === 'C' ? '#10B981' : '#EF4444';
      ctx.fillRect(x + 1, 38, cellW - 3, 20);

      // Person B move box
      ctx.fillStyle = r.intentB === 'C' ? '#10B981' : '#EF4444';
      ctx.fillRect(x + 1, 70, cellW - 3, 20);

      // Highlight noise lightning bolt / marker if misread occurred
      if (r.hadNoise) {
        ctx.fillStyle = '#FBBF24';
        ctx.beginPath();
        ctx.arc(x + cellW / 2, 31, 3.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    // Legend for timeline
    ctx.fillStyle = '#10B981';
    ctx.fillRect(startX, 100, 10, 8);
    ctx.fillStyle = '#9BA3B0';
    ctx.font = '10px monospace';
    ctx.fillText('Cooperate', startX + 14, 108);

    ctx.fillStyle = '#EF4444';
    ctx.fillRect(startX + 86, 100, 10, 8);
    ctx.fillStyle = '#9BA3B0';
    ctx.fillText('Retaliate / Defect', startX + 100, 108);

    ctx.fillStyle = '#FBBF24';
    ctx.beginPath();
    ctx.arc(startX + 230, 104, 3.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#9BA3B0';
    ctx.fillText('Misread Intent (Noise)', startX + 238, 108);

    // Divider line
    ctx.strokeStyle = 'rgba(255,255,255,0.12)';
    ctx.beginPath();
    ctx.moveTo(14, 122);
    ctx.lineTo(w - 14, 122);
    ctx.stroke();

    // Bottom half: Strategy Survival & Trust Comparison Bars
    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 11px monospace';
    ctx.fillText('LONG-TERM TRUST SURVIVAL BY STRATEGY AT CURRENT NOISE LEVEL', 16, 142);

    const bars = [
      { key: 'generous', label: 'Generous Tit-for-Tat (Forgive 1st Noise)', score: tournamentScores.generous, color: '#34D399' },
      { key: 'tft',      label: 'Strict Tit-for-Tat (Immediate Retaliation)', score: tournamentScores.tft, color: '#60A5FA' },
      { key: 'always_coop', label: 'Unconditional Nice (No Boundaries)', score: tournamentScores.always_coop, color: '#FBBF24' },
      { key: 'grudger',  label: 'Permanent Grudge (Never Forgive)', score: tournamentScores.grudger, color: '#F87171' }
    ];

    bars.forEach((b, i) => {
      const y = 156 + i * 24;
      const isSelected = b.key === selectedStrategy;
      ctx.fillStyle = isSelected ? '#FFFFFF' : '#9BA3B0';
      ctx.font = isSelected ? 'bold 10px monospace' : '10px monospace';
      ctx.fillText(b.label, 16, y + 11);

      const barX = 278;
      const maxBarW = w - barX - 52;
      ctx.fillStyle = 'rgba(255,255,255,0.07)';
      ctx.fillRect(barX, y, maxBarW, 14);

      ctx.fillStyle = b.color;
      ctx.fillRect(barX, y, (b.score / 100) * maxBarW, 14);

      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(`${b.score}%`, barX + maxBarW + 8, y + 11);
    });
  }

  if (noiseSlider) {
    noiseSlider.addEventListener('input', () => {
      noiseRate = parseInt(noiseSlider.value, 10) / 100;
      noiseValEl.textContent = `${noiseSlider.value}%`;
      runSimulation();
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(3);
      }
    });
  }

  strategyTabs.forEach(btn => {
    btn.addEventListener('click', () => {
      strategyTabs.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      selectedStrategy = btn.getAttribute('data-trust-strategy');
      sound.playClick(640);
      runSimulation();
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(3);
      }
    });
  });

  if (runSimBtn) {
    runSimBtn.addEventListener('click', () => {
      sound.playClick(700);
      runSimulation();
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(3);
      }
    });
  }

  runSimulation();
}
