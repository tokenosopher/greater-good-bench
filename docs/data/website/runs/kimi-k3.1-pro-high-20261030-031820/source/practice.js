const FEELINGS = [
  'angry', 'anxious', 'disappointed', 'embarrassed', 'frustrated',
  'hurt', 'lonely', 'overwhelmed', 'sad', 'uncertain', 'worried', 'resentful'
];

const NEEDS = [
  'to be heard', 'clarity', 'consideration', 'trust', 'respect', 'rest',
  'support', 'fairness', 'autonomy', 'reliability', 'connection', 'reassurance'
];

const SCENARIOS = {
  meeting: 'During our meeting today, I was interrupted twice while I was explaining my idea',
  message: 'When I saw that my message from yesterday still had no reply, even though we had agreed to make a decision today',
  chores: 'When I came home and saw the dishes still in the sink after we had agreed to share the cleaning'
};

const NEXT_LABELS = [
  'Next: name the feeling',
  'Next: find the need',
  'Next: make a request',
  'Finish my message'
];

const cleanSentence = (value) => value.trim().replace(/[.!?]+$/, '');
const capitalize = (value) => value ? value.charAt(0).toUpperCase() + value.slice(1) : value;
const lowerFirst = (value) => value ? value.charAt(0).toLowerCase() + value.slice(1) : value;

function naturalList(items) {
  if (items.length < 2) return items[0] || '';
  if (items.length === 2) return `${items[0]} and ${items[1]}`;
  return `${items.slice(0, -1).join(', ')}, and ${items.at(-1)}`;
}

