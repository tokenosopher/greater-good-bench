const DURATION = 60_000;

export function initBreathing() {
  const button = document.querySelector('#breath-toggle');
  const buttonLabel = button.querySelector('span:last-child');
  const buttonIcon = button.querySelector('.play-icon');
  const circle = document.querySelector('#breath-circle');
  const phaseLabel = document.querySelector('#breath-phase');
  const countLabel = document.querySelector('#breath-count');
  const timerLabel = document.querySelector('#breath-timer');
  const instruction = document.querySelector('#breath-instruction');

  let running = false;
  let elapsedBeforeStart = 0;
  let startedAt = 0;
  let interval = null;
  let previousPhase = '';

  function setPhase(phase, phaseSeconds) {
    if (phase !== previousPhase) {
      previousPhase = phase;
      circle.classList.remove('inhale', 'exhale');
      // Restart the CSS transition at each natural breath boundary.
      void circle.offsetWidth;
      circle.classList.add(phase);
      phaseLabel.textContent = phase === 'inhale' ? 'Breathe in' : 'Breathe out';
      instruction.innerHTML = phase === 'inhale'
        ? 'Let the breath arrive.<br>No forcing, no filling up.'
        : 'Unclench your jaw.<br>Let the breath leave slowly.';
    }
    const phaseLength = phase === 'inhale' ? 4 : 6;
    countLabel.textContent = `${Math.max(1, phaseLength - Math.floor(phaseSeconds))} seconds`;
  }

  function finish() {
    clearInterval(interval);
    interval = null;
    running = false;
    elapsedBeforeStart = 0;
    previousPhase = '';
    circle.classList.remove('inhale', 'exhale');
    phaseLabel.textContent = 'A little room.';
    countLabel.textContent = 'notice what changed';
    timerLabel.textContent = '1:00';
    instruction.innerHTML = 'You don’t have to feel completely calm.<br>A little more choice is enough.';
    buttonLabel.textContent = 'Begin another minute';
    buttonIcon.textContent = '▶';
    button.setAttribute('aria-pressed', 'false');
  }

  function tick() {
    const elapsed = elapsedBeforeStart + (performance.now() - startedAt);
    if (elapsed >= DURATION) {
      finish();
      return;
    }
    const remaining = Math.ceil((DURATION - elapsed) / 1000);
    timerLabel.textContent = `0:${String(remaining).padStart(2, '0')}`;
    const cycleSeconds = (elapsed / 1000) % 10;
    if (cycleSeconds < 4) setPhase('inhale', cycleSeconds);
    else setPhase('exhale', cycleSeconds - 4);
  }

  function start() {
    running = true;
    startedAt = performance.now();
    buttonLabel.textContent = 'Pause for now';
    buttonIcon.textContent = 'Ⅱ';
    button.setAttribute('aria-pressed', 'true');
    tick();
    interval = setInterval(tick, 150);
  }

  function pause() {
    elapsedBeforeStart += performance.now() - startedAt;
    clearInterval(interval);
    interval = null;
    running = false;
    previousPhase = '';
    circle.classList.remove('inhale', 'exhale');
    phaseLabel.textContent = 'Paused';
    countLabel.textContent = 'take all the time you need';
    instruction.innerHTML = 'There is no perfect way to do this.<br>Continue whenever you’re ready.';
    buttonLabel.textContent = 'Continue breathing';
    buttonIcon.textContent = '▶';
    button.setAttribute('aria-pressed', 'false');
  }

  button.setAttribute('aria-pressed', 'false');
  button.addEventListener('click', () => running ? pause() : start());
}
