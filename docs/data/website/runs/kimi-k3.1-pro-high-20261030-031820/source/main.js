import { initPractice } from './practice.js';
import { initBreathing } from './breathing.js';
import { initUI } from './ui.js';

let toastTimeout;
function showToast(message) {
  const toast = document.querySelector('#toast');
  clearTimeout(toastTimeout);
  toast.textContent = message;
  toast.classList.add('show');
  toastTimeout = setTimeout(() => toast.classList.remove('show'), 3200);
}

initUI();
initPractice(showToast);
initBreathing();
