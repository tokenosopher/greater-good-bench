// ==========================================================================
// THE HUMAN FIELD MANUAL — Main Entry Module
// 100% Offline, Self-Contained Interactive Training & Calibration System
// ==========================================================================

import { sound } from './src/audio.js';
import { initSection1 } from './src/section1-cpr.js';
import { initSection2 } from './src/section2-breath.js';
import { initSection3 } from './src/section3-conflict.js';
import { initSection4 } from './src/section4-water.js';
import { initSection5 } from './src/section5-leverage.js';
import { initSection6 } from './src/section6-card.js';

// In-memory state (never touches localStorage/cookies so it runs safely in sandboxed iframes)
const appState = {
  theme: 'light',
  completedScales: new Set(),
};

function updateReadinessUI() {
  const count = appState.completedScales.size;
  const statusEl = document.getElementById('readiness-status-text');
  if (statusEl) {
    if (count === 0) {
      statusEl.textContent = '0 of 5 Interactive Drills Practiced — Start any simulator below';
    } else if (count < 5) {
      statusEl.textContent = `${count} of 5 Field Drills Practiced — Keep going to complete full readiness`;
    } else {
      statusEl.textContent = '5 of 5 Field Drills Completed ✓ — Full Citizen Readiness Unlocked';
    }
  }

  for (let i = 1; i <= 5; i++) {
    const done = appState.completedScales.has(i);
    const pip = document.querySelector(`[data-readiness-pip="${i}"]`);
    if (pip) {
      pip.classList.toggle('done', done);
      pip.textContent = done ? `0${i} ✓` : `0${i}`;
    }
    const navLink = document.querySelector(`[data-scale-nav="${i}"]`);
    if (navLink) {
      navLink.classList.toggle('completed', done);
    }
  }
}

function handleScaleComplete(scaleNum) {
  if (!appState.completedScales.has(scaleNum)) {
    appState.completedScales.add(scaleNum);
    updateReadinessUI();
  }
}

function initGlobalControls() {
  const themeBtn = document.getElementById('theme-toggle-btn');
  const audioBtn = document.getElementById('global-audio-btn');
  const sosBtn = document.getElementById('sos-modal-btn');
  const sosCloseBtn = document.getElementById('sos-close-btn');
  const sosBackdrop = document.getElementById('sos-modal-backdrop');

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      appState.theme = appState.theme === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', appState.theme);
      themeBtn.textContent = appState.theme === 'light' ? '☾ Night Mode' : '☀ Paper Mode';
      sound.playClick(520);
    });
  }

  if (audioBtn) {
    audioBtn.addEventListener('click', () => {
      const enabled = sound.toggle();
      audioBtn.textContent = enabled ? '🔊 Synth: ON' : '🔇 Synth: MUTED';
    });
  }

  if (sosBtn && sosBackdrop) {
    sosBtn.addEventListener('click', () => {
      sosBackdrop.classList.add('open');
      sound.playClick(780);
    });
  }

  if (sosCloseBtn && sosBackdrop) {
    sosCloseBtn.addEventListener('click', () => {
      sosBackdrop.classList.remove('open');
      sound.playClick(480);
    });
    sosBackdrop.addEventListener('click', (e) => {
      if (e.target === sosBackdrop) {
        sosBackdrop.classList.remove('open');
      }
    });
  }

  // Readiness pips jump to section
  document.querySelectorAll('[data-readiness-pip]').forEach(pip => {
    pip.addEventListener('click', () => {
      const idx = pip.getAttribute('data-readiness-pip');
      const target = document.getElementById(`scale-${idx}`);
      if (target) {
        target.scrollIntoView({ behavior: 'smooth' });
      }
    });
  });

  // Keyboard shortcut Esc to close modal
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sosBackdrop?.classList.contains('open')) {
      sosBackdrop.classList.remove('open');
    }
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initGlobalControls();
  initSection1(handleScaleComplete);
  initSection2(handleScaleComplete);
  initSection3(handleScaleComplete);
  initSection4(handleScaleComplete);
  initSection5(handleScaleComplete);
  initSection6();
  updateReadinessUI();
});
