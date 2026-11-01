const SHIFT_CONTENT = {
  reflex: {
    quote: 'You never listen to me. You obviously don’t care about what I have to say.',
    insight: 'A judgment, a generalization, and a guess about their intentions.',
    caption: 'Same hurt. Different doorway.'
  },
  repair: {
    quote: 'When I was interrupted just now, I felt frustrated because I need to be heard. Could you let me finish before you respond?',
    insight: 'A specific moment, an honest feeling, a shared need, and a clear request.',
    caption: 'Clear enough to hear. Open enough to answer.'
  }
};

const GUIDES = {
  listen: {
    instead: '“You never listen to me.”',
    try: '“I want to understand each other. Could we each take two minutes to speak without interrupting?”',
    label: 'Open with a shared purpose'
  },
  defensive: {
    instead: '“Why are you being so defensive?”',
    try: '“I’m not trying to attack you. Would it help to take a break and come back to this in twenty minutes?”',
    label: 'Lower the threat, keep the thread'
  },
  boundary: {
    instead: '“You can’t talk to me like that.”',
    try: '“I want to work this out, and I’m not willing to continue while we’re shouting. I’ll come back at 7.”',
    label: 'Say what you will do, not what they must'
  },
  online: {
    instead: '“Anyone who believes that is an idiot.”',
    try: '“I see this differently. The part I’m concerned about is… What am I missing about your perspective?”',
    label: 'Be firm about ideas, curious about people'
  }
};

export function initUI() {
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const reveals = document.querySelectorAll('.reveal');
  if (reducedMotion || !('IntersectionObserver' in window)) {
    reveals.forEach((element) => element.classList.add('visible'));
  } else {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.08, rootMargin: '0px 0px -30px' });
    reveals.forEach((element) => observer.observe(element));
  }

  const shiftButtons = [...document.querySelectorAll('[data-shift]')];
  const shiftContent = document.querySelector('.shift-content');
  shiftButtons.forEach((button) => {
    button.addEventListener('click', () => {
      const key = button.dataset.shift;
      const content = SHIFT_CONTENT[key];
      shiftButtons.forEach((item) => {
        const active = item === button;
        item.classList.toggle('active', active);
        item.setAttribute('aria-pressed', String(active));
      });
      document.querySelector('#shift-quote').textContent = content.quote;
      document.querySelector('#shift-insight p').textContent = content.insight;
      document.querySelector('#shift-caption').textContent = content.caption;
      shiftContent.classList.remove('changing');
      void shiftContent.offsetWidth;
      shiftContent.classList.add('changing');
    });
  });

  const tabs = [...document.querySelectorAll('[data-guide]')];
  const guidePanel = document.querySelector('#guide-panel');

  function selectTab(tab, focus = false) {
    const content = GUIDES[tab.dataset.guide];
    tabs.forEach((item) => {
      const active = item === tab;
      item.setAttribute('aria-selected', String(active));
      item.tabIndex = active ? 0 : -1;
    });
    guidePanel.setAttribute('aria-labelledby', tab.id);
    document.querySelector('#guide-instead').textContent = content.instead;
    document.querySelector('#guide-try').textContent = content.try;
    guidePanel.querySelector('.try-label').textContent = content.label;
    guidePanel.classList.remove('changing');
    void guidePanel.offsetWidth;
    guidePanel.classList.add('changing');
    if (focus) tab.focus();
  }

  tabs.forEach((tab, index) => {
    tab.addEventListener('click', () => selectTab(tab));
    tab.addEventListener('keydown', (event) => {
      let nextIndex;
      if (event.key === 'ArrowRight') nextIndex = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') nextIndex = (index - 1 + tabs.length) % tabs.length;
      if (event.key === 'Home') nextIndex = 0;
      if (event.key === 'End') nextIndex = tabs.length - 1;
      if (nextIndex !== undefined) {
        event.preventDefault();
        selectTab(tabs[nextIndex], true);
      }
    });
  });
}
