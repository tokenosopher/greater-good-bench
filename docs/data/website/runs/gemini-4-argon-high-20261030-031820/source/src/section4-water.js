// ==========================================================================
// SCALE IV: THE HOUSEHOLD FORMULAS — WHO Oral Rehydration & Safe Water Lab
// ==========================================================================

import { sound } from './audio.js';

export function initSection4(onComplete) {
  const sugarSlider = document.getElementById('ors-sugar-slider');
  const saltSlider = document.getElementById('ors-salt-slider');
  const sugarValEl = document.getElementById('ors-sugar-val');
  const saltValEl = document.getElementById('ors-salt-val');
  const presetBtns = document.querySelectorAll('[data-ors-preset]');

  const osmValEl = document.getElementById('ors-osm-val');
  const fluxValEl = document.getElementById('ors-flux-val');
  const statusBanner = document.getElementById('ors-status-banner');
  const canvas = document.getElementById('ors-canvas');

  // Water Disinfection Calculator elements
  const volSelect = document.getElementById('water-vol-select');
  const clarityBtns = document.querySelectorAll('[data-water-clarity]');
  const methodBtns = document.querySelectorAll('[data-water-method]');
  const waterOutputBox = document.getElementById('water-calc-output');

  let sugarTsp = 6.0; // Optimal WHO home recipe = 6 level tsp (~25g sucrose)
  let saltTsp = 0.5;  // Optimal WHO home recipe = 0.5 level tsp (~2.6g NaCl)
  let completed = false;

  // Animated particles for the SGLT1 gut lumen -> bloodstream canvas
  const particles = Array.from({ length: 28 }, (_, i) => ({
    x: (i / 28) * 520 + 20,
    y: 30 + (i % 5) * 14,
    vy: 0.8 + (i % 3) * 0.3,
    type: i % 3 === 0 ? 'glucose' : (i % 3 === 1 ? 'sodium' : 'water')
  }));

  function evaluateORS() {
    // 1 level tsp sugar ≈ 4.2g sucrose. Hydrolyzes to glucose + fructose (~24.5 mOsm per tsp in 1L)
    // 1 level tsp table salt ≈ 5.6g NaCl. Dissociates to Na+ and Cl- (~190 mOsm per tsp in 1L)
    const sugarOsm = sugarTsp * 24.5;
    const saltOsm = saltTsp * 190;
    const totalOsm = Math.round(sugarOsm + saltOsm);

    // Evaluate physiological state (Normal plasma osmolarity is ~285-295 mOsm/L; WHO Reduced-Osmolarity ORS is ~245 mOsm/L)
    let state = 'optimal';
    let absorptionRate = 95;
    let bannerText = '';
    let bannerColor = '#34D399';

    const sugarOk = sugarTsp >= 4.5 && sugarTsp <= 7.5;
    const saltOk = saltTsp >= 0.35 && saltTsp <= 0.75;

    if (sugarOk && saltOk) {
      state = 'optimal';
      absorptionRate = 96;
      bannerText = 'OPTIMAL WHO RATIO (~242 mOsm/L): Glucose unlocks SGLT1 cotransporters, actively pumping sodium and water into the bloodstream.';
      bannerColor = '#34D399';
    } else if (saltTsp > 1.2 || totalOsm > 360) {
      state = 'hyperosmolar';
      absorptionRate = -65; // Reverse osmotic pull!
      bannerText = `DANGER — HYPEROSMOLAR (${totalOsm} mOsm/L): Solution is too concentrated! Osmosis pulls water OUT of the body into the gut, worsening dehydration.`;
      bannerColor = '#F87171';
    } else if (sugarTsp < 2.0 && saltTsp < 0.2) {
      state = 'plain';
      absorptionRate = 22;
      bannerText = `PLAIN WATER (${totalOsm} mOsm/L): Without coupled sodium and glucose, SGLT1 pumps remain inactive; most water passes straight through an inflamed gut.`;
      bannerColor = '#FBBF24';
    } else if (sugarTsp > 8.0 && saltTsp < 0.25) {
      state = 'soda';
      absorptionRate = -30;
      bannerText = `JUICE / SODA PROFILE (${totalOsm} mOsm/L): Excess unabsorbed sugar ferments and draws water into the intestine, while sodium is too low to replace electrolytes.`;
      bannerColor = '#F87171';
    } else {
      state = 'suboptimal';
      absorptionRate = 52;
      bannerText = `IMBALANCED RATIO (${totalOsm} mOsm/L): Adjust toward 6 level tsp sugar + 0.5 level tsp salt per 1 Liter ("no saltier than tears").`;
      bannerColor = '#FBBF24';
    }

    if (sugarValEl) sugarValEl.textContent = `${sugarTsp.toFixed(1)} tsp (${Math.round(sugarTsp * 4.2)}g)`;
    if (saltValEl) saltValEl.textContent = `${saltTsp.toFixed(2)} tsp (${(saltTsp * 5.6).toFixed(1)}g)`;
    if (osmValEl) {
      osmValEl.textContent = `${totalOsm} mOsm/L`;
      osmValEl.style.color = bannerColor;
    }
    if (fluxValEl) {
      fluxValEl.textContent = absorptionRate > 75
        ? '+96% Rapid Uptake'
        : (absorptionRate < 0 ? `${absorptionRate}% Reverse Loss!` : `+${absorptionRate}% Weak Uptake`);
      fluxValEl.style.color = bannerColor;
    }
    if (statusBanner) {
      statusBanner.textContent = bannerText;
      statusBanner.style.color = bannerColor;
    }

    return { totalOsm, state, absorptionRate };
  }

  if (sugarSlider && saltSlider) {
    sugarSlider.addEventListener('input', () => {
      sugarTsp = parseFloat(sugarSlider.value);
      evaluateORS();
      if (!completed) { completed = true; if (onComplete) onComplete(4); }
    });
    saltSlider.addEventListener('input', () => {
      saltTsp = parseFloat(saltSlider.value);
      evaluateORS();
      if (!completed) { completed = true; if (onComplete) onComplete(4); }
    });
  }

  presetBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const preset = btn.getAttribute('data-ors-preset');
      sound.playClick(660);
      if (preset === 'who') {
        sugarTsp = 6.0; saltTsp = 0.5;
      } else if (preset === 'plain') {
        sugarTsp = 0.0; saltTsp = 0.0;
      } else if (preset === 'soda') {
        sugarTsp = 10.5; saltTsp = 0.05;
      } else if (preset === 'salty') {
        sugarTsp = 6.0; saltTsp = 2.2;
      }
      if (sugarSlider) sugarSlider.value = sugarTsp;
      if (saltSlider) saltSlider.value = saltTsp;
      evaluateORS();
      if (!completed) { completed = true; if (onComplete) onComplete(4); }
    });
  });

  evaluateORS();

  // Animate SGLT1 Cotransporter Canvas
  const ctx = canvas.getContext('2d');
  function animateORS() {
    const { state, absorptionRate } = evaluateORS();
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    const lumenH = 82;
    const cellTop = 82;
    const cellBot = 160;
    const bloodTop = 160;

    // 1. Intestinal Lumen (Top zone)
    ctx.fillStyle = '#131B26';
    ctx.fillRect(0, 0, w, lumenH);
    ctx.fillStyle = '#9BA3B0';
    ctx.font = '600 10px monospace';
    ctx.fillText('INTESTINAL LUMEN (GUT CAVITY — 1 LITER SOLUTION)', 14, 18);

    // 2. Enterocyte Brush Border Membrane & SGLT1 Pumps (Middle zone)
    ctx.fillStyle = '#1E293B';
    ctx.fillRect(0, cellTop, w, cellBot - cellTop);

    // Draw 5 SGLT1 Cotransporter Gate Channels across the membrane
    const gatePositions = [95, 195, 295, 395, 495];
    const pumpsActive = state === 'optimal' || state === 'suboptimal';
    gatePositions.forEach((gx) => {
      ctx.fillStyle = state === 'optimal'
        ? 'rgba(16, 185, 129, 0.28)'
        : (state === 'hyperosmolar' || state === 'soda' ? 'rgba(239, 68, 68, 0.25)' : 'rgba(148, 163, 184, 0.18)');
      ctx.strokeStyle = state === 'optimal'
        ? '#34D399'
        : (state === 'hyperosmolar' || state === 'soda' ? '#F87171' : '#64748B');
      ctx.lineWidth = 2;
      ctx.fillRect(gx - 22, cellTop + 6, 44, cellBot - cellTop - 12);
      ctx.strokeRect(gx - 22, cellTop + 6, 44, cellBot - cellTop - 12);

      ctx.fillStyle = '#E2E8F0';
      ctx.font = 'bold 9px monospace';
      ctx.textAlign = 'center';
      ctx.fillText('SGLT1', gx, cellTop + 32);

      // Direction arrow inside pump
      ctx.fillStyle = absorptionRate > 0 ? '#34D399' : '#F87171';
      ctx.font = 'bold 12px monospace';
      ctx.fillText(absorptionRate > 0 ? '▼' : '▲', gx, cellTop + 52);
    });
    ctx.textAlign = 'left';

    // 3. Bloodstream Capillary (Bottom zone)
    ctx.fillStyle = 'rgba(153, 27, 27, 0.28)';
    ctx.fillRect(0, bloodTop, w, h - bloodTop);
    ctx.strokeStyle = 'rgba(248, 113, 113, 0.35)';
    ctx.beginPath();
    ctx.moveTo(0, bloodTop);
    ctx.lineTo(w, bloodTop);
    ctx.stroke();

    ctx.fillStyle = '#FCA5A5';
    ctx.font = '600 10px monospace';
    ctx.fillText('BLOODSTREAM CAPILLARIES (SYSTEMIC REHYDRATION)', 14, h - 10);

    // Animate particles moving downward (absorption) or upward (hyperosmolar loss)
    const dir = absorptionRate >= 0 ? 1 : -1;
    const speedMult = state === 'optimal' ? 1.5 : (state === 'plain' ? 0.35 : 1.1);

    particles.forEach((p) => {
      p.y += p.vy * dir * speedMult;
      if (dir > 0 && p.y > h - 18) p.y = 26;
      if (dir < 0 && p.y < 24) p.y = h - 22;

      if (p.type === 'water') {
        ctx.fillStyle = '#38BDF8';
        ctx.beginPath();
        ctx.arc(p.x, p.y, 4, 0, Math.PI * 2);
        ctx.fill();
      } else if (p.type === 'glucose' && sugarTsp > 0.2) {
        ctx.fillStyle = '#FBBF24';
        ctx.fillRect(p.x - 4, p.y - 4, 8, 8);
      } else if (p.type === 'sodium' && saltTsp > 0.05) {
        ctx.fillStyle = '#A78BFA';
        ctx.beginPath();
        ctx.arc(p.x, p.y, 3.5, 0, Math.PI * 2);
        ctx.fill();
      }
    });

    requestAnimationFrame(animateORS);
  }

  requestAnimationFrame(animateORS);

  // --- PART B: EMERGENCY SAFE WATER DISINFECTION CALCULATOR ---
  let waterLiters = 1;
  let waterClarity = 'clear'; // 'clear' | 'cloudy'
  let waterMethod = 'bleach6'; // 'bleach6' | 'bleach8' | 'boil' | 'sodis'

  function renderWaterCalculator() {
    if (!waterOutputBox) return;
    const isCloudy = waterClarity === 'cloudy';
    const mult = isCloudy ? 2 : 1; // Double chlorine dose if water is cloudy/turbid after cloth settling

    let headline = '';
    let stepsHtml = '';
    let warningText = '';

    if (waterMethod === 'bleach6' || waterMethod === 'bleach8') {
      // Base EPA/WHO rule for 1L clear water:
      // 6% sodium hypochlorite: 2 drops per Liter (or 8 drops per gallon)
      // 8.25% sodium hypochlorite: 1.5 drops (~2 drops rounded safely for 1L, 6 drops per 4L)
      const baseDropsPerLiter = waterMethod === 'bleach6' ? 2 : 1.5;
      const totalDrops = Math.max(2, Math.round(waterLiters * baseDropsPerLiter * mult));
      const totalMl = (totalDrops * 0.05).toFixed(1);

      headline = `ADD ${totalDrops} DROPS (${totalMl} mL) OF UNSCENTED BLEACH TO ${waterLiters}L WATER`;
      stepsHtml = `
        <div class="protocol-step">
          <div class="step-num">1</div>
          <div class="step-body">
            <h4>Pre-Filter & Settle${isCloudy ? ' (CRITICAL FOR CLOUDY WATER)' : ''}</h4>
            <p>${isCloudy ? 'Pour water through a clean cotton T-shirt or coffee filter twice and let sediment settle before adding bleach.' : 'Ensure water is free of floating particles and use ONLY plain, unscented household bleach (no "splash-less" or scented additives).'}</p>
          </div>
        </div>
        <div class="protocol-step">
          <div class="step-num">2</div>
          <div class="step-body">
            <h4>Mix ${totalDrops} Drops & Wait 30 Full Minutes</h4>
            <p>Stir or shake thoroughly. Let stand for <strong>30 minutes</strong> (wait <strong>60 minutes</strong> if water is icy cold or turbid).</p>
          </div>
        </div>
        <div class="protocol-step">
          <div class="step-num">3</div>
          <div class="step-body">
            <h4>The Smell Verification Test</h4>
            <p>After 30 minutes, the water MUST have a faint smell of chlorine. If not, repeat the dose once and wait another 15 minutes.</p>
          </div>
        </div>
      `;
      warningText = 'NEVER use scented, color-safe, or "splash-less" bleach (contains surfactants/soaps toxic to ingest). Check label for "Sodium Hypochlorite 5%–8.25%".';
    } else if (waterMethod === 'boil') {
      headline = `BRING ALL ${waterLiters}L TO A FULL ROLLING BOIL FOR 1 MINUTE (3 MIN AT HIGH ALTITUDE)`;
      stepsHtml = `
        <div class="protocol-step">
          <div class="step-num">1</div>
          <div class="step-body">
            <h4>Pre-Filter if Cloudy, Then Heat to Vigorous Rolling Boil</h4>
            <p>Pasteurization kills bacteria, viruses, and protozoan cysts (including chlorine-resistant Cryptosporidium) even before boiling, so reaching a full rolling boil is 100% reliable.</p>
          </div>
        </div>
        <div class="protocol-step">
          <div class="step-num">2</div>
          <div class="step-body">
            <h4>Maintain Rolling Boil: 1 Min (Sea Level) or 3 Min (>2,000m / 6,500ft)</h4>
            <p>At higher altitudes, water boils at a lower temperature, requiring 3 minutes of active boiling.</p>
          </div>
        </div>
        <div class="protocol-step">
          <div class="step-num">3</div>
          <div class="step-body">
            <h4>Cool & Aerate to Restore Taste</h4>
            <p>Pour cooled water back and forth between two clean containers several times to re-dissolve oxygen and remove the flat boiled taste.</p>
          </div>
        </div>
      `;
      warningText = 'NOTE: Boiling kills all biological pathogens (viruses, bacteria, parasites) but does NOT remove heavy metals, fuel, or chemical contamination.';
    } else {
      headline = 'SOLAR UV DISINFECTION (SODIS): 6 HOURS FULL SUN IN CLEAR PET BOTTLES';
      stepsHtml = `
        <div class="protocol-step">
          <div class="step-num">1</div>
          <div class="step-body">
            <h4>Use Only Clear 1L–2L PET Plastic or Glass Bottles</h4>
            <p>Remove all labels. Filter cloudy water through folded cloth until you can read newspaper headlines through the bottle.</p>
          </div>
        </div>
        <div class="protocol-step">
          <div class="step-num">2</div>
          <div class="step-body">
            <h4>Fill 3/4, Shake 20 Seconds to Oxygenate, Then Top Off</h4>
            <p>Dissolved oxygen reacts with solar UV-A rays to form reactive oxygen species that destroy pathogen DNA.</p>
          </div>
        </div>
        <div class="protocol-step">
          <div class="step-num">3</div>
          <div class="step-body">
            <h4>Lay Horizontally on a Reflective Roof for 6 Hours (or 2 Days if Overcast)</h4>
            <p>Combined UV-A radiation and solar thermal heating (>50°C) inactivates diarrhea-causing viruses, bacteria, and Giardia.</p>
          </div>
        </div>
      `;
      warningText = 'DO NOT use PVC, green/brown tinted bottles, or containers >2 Liters (UV-A rays cannot penetrate deep or tinted plastic).';
    }

    waterOutputBox.innerHTML = `
      <div style="background: var(--bg-canvas); color: #34D399; font-family: var(--font-mono); font-size: 0.84rem; font-weight: 700; padding: 0.75rem 0.9rem; border-radius: var(--radius-sm); margin-bottom: 0.85rem;">
        ${headline}
      </div>
      <div class="protocol-steps">
        ${stepsHtml}
      </div>
      <div class="clinical-note teal">
        <strong>SAFETY CHECK:</strong> ${warningText}
      </div>
    `;
  }

  if (volSelect) {
    volSelect.addEventListener('change', () => {
      waterLiters = parseFloat(volSelect.value);
      sound.playClick(620);
      renderWaterCalculator();
      if (!completed) { completed = true; if (onComplete) onComplete(4); }
    });
  }

  clarityBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      clarityBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      waterClarity = btn.getAttribute('data-water-clarity');
      sound.playClick(640);
      renderWaterCalculator();
      if (!completed) { completed = true; if (onComplete) onComplete(4); }
    });
  });

  methodBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      methodBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      waterMethod = btn.getAttribute('data-water-method');
      sound.playClick(680);
      renderWaterCalculator();
      if (!completed) { completed = true; if (onComplete) onComplete(4); }
    });
  });

  renderWaterCalculator();
}