export function initPractice(showToast) {
  const state = {
    step: 0,
    furthestStep: 0,
    feelings: [],
    needs: []
  };

  const form = document.querySelector('#practice-form');
  const steps = [...document.querySelectorAll('.practice-step')];
  const stepButtons = [...document.querySelectorAll('[data-go-step]')];
  const observation = document.querySelector('#observation');
  const request = document.querySelector('#request');
  const nextButton = document.querySelector('#next-step');
  const backButton = document.querySelector('#back-step');
  const error = document.querySelector('#form-error');
  const resetButton = document.querySelector('#reset-practice');
  let resetArmed = false;
  let resetTimer;

  function createChoices(containerId, values, type) {
    const container = document.querySelector(containerId);
    values.forEach((value) => {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'choice-chip';
      button.textContent = value;
      button.dataset.value = value;
      button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', () => {
        const selected = state[type];
        const index = selected.indexOf(value);
        const limit = type === 'feelings' ? 3 : 2;
        if (index >= 0) {
          selected.splice(index, 1);
        } else if (selected.length < limit) {
          selected.push(value);
        } else {
          showToast(`Choose up to ${limit}. Remove one to make another choice.`);
          return;
        }
        error.textContent = '';
        updateChoices(container, selected);
        updatePreview();
      });
      container.append(button);
    });
  }

  function updateChoices(container, selected) {
    [...container.children].forEach((button) => {
      const isSelected = selected.includes(button.dataset.value);
      button.classList.toggle('selected', isSelected);
      button.setAttribute('aria-pressed', String(isSelected));
    });
  }

  createChoices('#feeling-choices', FEELINGS, 'feelings');
  createChoices('#need-choices', NEEDS, 'needs');

  function observationSentence() {
    const raw = cleanSentence(observation.value);
    if (!raw) return '';
    return /^(when|during|after|before|while|as)\b/i.test(raw)
      ? capitalize(raw)
      : `When ${lowerFirst(raw)}`;
  }

  function requestSentence() {
    const raw = cleanSentence(request.value);
    if (!raw) return '';
    if (/^(could|would|can|will|are|is|do|did|may|might|shall)\b/i.test(raw)) {
      return `${capitalize(raw)}?`;
    }
    return `Would you be willing to ${lowerFirst(raw)}?`;
  }

  function setPreviewLine(id, content, placeholder) {
    const line = document.querySelector(id);
    line.classList.toggle('placeholder', !content);
    line.replaceChildren();
    if (content) {
      line.textContent = content;
    } else {
      line.append(document.createTextNode(placeholder.before));
      const span = document.createElement('span');
      span.textContent = placeholder.highlight;
      line.append(span, document.createTextNode(placeholder.after));
    }
  }

  function updatePreview() {
    const observed = observationSentence();
    const feeling = state.feelings.length ? `I felt ${naturalList(state.feelings)}` : '';
    const need = state.needs.length ? `because I needed ${naturalList(state.needs)}.` : '';
    const requested = requestSentence();

    setPreviewLine('#preview-observation', observed ? `${observed},` : '', {
      before: 'When ', highlight: 'the moment you describe', after: ','
    });
    setPreviewLine('#preview-feeling', feeling, {
      before: 'I felt ', highlight: 'your feeling', after: ''
    });
    setPreviewLine('#preview-need', need, {
      before: 'because I needed ', highlight: 'what matters to you', after: '.'
    });
    setPreviewLine('#preview-request', requested, {
      before: 'Would you be willing to ', highlight: 'one clear next step', after: '?'
    });
  }

  function plainMessage() {
    const lines = [];
    const observed = observationSentence();
    if (observed) lines.push(`${observed},`);
    if (state.feelings.length) {
      let line = `I felt ${naturalList(state.feelings)}`;
      if (state.needs.length) line += ` because I needed ${naturalList(state.needs)}.`;
      else line += '.';
      lines.push(line);
    } else if (state.needs.length) {
      lines.push(`This mattered to me because I needed ${naturalList(state.needs)}.`);
    }
    if (request.value.trim()) lines.push(requestSentence());
    return lines.join(' ');
  }

  function validateStep() {
    if (state.step === 0 && observation.value.trim().length < 8) {
      error.textContent = 'Add a little more detail about this one moment.';
      observation.focus();
      return false;
    }
    if (state.step === 1 && state.feelings.length === 0) {
      error.textContent = 'Choose at least one feeling. An honest guess is enough.';
      document.querySelector('#feeling-choices button')?.focus();
      return false;
    }
    if (state.step === 2 && state.needs.length === 0) {
      error.textContent = 'Choose one thing that mattered to you.';
      document.querySelector('#need-choices button')?.focus();
      return false;
    }
    if (state.step === 3 && request.value.trim().length < 5) {
      error.textContent = 'Add one small, specific action to ask for.';
      request.focus();
      return false;
    }
    error.textContent = '';
    return true;
  }

  function goToStep(newStep, shouldFocus = true) {
    state.step = Math.max(0, Math.min(3, newStep));
    state.furthestStep = Math.max(state.furthestStep, state.step);
    steps.forEach((step, index) => {
      const active = index === state.step;
      step.hidden = !active;
      step.classList.toggle('active', active);
    });
    stepButtons.forEach((button, index) => {
      button.disabled = index > state.furthestStep;
      button.classList.toggle('active', index === state.step);
      button.classList.toggle('complete', index < state.step);
      if (index === state.step) button.setAttribute('aria-current', 'step');
      else button.removeAttribute('aria-current');
    });
    document.querySelector('#step-count').textContent = `Step ${state.step + 1} of 4`;
    document.querySelector('#progress-bar').style.width = `${(state.step + 1) * 25}%`;
    nextButton.innerHTML = `${NEXT_LABELS[state.step]} <span aria-hidden="true">→</span>`;
    backButton.disabled = state.step === 0;
    error.textContent = '';
    if (shouldFocus) steps[state.step].querySelector('legend')?.focus({ preventScroll: true });
  }

  nextButton.addEventListener('click', () => {
    if (!validateStep()) return;
    if (state.step < 3) {
      goToStep(state.step + 1);
    } else {
      document.querySelector('.message-panel').scrollIntoView({ behavior: 'smooth', block: 'center' });
      document.querySelector('#copy-message').focus({ preventScroll: true });
      showToast('Your message is ready. Make it sound like you.');
    }
  });

  backButton.addEventListener('click', () => goToStep(state.step - 1));
  stepButtons.forEach((button) => {
    button.addEventListener('click', () => goToStep(Number(button.dataset.goStep)));
  });

  form.addEventListener('submit', (event) => event.preventDefault());
  form.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      nextButton.click();
    }
  });

  document.querySelectorAll('[data-scenario]').forEach((button) => {
    button.addEventListener('click', () => {
      observation.value = SCENARIOS[button.dataset.scenario];
      observation.dispatchEvent(new Event('input'));
      observation.focus();
      observation.setSelectionRange(observation.value.length, observation.value.length);
    });
  });

  observation.addEventListener('input', () => {
    const length = observation.value.length;
    document.querySelector('#observation-count').textContent = `${length} / 360`;
    const nudge = document.querySelector('#observation-nudge');
    const hasJudgment = /\b(always|never|obviously|clearly|lazy|selfish|stupid|rude|doesn['’]t care|don['’]t care)\b/i.test(observation.value);
    nudge.classList.toggle('warning', hasJudgment);
    nudge.textContent = hasJudgment
      ? 'Could a camera verify that? Try describing only this specific moment.'
      : length > 0 ? 'Good—keep it specific to this one moment.' : 'Tip: begin with “When…” or “During…”';
    error.textContent = '';
    updatePreview();
  });

  request.addEventListener('input', () => {
    const length = request.value.length;
    document.querySelector('#request-count').textContent = `${length} / 280`;
    const nudge = document.querySelector('#request-nudge');
    const vague = /^(be better|do better|stop it|change|care more|be nice|fix this)[.!?]*$/i.test(request.value.trim());
    nudge.classList.toggle('warning', vague);
    nudge.textContent = vague
      ? 'What would “better” look like? Name one observable action.'
      : 'Try “Could we…” or “Would you be willing to…”';
    error.textContent = '';
    updatePreview();
  });

  document.querySelectorAll('[data-starter]').forEach((button) => {
    button.addEventListener('click', () => {
      const existing = request.value.trim();
      const starter = button.dataset.starter;
      if (!existing || /^(could we|would you be willing to|can we agree to)\s*$/i.test(existing)) {
        request.value = starter;
      } else {
        const stripped = existing.replace(/^(could we|would you be willing to|can we agree to)\s+/i, '');
        request.value = starter + lowerFirst(stripped);
      }
      request.dispatchEvent(new Event('input'));
      request.focus();
      request.setSelectionRange(request.value.length, request.value.length);
    });
  });

  async function copyText(text) {
    if (navigator.clipboard && window.isSecureContext) {
      try {
        await navigator.clipboard.writeText(text);
        return true;
      } catch { /* Use the offline-safe selection fallback below. */ }
    }
    const temporary = document.createElement('textarea');
    temporary.value = text;
    temporary.setAttribute('readonly', '');
    temporary.style.cssText = 'position:fixed;left:-9999px;top:0;';
    document.body.append(temporary);
    temporary.select();
    let copied = false;
    try { copied = document.execCommand('copy'); } catch { copied = false; }
    temporary.remove();
    return copied;
  }

  document.querySelector('#copy-message').addEventListener('click', async () => {
    const message = plainMessage();
    const feedback = document.querySelector('#copy-feedback');
    if (!message) {
      feedback.textContent = 'Start with the moment, then your draft will appear here.';
      goToStep(0, false);
      observation.focus();
      return;
    }
    const copied = await copyText(message);
    feedback.textContent = copied ? 'Copied. Take a breath before you send it.' : 'Copy not available—select your message above instead.';
    if (copied) showToast('Message copied to your clipboard.');
  });

  function clearPractice() {
    observation.value = '';
    request.value = '';
    state.feelings = [];
    state.needs = [];
    state.furthestStep = 0;
    updateChoices(document.querySelector('#feeling-choices'), state.feelings);
    updateChoices(document.querySelector('#need-choices'), state.needs);
    observation.dispatchEvent(new Event('input'));
    request.dispatchEvent(new Event('input'));
    document.querySelector('#copy-feedback').textContent = '';
    resetButton.textContent = 'Start over';
    resetArmed = false;
    goToStep(0, false);
    showToast('A clean page. Nothing was saved.');
  }

  resetButton.addEventListener('click', () => {
    const hasContent = observation.value || request.value || state.feelings.length || state.needs.length;
    if (hasContent && !resetArmed) {
      resetArmed = true;
      resetButton.textContent = 'Clear everything?';
      clearTimeout(resetTimer);
      resetTimer = setTimeout(() => {
        resetArmed = false;
        resetButton.textContent = 'Start over';
      }, 3500);
      return;
    }
    clearTimeout(resetTimer);
    clearPractice();
  });

  updatePreview();
  goToStep(0, false);
}
