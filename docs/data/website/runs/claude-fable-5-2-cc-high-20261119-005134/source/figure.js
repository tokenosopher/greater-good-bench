// Pictogram people, drawn from a handful of named joints so they can be posed and animated.
import { s, lerp, ease } from "./ui.js";

/**
 * A figure is a list of parts drawn over named points.
 *   { pts: ["shL","elL","haL"], w: 13, halo: true }   a limb (thick round stroke)
 *   { pts: [...], w: 14, closed: true }               a filled body shape
 *   { head: "head", r: 17 }                           the head
 */
export class Figure {
  constructor(spec, pose, cls = "") {
    this.spec = spec;
    this.pose = {};
    this.el = s("g", { class: "fig " + cls });
    this.nodes = spec.map((part) => {
      if (part.head) {
        const c = s("circle", { class: "fig-head", r: part.r });
        this.el.append(c);
        return { part, c };
      }
      const halo = part.halo
        ? s("path", { class: "fig-halo", "stroke-width": part.w + (part.haloW || 7), fill: "none" })
        : null;
      const p = s("path", {
        class: part.closed ? "fig-body" : "fig-limb",
        "stroke-width": part.w,
      });
      if (halo) this.el.append(halo);
      this.el.append(p);
      return { part, p, halo };
    });
    this.set(pose);
  }

  set(pose) {
    Object.assign(this.pose, pose);
    const P = this.pose;
    for (const { part, c, p, halo } of this.nodes) {
      if (part.head) {
        const at = P[part.head];
        c.setAttribute("cx", at[0].toFixed(2));
        c.setAttribute("cy", at[1].toFixed(2));
        continue;
      }
      const d =
        part.pts.map((name, i) => (i ? "L" : "M") + P[name][0].toFixed(2) + " " + P[name][1].toFixed(2)).join("") +
        (part.closed ? "Z" : "");
      p.setAttribute("d", d);
      if (halo) {
        // "tail" halos outline only the last segment (a forearm), so shoulders stay joined to the body.
        const pts = part.halo === "tail" ? part.pts.slice(-2) : part.pts;
        halo.setAttribute("d", pts.map((name, i) => (i ? "L" : "M") + P[name][0].toFixed(2) + " " + P[name][1].toFixed(2)).join(""));
      }
    }
    return this;
  }

  /** Animate to a pose inside a scope. */
  to(pose, ms, sc, easing = ease.inOut) {
    const from = {};
    for (const k of Object.keys(pose)) from[k] = this.pose[k] ? [...this.pose[k]] : [...pose[k]];
    return sc.tween(
      ms,
      (t) => {
        const cur = {};
        for (const k of Object.keys(pose)) cur[k] = [lerp(from[k][0], pose[k][0], t), lerp(from[k][1], pose[k][1], t)];
        this.set(cur);
      },
      easing
    );
  }
}

// ── Front view (also reads as a person lying on their back, seen from above) ──────────────

export const FRONT_SPEC = [
  { pts: ["hipL", "knL", "ftL"], w: 14 },
  { pts: ["hipR", "knR", "ftR"], w: 14 },
  { pts: ["shL", "shR", "hipR", "hipL"], w: 14, closed: true },
  { head: "head", r: 17 },
  { pts: ["shL", "elL", "haL"], w: 12.5, halo: "tail", haloW: 6 },
  { pts: ["shR", "elR", "haR"], w: 12.5, halo: "tail", haloW: 6 },
];

export const FRONT = {
  head: [0, -30],
  shL: [-22, 4],
  shR: [22, 4],
  hipL: [-13, 78],
  hipR: [13, 78],
  elL: [-34, 40],
  haL: [-37, 76],
  elR: [34, 40],
  haR: [37, 76],
  knL: [-15, 126],
  ftL: [-16, 174],
  knR: [15, 126],
  ftR: [16, 174],
};

export const pose = (overrides) => ({ ...FRONT, ...overrides });

// ── Side view ───────────────────────────────────────────────────────────────────────────

export const SIDE_SPEC = [
  { pts: ["hip", "knB", "ftB"], w: 24 },
  { pts: ["sh", "elB", "haB"], w: 20 },
  { pts: ["neck", "hip"], w: 44 },
  { pts: ["hip", "knA", "ftA"], w: 24, halo: true, haloW: 6 },
  { head: "head", r: 29 },
  { pts: ["sh", "elA", "haA"], w: 20, halo: true, haloW: 8 },
];
