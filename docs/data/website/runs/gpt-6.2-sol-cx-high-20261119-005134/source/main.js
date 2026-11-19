import { actions, categories } from "./actions.js";
import { artwork } from "./artwork.js";
import { typefaces } from "./typefaces.js";

for (const [family, source, weight, style] of typefaces) {
  document.fonts.add(new FontFace(family, `url(${source})`, { weight, style }));
}

const image = document.getElementById("hero-image");
image.src = artwork;

const grid = document.getElementById("action-grid");
const cardTemplate = document.getElementById("action-template");
const actionStatus = document.getElementById("action-status");
const timeFilter = document.querySelector(".time-filter");
const planButton = document.getElementById("open-plans");
const planCount = document.getElementById("plan-count");
const panel = document.getElementById("panel");
const panelContent = document.getElementById("panel-content");
const planStatus = document.getElementById("plan-status");
const plans = new Map();

const symbols = {
  heart: "♡",
  check: "✓",
  asterisk: "✳",
  box: "◇",
  sun: "☼",
};

function renderActions(announce = false) {
  const selectedTime = timeFilter.querySelector(":checked");
  const suggestions = actions.filter((action) => action.minutes === Number(selectedTime.value));
  const cards = suggestions.map((action) => {
    const card = cardTemplate.content.firstElementChild.cloneNode(true);
    card.dataset.actionId = action.id;
    const category = categories[action.category];
    const icon = card.querySelector(".category-icon");
    icon.dataset.symbol = category.symbol;
    icon.textContent = symbols[category.symbol];
    card.querySelector(".category-name").textContent = category.name;
    card.querySelector("h3").textContent = action.title;
    card.querySelector("p").textContent = action.description;
    const button = card.querySelector("button");
    const plan = plans.get(action.id);
    const label = plan ? (plan.done ? "See completed plan" : "See my plan") : "Make a plan";
    button.firstElementChild.textContent = label;
    button.setAttribute("aria-label", `${label} for “${action.title}”`);
    button.addEventListener("click", () => openAction(action));
    return card;
  });
  grid.replaceChildren(...cards);

  if (announce) {
    actionStatus.textContent = `${suggestions.length} actions for ${selectedTime.labels[0].textContent.toLowerCase()}.`;
  }
}

function updateActionButton(action) {
  const card = grid.querySelector(`[data-action-id="${action.id}"]`);
  if (!card) return;

  const plan = plans.get(action.id);
  const label = plan.done ? "See completed plan" : "See my plan";
  const button = card.querySelector("button");
  button.firstElementChild.textContent = label;
  button.setAttribute("aria-label", `${label} for “${action.title}”`);
}

function showPanel(content) {
  planStatus.textContent = "";
  const wasOpen = panel.open;
  panelContent.innerHTML = content;

  if (wasOpen) {
    panelContent.querySelector("h2").focus();
  } else {
    panel.showModal();
  }
}

function openAction(action, fromList = false) {
  if (plans.has(action.id)) {
    showSavedPlan(action, fromList);
  } else {
    showActionForm(action, fromList);
  }
}

function actionGuide(action) {
  return `
    <ol class="action-steps">${action.steps.map((step) => `<li>${step}</li>`).join("")}</ol>
    <p class="action-example">${action.example}</p>
  `;
}

function showActionForm(action, fromList = false) {
  const plan = plans.get(action.id);
  showPanel(`
    <p class="eyebrow">${categories[action.category].name} · ${action.minutes === 60 ? "1 hour" : `${action.minutes} minutes`}</p>
    <h2 id="panel-title" tabindex="-1">${action.title}</h2>
    ${actionGuide(action)}
    <form class="plan-form">
      <label for="plan-when">When will you do it?</label>
      <input id="plan-when" name="when" placeholder="Example: Tomorrow after lunch" maxlength="100" required>
      <label for="plan-note">Who or where? <span class="optional">Optional</span></label>
      <input id="plan-note" name="note" placeholder="Add a detail to make it easier to follow through" maxlength="160">
      <div class="panel-actions">
        <button class="button button-primary" type="submit">Save my plan <span aria-hidden="true">→</span></button>
        ${plan ? '<button class="button button-outline" type="button" id="cancel-edit">Cancel edit</button>' : ""}
      </div>
    </form>
  `);

  const form = panelContent.querySelector("form");
  if (plan) {
    form.elements.when.value = plan.when;
    form.elements.note.value = plan.note;
    document.getElementById("cancel-edit").addEventListener("click", () => showSavedPlan(action, fromList));
  }

  form.elements.when.addEventListener("input", () => form.elements.when.setCustomValidity(""));
  function savePlan(event) {
    event.preventDefault();
    if (!form.reportValidity()) return;

    const when = form.elements.when.value.trim();
    if (!when) {
      form.elements.when.setCustomValidity("Enter a time for your plan.");
      form.elements.when.reportValidity();
      return;
    }

    plans.set(action.id, { when, note: form.elements.note.value.trim(), done: plan?.done ?? false });
    planCount.hidden = false;
    planCount.textContent = String(plans.size);
    updateActionButton(action);
    showSavedPlan(action, fromList);
    planStatus.textContent = "Plan saved for this visit.";
  }

  // Also handle activation directly in iframes that block native form submission.
  form.querySelector('[type="submit"]').addEventListener("click", savePlan);
  form.addEventListener("submit", savePlan);
}

