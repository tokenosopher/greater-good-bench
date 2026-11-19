// Tiny DOM helpers shared by every view.

const SVGNS = "http://www.w3.org/2000/svg";

function apply(el, attrs, kids) {
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === false || v == null) continue;
    if (k === "html") el.innerHTML = v;
    else if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else el.setAttribute(k, v === true ? "" : v);
  }
  for (const kid of kids.flat(Infinity)) {
    if (kid === false || kid == null) continue;
    el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  }
  return el;
}

/** Create an HTML element. */
export const h = (tag, attrs, ...kids) => apply(document.createElement(tag), attrs, kids);
/** Create an SVG element. */
export const s = (tag, attrs, ...kids) => apply(document.createElementNS(SVGNS, tag), attrs, kids);

export const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, t) => a + (b - a) * t;
export const ease = {
  out: (t) => 1 - Math.pow(1 - t, 3),
  inOut: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2),
  back: (t) => 1 + 2.4 * Math.pow(t - 1, 3) + 1.4 * Math.pow(t - 1, 2),
  linear: (t) => t,
};

export const reducedMotion = () =>
  typeof matchMedia === "function" && matchMedia("(prefers-reduced-motion: reduce)").matches;

/**
 * A scope collects timers, listeners and animation frames so a step or a view
 * can be torn down in one call without leaking anything.
 */
export function scope() {
  const cleanups = [];
  let dead = false;
  const api = {
    get dead() {
      return dead;
    },
    add(fn) {
      if (dead) fn();
      else cleanups.push(fn);
      return fn;
    },
    on(target, type, fn, opts) {
      target.addEventListener(type, fn, opts);
      api.add(() => target.removeEventListener(type, fn, opts));
    },
    timeout(fn, ms) {
      const id = setTimeout(() => !dead && fn(), ms);
      api.add(() => clearTimeout(id));
      return id;
    },
    interval(fn, ms) {
      const id = setInterval(() => !dead && fn(), ms);
      api.add(() => clearInterval(id));
      return id;
    },
    /** Run fn(dt, now) every frame until the scope ends. */
    frame(fn) {
      let id;
      let last = performance.now();
      const tick = (now) => {
        if (dead) return;
        fn(Math.min(0.1, (now - last) / 1000), now);
        last = now;
        id = requestAnimationFrame(tick);
      };
      id = requestAnimationFrame(tick);
      api.add(() => cancelAnimationFrame(id));
    },
    /** Animate t from 0 to 1 over ms. Resolves when finished (or immediately if the scope ends). */
    tween(ms, fn, easing = ease.out) {
      return new Promise((resolve) => {
        if (dead) return resolve();
        const start = performance.now();
        let id;
        const tick = (now) => {
          if (dead) return resolve();
          const t = clamp((now - start) / ms, 0, 1);
          fn(easing(t), t);
          if (t < 1) id = requestAnimationFrame(tick);
          else resolve();
        };
        id = requestAnimationFrame(tick);
        api.add(() => cancelAnimationFrame(id));
      });
    },
    wait(ms) {
      return new Promise((resolve) => api.timeout(resolve, ms));
    },
    end() {
      if (dead) return;
      dead = true;
      while (cleanups.length) {
        try {
          cleanups.pop()();
        } catch (e) {
          /* keep tearing down */
        }
      }
    },
  };
  return api;
}

/**
 * Turn an SVG node into a real, keyboard-reachable button.
 */
export function hot(el, label, fn) {
  el.setAttribute("role", "button");
  el.setAttribute("tabindex", "0");
  el.setAttribute("aria-label", label);
  el.classList.add("hot");
  el.addEventListener("click", (e) => {
    e.stopPropagation();
    fn(e);
  });
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      if (!e.repeat) fn(e);
    }
  });
  return el;
}

/** A pulsing ring target at (x, y) in SVG units. */
export function ring(x, y, r, label, fn, extra = {}) {
  const g = s(
    "g",
    { class: "ring " + (extra.class || ""), transform: `translate(${x} ${y})` },
    s("circle", { class: "ring-pulse", r }),
    s("circle", { class: "ring-core", r }),
    s("circle", { class: "ring-dot", r: Math.max(4, r * 0.18) }),
    s("circle", { class: "ring-hit", r: r + 14 })
  );
  return hot(g, label, fn);
}

/** Shake an element briefly to say "no". */
export function shake(el) {
  el.classList.remove("shake");
  // Restart the animation.
  void el.getBoundingClientRect();
  el.classList.add("shake");
}

/** Format seconds as m:ss. */
export function mmss(sec) {
  const t = Math.max(0, Math.floor(sec));
  return Math.floor(t / 60) + ":" + String(t % 60).padStart(2, "0");
}

/** Convert a pointer event to SVG user-space coordinates. */
export function svgPoint(svg, e) {
  const pt = svg.createSVGPoint();
  pt.x = e.clientX;
  pt.y = e.clientY;
  const m = svg.getScreenCTM();
  return m ? pt.matrixTransform(m.inverse()) : pt;
}

/**
 * Bring an element to the top of the window, below the sticky bar.
 * Uses window.scrollTo rather than scrollIntoView so an embedding page is never scrolled.
 */
export function scrollToEl(el) {
  const bar = document.getElementById("header");
  const offset = bar ? bar.offsetHeight : 0;
  const top = el.getBoundingClientRect().top + window.scrollY - offset;
  window.scrollTo({ top: Math.max(0, top), behavior: "instant" });
}
