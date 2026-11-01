// ==========================================================================
// SECTION 06: POCKET FIELD CARD — Offline Reference & High-Res Image Exporter
// ==========================================================================

import { sound } from './audio.js';

export function initSection6() {
  const downloadBtn = document.getElementById('download-card-btn');
  const printBtn = document.getElementById('print-card-btn');
  const copyBtn = document.getElementById('copy-card-btn');

  if (printBtn) {
    printBtn.addEventListener('click', () => {
      sound.playClick(640);
      window.print();
    });
  }

  if (copyBtn) {
    copyBtn.addEventListener('click', () => {
      sound.playSuccessChord();
      const summaryText = [
        '=== THE HUMAN FIELD MANUAL (POCKET EDITION) ===',
        '01. CPR (CARDIAC ARREST): Check responsiveness -> Call 911/112 & AED -> Push hard & fast center of chest 100-120 BPM, 5-6 cm deep, full recoil.',
        '02. CHOKING & STROKE: 5 back blows between shoulder blades + 5 abdominal thrusts above navel. Stroke = B.E.F.A.S.T. (Balance, Eyes, Face, Arm, Speech, Time).',
        '03. NERVOUS SYSTEM RESET: Physiological Sigh = 2 nasal inhales + 1 long slow mouth exhale (x3). Wait 90 seconds for adrenaline clearance before acting in anger.',
        '04. CONFLICT & TRUST: "When [observation], I feel [emotion] because I need [value]. Would you be willing to [action]?" Forgive isolated noise; hold firm boundaries.',
        '05. WHO ORAL REHYDRATION (ORS): 1 Liter clean water + 6 level tsp sugar (25g) + 0.5 level tsp salt (2.6g). Bleach water disinfection: 2 drops 6% unscented bleach per 1L (wait 30 min) or 1 min rolling boil.',
        '06. 100x LEVERAGE: Top-evidence global health interventions multiply impact ~100x (~$5 malaria net, ~$1.50 Vitamin A). Donate blood 3x/yr & register as marrow/organ donor.'
      ].join('\n');

      try {
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(summaryText).then(() => {
            copyBtn.textContent = 'Copied Plain-Text Summary ✓';
            setTimeout(() => { copyBtn.textContent = 'Copy Text Summary'; }, 2500);
          }).catch(() => {
            copyBtn.textContent = 'Summary Ready Below ✓';
          });
        }
      } catch {
        copyBtn.textContent = 'Summary Ready ✓';
      }
    });
  }

  if (downloadBtn) {
    downloadBtn.addEventListener('click', () => {
      sound.playSuccessChord();
      exportFieldCardJpg();
      downloadBtn.textContent = 'Field Card Downloaded (.jpg) ✓';
      setTimeout(() => {
        downloadBtn.textContent = 'Download High-Res Field Card (.jpg)';
      }, 3000);
    });
  }
}

function exportFieldCardJpg() {
  const canvas = document.createElement('canvas');
  canvas.width = 1600;
  canvas.height = 1040;
  const ctx = canvas.getContext('2d');

  // Background archival paper
  ctx.fillStyle = '#F5F2EB';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Outer border
  ctx.strokeStyle = '#141619';
  ctx.lineWidth = 6;
  ctx.strokeRect(28, 28, canvas.width - 56, canvas.height - 56);

  // Header bar
  ctx.fillStyle = '#141619';
  ctx.fillRect(28, 28, canvas.width - 56, 86);

  ctx.fillStyle = '#F5F2EB';
  ctx.font = 'bold 28px monospace';
  ctx.fillText('THE HUMAN FIELD MANUAL — EMERGENCY & HIGH-LEVERAGE POCKET CARD', 56, 80);

  const cards = [
    {
      num: '01 / CARDIAC ARREST (CPR)',
      color: '#D9381E',
      lines: [
        '• Unresponsive / not breathing normally:',
        '• Call 911/112 on speaker + send for AED',
        '• Push center of sternum: 100–120 BPM',
        '• Depth: 5–6 cm (2–2.4 in) with full recoil',
        '• Never pause compressions >10 seconds'
      ]
    },
    {
      num: '02 / CHOKING, BLEEDING & STROKE',
      color: '#D9381E',
      lines: [
        '• Choking: 5 back blows + 5 abdominal thrusts',
        '• Fist thumb-in just ABOVE navel, below ribs',
        '• Stroke: B.E.F.A.S.T. (Note exact start time!)',
        '• Severe Bleed: Firm direct pressure 3–5 min',
        '• Do NOT peek; limb artery -> Tourniquet high'
      ]
    },
    {
      num: '03 / 60-SECOND AUTONOMIC RESET',
      color: '#18589A',
      lines: [
        '• Fastest brake on panic: Physiological Sigh',
        '• 1st deep nasal inhale + 2nd top-up inhale',
        '• Long, slow mouth exhale (repeat 3 cycles)',
        '• 90-Second Rule: Adrenaline clears blood in',
        '  90s if you do not feed the narrative loop'
      ]
    },
    {
      num: '04 / CONFLICT & NOISY TRUST',
      color: '#C46D08',
      lines: [
        '• Avoid "Always/Never" blame or stonewalling',
        '• Formula: Observation -> Feeling -> Shared',
        '  Need -> Concrete Doable Request now',
        '• Generous Tit-for-Tat: Forgive isolated noise',
        '  (misread intent) while keeping firm boundaries'
      ]
    },
    {
      num: '05 / WHO ORS & SAFE WATER',
      color: '#0E6B63',
      lines: [
        '• Oral Rehydration (SGLT1 pump): 1 Liter clean',
        '  water + 6 level tsp sugar + 1/2 level tsp salt',
        '• Taste check: "No saltier than human tears"',
        '• Bleach Disinfection: 2 drops 6% unscented',
        '  bleach per 1L (4 if cloudy), wait 30 minutes'
      ]
    },
    {
      num: '06 / THE 100× GOOD MULTIPLIER',
      color: '#177847',
      lines: [
        '• Defeat fatalism: Child survival is 96.3% today',
        '• Top-tested interventions do ~100× more good',
        '• ~$5 protects a child from malaria; ~$4k saves',
        '  a statistical life across top global programs',
        '• Zero-cost: Donate blood 3×/yr & marrow swab'
      ]
    }
  ];

  const colW = 480;
  const rowH = 400;
  cards.forEach((c, idx) => {
    const col = idx % 3;
    const row = Math.floor(idx / 3);
    const x = 56 + col * (colW + 24);
    const y = 144 + row * (rowH + 28);

    ctx.fillStyle = '#FDFBF7';
    ctx.fillRect(x, y, colW, rowH);
    ctx.strokeStyle = '#B8B0A0';
    ctx.lineWidth = 2;
    ctx.strokeRect(x, y, colW, rowH);

    ctx.fillStyle = c.color;
    ctx.fillRect(x, y, colW, 48);

    ctx.fillStyle = '#FFFFFF';
    ctx.font = 'bold 19px monospace';
    ctx.fillText(c.num, x + 18, y + 31);

    ctx.fillStyle = '#141619';
    ctx.font = '20px -apple-system, BlinkMacSystemFont, sans-serif';
    c.lines.forEach((line, lIdx) => {
      ctx.fillText(line, x + 20, y + 95 + lIdx * 54);
    });
  });

  try {
    const dataUrl = canvas.toDataURL('image/jpeg', 0.92);
    const a = document.createElement('a');
    a.href = dataUrl;
    a.download = 'human-field-manual-card.jpg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  } catch {
    // Ignore in restricted iframe if download is blocked
  }
}
