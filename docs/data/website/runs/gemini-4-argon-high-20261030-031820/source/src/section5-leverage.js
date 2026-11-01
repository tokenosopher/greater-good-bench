// ==========================================================================
// SCALE V: THE 100× MULTIPLIER — Reality Calibration & High-Leverage Good
// ==========================================================================

import { sound } from './audio.js';

export function initSection5(onComplete) {
  // Calibration Quiz Sliders
  const q1Slider = document.getElementById('cal-q1-slider');
  const q1Val = document.getElementById('cal-q1-val');
  const q1Reveal = document.getElementById('cal-q1-reveal');

  const q2Slider = document.getElementById('cal-q2-slider');
  const q2Val = document.getElementById('cal-q2-val');
  const q2Reveal = document.getElementById('cal-q2-reveal');

  const q3Slider = document.getElementById('cal-q3-slider');
  const q3Val = document.getElementById('cal-q3-val');
  const q3Reveal = document.getElementById('cal-q3-reveal');

  const revealBtn = document.getElementById('cal-reveal-btn');
  const calCanvas = document.getElementById('calibration-canvas');

  // Impact Multiplier Calculator Controls
  const incomeSlider = document.getElementById('impact-income-slider');
  const incomeValEl = document.getElementById('impact-income-val');
  const pctSlider = document.getElementById('impact-pct-slider');
  const pctValEl = document.getElementById('impact-pct-val');
  const horizonBtns = document.querySelectorAll('[data-impact-horizon]');
  const donorChecks = document.querySelectorAll('[data-donor-check]');

  const outNets = document.getElementById('impact-out-nets');
  const outVitA = document.getElementById('impact-out-vita');
  const outLives = document.getElementById('impact-out-lives');
  const outBio = document.getElementById('impact-out-bio');
  const summaryNote = document.getElementById('impact-summary-note');

  let completed = false;
  let isRevealed = false;
  let horizonYears = 10;

  function updateCalLabels() {
    if (q1Val) q1Val.textContent = `Your Guess: ${q1Slider.value}%`;
    if (q2Val) q2Val.textContent = `Your Guess: ${q2Slider.value}%`;
    if (q3Val) q3Val.textContent = `Your Guess: ${q3Slider.value}×`;
    drawCalibrationCanvas();
  }

  [q1Slider, q2Slider, q3Slider].forEach(s => {
    if (s) {
      s.addEventListener('input', () => {
        updateCalLabels();
      });
    }
  });

  if (revealBtn) {
    revealBtn.addEventListener('click', () => {
      isRevealed = true;
      sound.playSuccessChord();
      if (q1Reveal) q1Reveal.classList.add('visible');
      if (q2Reveal) q2Reveal.classList.add('visible');
      if (q3Reveal) q3Reveal.classList.add('visible');
      revealBtn.textContent = 'Reality Curves Unlocked (Adjust Sliders to Compare)';
      drawCalibrationCanvas();
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(5);
      }
    });
  }

  function drawCalibrationCanvas() {
    if (!calCanvas) return;
    const ctx = calCanvas.getContext('2d');
    const w = calCanvas.width;
    const h = calCanvas.height;
    ctx.clearRect(0, 0, w, h);

    const g1Guess = parseInt(q1Slider?.value || 32, 10);
    const g2Guess = parseInt(q2Slider?.value || 75, 10);
    const g3Guess = parseInt(q3Slider?.value || 10, 10);

    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 10px monospace';
    ctx.fillText('HUMAN REALITY CALIBRATION: YOUR INTUITION VS. EMPIRICAL DATA', 14, 20);

    const rows = [
      {
        label: '1. Extreme Poverty Share Today',
        guess: g1Guess,
        actual: 8.5,
        max: 60,
        unit: '%',
        note: 'Fell from 38% (1990) to ~8.5%'
      },
      {
        label: '2. Global Child Survival (Age 5)',
        guess: g2Guess,
        actual: 96.3,
        max: 100,
        unit: '%',
        note: 'Rose from 57% (1800) to 96.3%'
      },
      {
        label: '3. Top vs. Median Intervention',
        guess: g3Guess,
        actual: 100,
        max: 120,
        unit: '×',
        note: 'Top 1% health programs = ~100× impact'
      }
    ];

    rows.forEach((r, idx) => {
      const y = 36 + idx * 54;
      ctx.fillStyle = '#E2E8F0';
      ctx.font = 'bold 10px monospace';
      ctx.fillText(r.label, 14, y + 10);

      const barX = 228;
      const barW = w - barX - 20;

      // Track background
      ctx.fillStyle = 'rgba(255,255,255,0.07)';
      ctx.fillRect(barX, y, barW, 11);
      ctx.fillRect(barX, y + 15, barW, 11);

      // Guess bar (Blue)
      const guessW = Math.min(1, r.guess / r.max) * barW;
      ctx.fillStyle = '#2563EB';
      ctx.fillRect(barX, y, guessW, 12);
      ctx.fillStyle = '#FFFFFF';
      ctx.font = 'bold 9px monospace';
      ctx.fillText(`Your Guess: ${r.guess}${r.unit}`, barX + 6, y + 9);

      // Actual bar (Emerald — shown fully when revealed, or teaser outline before)
      const actualW = Math.min(1, r.actual / r.max) * barW;
      if (isRevealed) {
        ctx.fillStyle = '#059669';
        ctx.fillRect(barX, y + 16, actualW, 12);
        ctx.fillStyle = '#FFFFFF';
        ctx.font = 'bold 9px monospace';
        ctx.fillText(`Actual: ${r.actual}${r.unit} (${r.note})`, barX + 6, y + 25);
      } else {
        ctx.fillStyle = '#94A3B8';
        ctx.font = '9px monospace';
        ctx.fillText('Click "Reveal Empirical Reality" above to compare', barX + 6, y + 25);
      }
    });
  }

  updateCalLabels();

  // --- PART B: PERSONAL LEVERAGE & DONOR MULTIPLIER ---
  function updateImpactCalculator() {
    const income = parseInt(incomeSlider?.value || 55000, 10);
    const pct = parseFloat(pctSlider?.value || 2.0);
    const annualAllocation = Math.round(income * (pct / 100));
    const totalAllocation = annualAllocation * horizonYears;

    if (incomeValEl) incomeValEl.textContent = `$${income.toLocaleString()}/yr`;
    if (pctValEl) pctValEl.textContent = `${pct.toFixed(1)}% ($${annualAllocation.toLocaleString()}/yr)`;

    // Empirical cost-effectiveness benchmarks (GiveWell / WHO / Disease Control Priorities):
    // - Long-Lasting Insecticide-Treated Net (LLIN) / Seasonal Malaria Chemoprevention: ~$5.50 per child protected
    // - Vitamin A supplementation: ~$1.50 per child-year protected
    // - Statistical life saved across top-tier portfolio: ~$4,000 per life saved (or ~32 healthy life-years / DALYs averted)
    const netsProtected = Math.round(totalAllocation / 5.5);
    const vitADoses = Math.round(totalAllocation / 1.5);
    const statisticalLives = (totalAllocation / 4000).toFixed(2);
    const healthyYears = Math.max(1, Math.round(totalAllocation / 125));

    // Biological & Civic non-monetary checkboxes
    let bloodUnits = 0;
    let cprTrained = 0;
    let marrowRegistered = false;

    donorChecks.forEach(chk => {
      if (chk.checked) {
        const type = chk.getAttribute('data-donor-check');
        if (type === 'blood') bloodUnits = 3 * 3 * horizonYears; // 3 donations/yr * up to 3 components (RBC, plasma, platelets)
        if (type === 'marrow') marrowRegistered = true;
        if (type === 'teach') cprTrained = 2 * horizonYears;
      }
    });

    if (outNets) outNets.textContent = netsProtected.toLocaleString();
    if (outVitA) outVitA.textContent = vitADoses.toLocaleString();
    if (outLives) outLives.textContent = parseFloat(statisticalLives) >= 1.0
      ? `${statisticalLives} Lives`
      : `${healthyYears} Healthy Yrs`;
    if (outBio) {
      const totalPatients = bloodUnits + cprTrained;
      outBio.textContent = `${totalPatients} People${marrowRegistered ? ' + Registry' : ''}`;
    }

    if (summaryNote) {
      summaryNote.innerHTML = `Over <strong>${horizonYears} ${horizonYears === 1 ? 'year' : 'years'}</strong>, directing <strong>${pct.toFixed(1)}%</strong> ($${totalAllocation.toLocaleString()} total) to evidence-verified global health programs unlocks roughly <strong>${healthyYears.toLocaleString()} years of healthy human life</strong> (${statisticalLives} statistical lives saved)—while your zero-cost blood & skill sharing directly protects <strong>${bloodUnits + cprTrained} local lives</strong>.`;
    }
  }

  [incomeSlider, pctSlider].forEach(s => {
    if (s) {
      s.addEventListener('input', () => {
        updateImpactCalculator();
        if (!completed) {
          completed = true;
          if (onComplete) onComplete(5);
        }
      });
    }
  });

  horizonBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      horizonBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      horizonYears = parseInt(btn.getAttribute('data-impact-horizon'), 10);
      sound.playClick(660);
      updateImpactCalculator();
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(5);
      }
    });
  });

  donorChecks.forEach(chk => {
    chk.addEventListener('change', () => {
      sound.playClick(700);
      updateImpactCalculator();
      if (!completed) {
        completed = true;
        if (onComplete) onComplete(5);
      }
    });
  });

  updateImpactCalculator();
}