function showSavedPlan(action, fromList = false) {
  const plan = plans.get(action.id);
  showPanel(`
    ${fromList ? '<button class="text-button back-button" type="button" id="back-to-plans">← All plans</button>' : ""}
    <p class="eyebrow">${plan.done ? "✓ Completed" : "Your plan"}</p>
    <h2 id="panel-title" tabindex="-1">${action.title}</h2>
    <dl class="plan-details">
      <div><dt>When</dt><dd id="saved-when"></dd></div>
      ${plan.note ? '<div><dt>Who or where</dt><dd id="saved-note"></dd></div>' : ""}
    </dl>
    <details class="saved-guide">
      <summary>Action steps</summary>
      ${actionGuide(action)}
    </details>
    <p class="session-note">Plans stay open for this visit. Copy yours to keep it for later.</p>
    <div class="panel-actions">
      <button type="button" class="button button-primary" id="toggle-done">${plan.done ? "Mark as open" : "Mark as done"} <span aria-hidden="true">${plan.done ? "↶" : "✓"}</span></button>
      <button type="button" class="button button-outline" id="copy-plan">Copy plan</button>
      <button type="button" class="text-button" id="edit-plan">Edit plan</button>
    </div>
    <div class="copy-fallback" id="copy-fallback" hidden>
      <label for="copyable-plan">Select and copy your plan</label>
      <textarea id="copyable-plan" rows="6" readonly></textarea>
    </div>
  `);

  document.getElementById("saved-when").textContent = plan.when;
  if (plan.note) document.getElementById("saved-note").textContent = plan.note;
  document.getElementById("back-to-plans")?.addEventListener("click", showPlans);
  document.getElementById("edit-plan").addEventListener("click", () => showActionForm(action, fromList));
  document.getElementById("toggle-done").addEventListener("click", () => {
    plan.done = !plan.done;
    updateActionButton(action);
    showSavedPlan(action, fromList);
    planStatus.textContent = plan.done ? "Action marked as done." : "Action marked as open.";
  });
  document.getElementById("copy-plan").addEventListener("click", (event) => copyPlan(action, plan, event.currentTarget));
}

async function copyPlan(action, plan, button) {
  const lines = [action.title, `When: ${plan.when}`];
  if (plan.note) lines.push(`Who or where: ${plan.note}`);
  lines.push("", ...action.steps, "", action.example);
  const text = lines.join("\n");

  try {
    await navigator.clipboard.writeText(text);
  } catch {
    if (!button.isConnected || !panel.open) return;
    const fallback = document.getElementById("copy-fallback");
    const field = document.getElementById("copyable-plan");
    fallback.hidden = false;
    field.value = text;
    field.focus();
    field.select();
    planStatus.textContent = "Your plan is selected and ready to copy.";
    return;
  }

  if (button.isConnected && panel.open) {
    button.textContent = "Copied";
    planStatus.textContent = "Plan copied.";
  }
}

function showPlans() {
  const saved = actions.filter((action) => plans.has(action.id));
  if (!saved.length) {
    showPanel(`
      <h2 id="panel-title" tabindex="-1">My plans</h2>
      <p class="session-note">Pick an action and decide when you’ll do it. Your plan will appear here for this visit.</p>
      <a class="button button-primary" href="#finder" id="find-from-panel">Find an action <span aria-hidden="true">↓</span></a>
    `);
    document.getElementById("find-from-panel").addEventListener("click", () => panel.close());
    return;
  }

  showPanel(`
    <h2 id="panel-title" tabindex="-1">My plans</h2>
    <p class="session-note">Open a plan to update it or keep a copy.</p>
    <ul class="saved-list">
      ${saved.map((action) => `
        <li><button type="button" data-action="${action.id}">
          <span><strong>${action.title}</strong><span>${plans.get(action.id).done ? "Completed" : "Planned"}</span></span>
          <span aria-hidden="true">↗</span>
        </button></li>
      `).join("")}
    </ul>
  `);
  for (const button of panelContent.querySelectorAll("[data-action]")) {
    const action = saved.find((item) => item.id === button.dataset.action);
    button.addEventListener("click", () => openAction(action, true));
  }
}

timeFilter.addEventListener("change", () => renderActions(true));
planButton.addEventListener("click", showPlans);
panel.querySelector(".panel-close").addEventListener("click", () => panel.close());
panel.addEventListener("click", (event) => {
  if (event.target === panel) panel.close();
});
renderActions();
