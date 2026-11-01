import { initHero } from './src/hero.js';
import { initLab } from './src/lab.js';
import { initAtlas } from './src/atlas.js';
import { initPortfolio } from './src/portfolio.js';
import { initRipple } from './src/ripple.js';

function initReveal() {
  const targets = document.querySelectorAll(
    '.section-head, .ledger, .ledger-row, .lab-grid, .atlas-toolbar, .portfolio-panel, .ripple-grid, .method-grid, .fineprint'
  );
  targets.forEach((el) => el.classList.add('reveal'));

  if (!('IntersectionObserver' in window)) {
    targets.forEach((el) => el.classList.add('in'));
    return;
  }

  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('in');
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -40px 0px' });

  targets.forEach((el, i) => {
    el.style.transitionDelay = `${Math.min(i % 6, 5) * 45}ms`;
    io.observe(el);
  });
}

function initNav() {
  const links = [...document.querySelectorAll('.nav-links a')];
  const sections = links
    .map((a) => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);

  if (!sections.length || !('IntersectionObserver' in window)) return;

  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      links.forEach((a) => {
        const active = a.getAttribute('href') === '#' + entry.target.id;
        a.style.color = active ? 'var(--ink)' : '';
      });
    });
  }, { rootMargin: '-40% 0px -55% 0px' });

  sections.forEach((s) => io.observe(s));
}

initHero();
initLab();
initPortfolio();
initAtlas();
initRipple();
initReveal();
initNav();
