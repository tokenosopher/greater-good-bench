'use strict';

const { drawHumanFigure, drawHeartOrgan, lerp, lerpColor } = require('./characters');
const { drawText } = require('./typography');

function clamp(x, a, b) {
  return Math.min(b, Math.max(a, x));
}

function smoothstep(edge0, edge1, x) {
  const t = clamp((x - edge0) / (edge1 - edge0 + 1e-9), 0.0, 1.0);
  return t * t * (3.0 - 2.0 * t);
}

function hash(n) {
  const s = Math.sin(n * 127.1 + 311.7) * 43758.5453123;
  return s - Math.floor(s);
}

// Precompute background/global network nodes & edges across a celestial canopy
const NETWORK_NODES = [];
const NETWORK_EDGES = [];
(function initNetwork() {
  for (let i = 0; i < 68; i++) {
    const row = i % 4;
    const u = (i + 0.5) / 68;
    const wx = -120 + u * 1520 + (hash(i * 7 + 1) - 0.5) * 45;
    // gentle arch across the sky and horizon
    const archY = Math.pow((u - 0.5) * 2.0, 2) * 140;
    const wy = 110 + row * 95 + archY + (hash(i * 13 + 3) - 0.5) * 48;
    NETWORK_NODES.push({
      wx, wy,
      distFromCenter: Math.hypot(wx - 640, wy - 340),
      size: 2.2 + hash(i * 19) * 2.0
    });
  }
  for (let i = 0; i < NETWORK_NODES.length; i++) {
    for (let j = i + 1; j < NETWORK_NODES.length; j++) {
      const d = Math.hypot(NETWORK_NODES[i].wx - NETWORK_NODES[j].wx, NETWORK_NODES[i].wy - NETWORK_NODES[j].wy);
      if (d < 165 && hash(i * 101 + j) > 0.35) {
        NETWORK_EDGES.push([i, j]);
      }
    }
  }
})();

/**
 * Draw a jagged crimson lightning/thorn bolt from (x0, y0) to (x1, y1)
 */
function drawJaggedBolt(canvas, x0, y0, x1, y1, progress, intensity, seed, scale = 1.0, shatter = 0.0) {
  if (intensity <= 0.01 || progress <= 0.01) return;

  const steps = 16;
  const maxStep = Math.max(1, Math.floor(steps * Math.min(1.0, progress)));
  const dx = x1 - x0;
  const dy = y1 - y0;
  const len = Math.hypot(dx, dy) + 1e-5;
  const nx = -dy / len;
  const ny = dx / len;

  const pts = [];
  for (let i = 0; i <= maxStep; i++) {
    const u = (i / steps) * Math.min(1.0, progress);
    const env = Math.sin(u * Math.PI);
    const jag = (hash(seed + i * 17.3) - 0.5) * 2.0 * 28 * scale * env;
    const driftX = (hash(seed + i * 31.1) - 0.25) * 65 * shatter * scale;
    const driftY = -shatter * (40 + hash(seed + i * 47.7) * 80) * scale;
    pts.push([
      x0 + dx * u + nx * jag + driftX,
      y0 + dy * u + ny * jag + driftY
    ]);
  }

  const colCore = lerpColor([1.65, 0.18, 0.16], [1.45, 1.05, 0.32], shatter);

  if (shatter < 0.30) {
    canvas.drawPath(
      pts,
      (t) => (1.8 + Math.sin(t * Math.PI) * 3.2) * scale * (1.0 - shatter * 0.7),
      colCore,
      intensity,
      8 * scale,
      0.55
    );
    // Sharp side thorns
    for (let i = 3; i < pts.length - 2; i += 3) {
      const side = (i % 2 === 0 ? 1 : -1);
      const tx = pts[i][0] + (dx / len * 16 + nx * side * 18) * scale;
      const ty = pts[i][1] + (dy / len * 16 + ny * side * 18) * scale;
      canvas.drawCapsule(pts[i][0], pts[i][1], tx, ty, 2.4 * scale, 0.4 * scale, colCore, intensity * 0.85, 5 * scale, 0.5);
    }
  } else {
    // Shattering into rising golden-ember fireflies during the slow exhale
    for (let i = 0; i < pts.length; i++) {
      const p = pts[i];
      const r = Math.max(1.4, (4.2 - 2.4 * shatter) * scale);
      canvas.drawCircle(p[0], p[1], r, colCore, intensity * (1.0 - shatter * 0.55), 7 * scale, 0.6, 0.6);
      const fx = p[0] + Math.sin(shatter * 5 + i * 1.7) * 16 * scale;
      const fy = p[1] - shatter * 28 * scale;
      canvas.drawCircle(fx, fy, 2.2 * scale, [1.45, 1.15, 0.38], intensity * (1.0 - shatter * 0.45), 6 * scale, 0.5, 0.6);
    }
  }
}

/**
 * Render the Act II Circular Breathing Pacer Halo & Airflow Streams
 * Clockwise from 12 o'clock (-0.5 * PI):
 *  - Inhale 1 (0..80%): -0.50*PI -> +0.24*PI (Right side)
 *  - Inhale 2 Top-Up (80..100%): +0.28*PI -> +0.50*PI (Bottom-Right)
 *  - Long Slow Exhale: +0.54*PI -> +1.48*PI (Left side sweep back to top)
 */
function renderBreathingGuide(canvas, fig2, camScale, t) {
  const guideAlpha = smoothstep(2.70, 3.10, t) * (1.0 - smoothstep(7.05, 7.45, t));
  if (guideAlpha <= 0.01) return;

  const chestS = fig2.chest;
  const noseS = fig2.nose;
  const mouthS = fig2.mouth;

  const inhale1 = smoothstep(3.00, 4.15, t);
  const inhale2 = smoothstep(4.20, 4.85, t);
  const exhale = smoothstep(4.95, 7.20, t);

  const lungRatio = (0.80 * inhale1 + 0.20 * inhale2) * (1.0 - 0.82 * exhale);
  const ringR = (68 + 18 * lungRatio) * camScale;

  // Subtle dark circular halo backing & reference ring
  canvas.drawArc(chestS[0], chestS[1], ringR, 4.0, 0, Math.PI * 2, [0.14, 0.28, 0.44], 0.45 * guideAlpha, 2, 0.0);

  // Tick marks at 12 o'clock, 4:30 (80% inhale), and 6 o'clock (100% full)
  for (const ang of [-0.5 * Math.PI, 0.26 * Math.PI, 0.5 * Math.PI]) {
    const tx0 = chestS[0] + Math.cos(ang) * (ringR - 7);
    const ty0 = chestS[1] + Math.sin(ang) * (ringR - 7);
    const tx1 = chestS[0] + Math.cos(ang) * (ringR + 7);
    const ty1 = chestS[1] + Math.sin(ang) * (ringR + 7);
    canvas.drawCapsule(tx0, ty0, tx1, ty1, 1.5, 1.5, [0.45, 0.75, 0.95], 0.65 * guideAlpha);
  }

  // Arc 1: Deep Inhale 1 (-0.50*PI to +0.24*PI)
  if (inhale1 > 0.01) {
    const aStart = -0.50 * Math.PI;
    const aEnd = lerp(aStart, 0.24 * Math.PI, inhale1);
    canvas.drawArc(
      chestS[0], chestS[1], ringR, 6.5,
      aStart, aEnd,
      [0.20, 0.88, 1.35],
      guideAlpha * 0.92,
      6, 0.35
    );
  }

  // Arc 2: Top-Up Inhale 2 (+0.28*PI to +0.50*PI)
  if (inhale2 > 0.01) {
    const aStart = 0.28 * Math.PI;
    const aEnd = lerp(aStart, 0.50 * Math.PI, inhale2);
    canvas.drawArc(
      chestS[0], chestS[1], ringR, 8.0,
      aStart, aEnd,
      [0.65, 1.35, 1.75],
      guideAlpha * 0.98,
      8, 0.45
    );
  }

  // Arc 3: Long Slow Exhale (+0.54*PI to +1.48*PI)
  if (exhale > 0.01) {
    const aStart = 0.54 * Math.PI;
    const aEnd = lerp(aStart, 1.48 * Math.PI, exhale);
    canvas.drawArc(
      chestS[0], chestS[1], ringR, 7.0,
      aStart, aEnd,
      [1.35, 0.98, 0.28],
      guideAlpha * 0.95,
      7, 0.40
    );
  }

  // --- Sleek Top 3-Step Physiological Sigh HUD Header (Never blocks airflow!) ---
  const hudY = 42;
  const b1Active = t >= 2.90 && t < 4.20;
  const b2Active = t >= 4.15 && t < 4.95;
  const b3Active = t >= 4.90 && t < 7.30;

  // Connecting progress bar ONLY in the gaps between the 3 badges
  canvas.drawCapsule(432, hudY + 7, 528, hudY + 7, 1.5, 1.5, [0.18, 0.36, 0.54], 0.55 * guideAlpha);
  canvas.drawCapsule(752, hudY + 7, 845, hudY + 7, 1.5, 1.5, [0.18, 0.36, 0.54], 0.55 * guideAlpha);
  if (inhale1 > 0.01) {
    canvas.drawCapsule(432, hudY + 7, lerp(432, 528, inhale1), hudY + 7, 2.2, 2.2, [0.25, 0.95, 1.40], 0.85 * guideAlpha);
  }
  if (inhale2 > 0.01) {
    canvas.drawCapsule(752, hudY + 7, lerp(752, 845, exhale > 0.01 ? exhale : inhale2 * 0.25), hudY + 7, 2.2, 2.2, [1.25, 0.95, 0.32], 0.85 * guideAlpha);
  }

  // Step 1 Badge (Top-Left): "1 · INHALE 80%"
  drawText(canvas, '1 · INHALE 80%', 340, hudY, 14, [0.45, 1.08, 1.45], guideAlpha * (b1Active ? 1.0 : 0.60), {
    align: 'center', weight: 0.095, bgAlpha: 0.85, borderColor: b1Active ? [0.28, 0.95, 1.40] : [0.15, 0.40, 0.60]
  });

  // Step 2 Badge (Top-Center): "+2 · TOP-UP 100%"
  const b2Alpha = guideAlpha * smoothstep(3.0, 3.4, t);
  drawText(canvas, '+2 · TOP-UP 100%', 640, hudY, 14, [0.78, 1.35, 1.65], b2Alpha * (b2Active ? 1.0 : (t > 4.2 ? 0.65 : 0.40)), {
    align: 'center', weight: 0.095, bgAlpha: 0.85, borderColor: b2Active ? [0.65, 1.30, 1.65] : [0.18, 0.45, 0.68]
  });

  // Step 3 Badge (Top-Right): "3 · SLOW EXHALE"
  const b3Alpha = guideAlpha * smoothstep(3.0, 3.4, t);
  drawText(canvas, '3 · SLOW EXHALE', 940, hudY, 14, [1.35, 1.02, 0.35], b3Alpha * (b3Active ? 1.0 : 0.40), {
    align: 'center', weight: 0.095, bgAlpha: 0.85, borderColor: b3Active ? [1.25, 0.92, 0.28] : [0.40, 0.32, 0.14]
  });

  // --- Animated Nasal Inhale Streams (t = 3.0s .. 4.9s) ---
  const inFlowAlpha = guideAlpha * smoothstep(2.95, 3.15, t) * (1.0 - smoothstep(4.80, 5.00, t));
  if (inFlowAlpha > 0.01) {
    const isSecondPuff = smoothstep(4.15, 4.30, t);
    const streamCount = isSecondPuff > 0.2 ? 2 : 1;
    for (let s = 0; s < streamCount; s++) {
      const pts = [];
      const col = s === 1 ? [0.75, 1.35, 1.65] : [0.22, 0.95, 1.40];
      for (let i = 0; i <= 14; i++) {
        const u = i / 14;
        const dist = (1.0 - u) * (92 - s * 22) * camScale;
        const angle = -0.28 + s * 0.24 + Math.sin(u * 4.5 - t * 7.0) * 0.10 * (1.0 - u);
        pts.push([
          noseS[0] + Math.cos(angle) * dist,
          noseS[1] + Math.sin(angle) * dist
        ]);
      }
      canvas.drawPath(pts, (u) => (1.2 + u * 2.2), col, inFlowAlpha * 0.88, 4, 0.35);

      for (let p = 0; p < 3; p++) {
        const pu = ((t * 2.2 + p * 0.33 + s * 0.15) % 1.0);
        const idx = Math.min(pts.length - 1, Math.floor(pu * pts.length));
        canvas.drawCircle(pts[idx][0], pts[idx][1], 3.0, col, inFlowAlpha, 4, 0.5, 0.4);
      }
    }
  }

  // --- Animated Golden-Teal Exhale Stream out of Mouth (t = 4.95s .. 7.25s) ---
  const exFlowAlpha = guideAlpha * smoothstep(4.92, 5.18, t) * (1.0 - smoothstep(7.00, 7.40, t));
  if (exFlowAlpha > 0.01) {
    const reach = smoothstep(4.95, 6.35, t);
    for (let rib = -1; rib <= 1; rib++) {
      const pts = [];
      for (let i = 0; i <= 20; i++) {
        const u = (i / 20) * reach;
        const dx = u * 235 * camScale;
        const wave = Math.sin(u * 6.0 - t * 4.0 + rib * 1.2) * (5 + u * 16) * camScale;
        pts.push([
          mouthS[0] + 6 + dx,
          mouthS[1] + rib * 5 + u * 16 * camScale + wave
        ]);
      }
      const col = rib === 0 ? [1.35, 1.02, 0.32] : [0.28, 0.98, 0.88];
      canvas.drawPath(
        pts,
        (u) => (1.2 + Math.sin(u * Math.PI) * 2.6) * (rib === 0 ? 1.15 : 0.8),
        col,
        exFlowAlpha * (rib === 0 ? 0.88 : 0.60),
        5, 0.35
      );
    }
  }
}

/**
 * Render the continuous Lower Autonomic Heart-Rate / Nervous System Waveform (ECG / HRV trace)
 */
function renderAutonomicWaveform(canvas, t) {
  const panelY = 618;
  const xStart = 180;
  const xEnd = 1100;
  const spanW = xEnd - xStart;

  const breathPhase = smoothstep(2.8, 3.4, t) * (1.0 - smoothstep(7.0, 7.6, t));
  const calmPhase = smoothstep(4.8, 6.2, t);
  const coRegPhase = smoothstep(7.3, 8.2, t);

  canvas.drawCapsule(xStart, panelY, xEnd, panelY, 0.8, 0.8, [0.14, 0.24, 0.36], 0.45);

  const steps = 180;
  const ptsMain = [];
  const ptsSecond = [];
  const ptsThird = [];

  for (let i = 0; i <= steps; i++) {
    const u = i / steps;
    const x = xStart + u * spanW;

    const localTime = t - (1.0 - u) * 1.5;
    const localCalm = smoothstep(4.2, 5.5, localTime);
    const localPause = smoothstep(2.6, 3.2, localTime) * (1.0 - localCalm);

    const phaseFast = u * 52 - t * 14.0;
    const qrs = Math.pow(Math.max(0, Math.sin(phaseFast)), 7) * 22
      - Math.pow(Math.max(0, Math.sin(phaseFast + 0.4)), 9) * 16
      + Math.sin(u * 95 - t * 22) * 6.5;

    const diaphragmWave = Math.sin(u * 10 - t * 3.2) * 13;
    const coherentWave = Math.sin(u * 14 - t * 3.6) * 12;

    const dy = qrs * (1.0 - localCalm) * (1.0 - localPause * 0.65)
      + diaphragmWave * localPause
      + coherentWave * localCalm;

    const env = Math.sin(u * Math.PI);
    ptsMain.push([x, panelY - dy * env]);

    if (coRegPhase > 0.01) {
      const dy2 = Math.sin(u * 14 - t * 3.6 + 0.9) * 10 * env * coRegPhase;
      const dy3 = Math.sin(u * 14 - t * 3.6 - 0.9) * 10 * env * coRegPhase;
      ptsSecond.push([x, panelY - dy2]);
      ptsThird.push([x, panelY - dy3]);
    }
  }

  const col1 = lerpColor([1.45, 0.22, 0.20], [0.28, 0.95, 1.35], breathPhase);
  const mainCol = lerpColor(col1, [1.35, 1.00, 0.32], calmPhase);

  if (coRegPhase > 0.01) {
    canvas.drawPath(ptsSecond, 1.4, [0.28, 0.98, 0.92], 0.65 * coRegPhase, 3, 0.25);
    canvas.drawPath(ptsThird, 1.4, [1.15, 0.72, 0.28], 0.65 * coRegPhase, 3, 0.25);
  }
  canvas.drawPath(ptsMain, 2.0, mainCol, 0.92, 4, 0.30);

  const lastPt = ptsMain[ptsMain.length - 1];
  canvas.drawCircle(lastPt[0], lastPt[1], 3.6, mainCol, 0.95, 5, 0.4, 0.3);
}

/**
 * Render a single frame of the 10-second animation at time `t` (in seconds, 0.0 <= t <= 10.0)
 */
function renderFrame(canvas, t) {
  const W = canvas.width;
  const H = canvas.height;

  // --- 1. TIMELINE ACT WEIGHTS & CAMERA CHOREOGRAPHY ---
  const act2Zoom = smoothstep(2.65, 3.35, t) * (1.0 - smoothstep(7.05, 7.80, t));
  const act3Wide = smoothstep(8.20, 9.65, t);

  const camScale = 1.0 + 0.36 * act2Zoom - 0.16 * act3Wide;
  const camFocusX = lerp(630, 665, act2Zoom);
  const camFocusY = lerp(355, 315, act2Zoom) + act3Wide * 10;

  function worldToScreen(wx, wy) {
    return [
      W * 0.5 + (wx - camFocusX) * camScale,
      H * 0.5 + (wy - camFocusY) * camScale
    ];
  }

  // --- 2. ATMOSPHERIC BACKGROUND ---
  const stressBg = smoothstep(0.15, 1.8, t) * (1.0 - smoothstep(3.0, 5.4, t));
  const calmBg = smoothstep(5.0, 7.6, t);

  const topRGB = lerpColor(
    lerpColor([0.012, 0.024, 0.055], [0.048, 0.012, 0.020], stressBg),
    [0.014, 0.038, 0.072],
    calmBg
  );
  const botRGB = lerpColor(
    lerpColor([0.028, 0.055, 0.115], [0.095, 0.018, 0.028], stressBg),
    [0.035, 0.092, 0.135],
    calmBg
  );
  const glowRGB = lerpColor(
    lerpColor([0.03, 0.07, 0.14], [0.18, 0.025, 0.03], stressBg),
    [0.16, 0.12, 0.04],
    calmBg
  );

  const centerS = worldToScreen(635, 340);
  canvas.drawBackground(topRGB, botRGB, glowRGB, centerS[0], centerS[1], 480 * camScale);

  // --- 3. GROUND HORIZON & DELICATE HUMAN NETWORK CONSTELLATION ---
  const groundY = 535;
  // Use a very wide radius (4200) so the ground plane is gently curved right underneath all three characters' feet!
  const earthCenter = worldToScreen(640, groundY + 4200);
  const earthRadius = 4200 * camScale;
  const horizonCol = lerpColor(
    lerpColor([0.14, 0.28, 0.48], [0.55, 0.14, 0.16], stressBg),
    [0.82, 0.65, 0.26],
    calmBg
  );
  canvas.drawArc(
    earthCenter[0], earthCenter[1],
    earthRadius, 2.2 + 1.5 * calmBg,
    -Math.PI * 0.62, -Math.PI * 0.38,
    horizonCol, 0.65, 6 * camScale, 0.25
  );

  // Ripple wave radius expanding from center in Act III (t = 7.2s .. 10.0s)
  const rippleProgress = smoothstep(7.15, 9.95, t);
  const rippleRadiusWorld = rippleProgress * 920;

  // Delicate Network Edges in the sky canopy
  const netBaseAlpha = 0.16 - 0.08 * act2Zoom + 0.26 * act3Wide;
  for (const [i, j] of NETWORK_EDGES) {
    const n1 = NETWORK_NODES[i];
    const n2 = NETWORK_NODES[j];
    const p1 = worldToScreen(n1.wx, n1.wy);
    const p2 = worldToScreen(n2.wx, n2.wy);

    const avgDist = 0.5 * (n1.distFromCenter + n2.distFromCenter);
    const lit = smoothstep(avgDist - 90, avgDist + 30, rippleRadiusWorld);
    const edgeCol = lerpColor(
      lerpColor([0.14, 0.26, 0.44], [0.45, 0.10, 0.12], stressBg),
      [0.85, 0.68, 0.26],
      lit
    );
    const edgeA = netBaseAlpha * (0.45 + 0.65 * lit);
    canvas.drawCapsule(p1[0], p1[1], p2[0], p2[1], 0.85, 0.85, edgeCol, edgeA, 0, 0);
  }

  // Delicate Network Nodes
  for (let i = 0; i < NETWORK_NODES.length; i++) {
    const n = NETWORK_NODES[i];
    const p = worldToScreen(n.wx, n.wy);
    if (p[0] < -20 || p[0] > W + 20 || p[1] < -20 || p[1] > H + 20) continue;

    const lit = smoothstep(n.distFromCenter - 70, n.distFromCenter + 20, rippleRadiusWorld);
    const waveFront = Math.exp(-Math.pow((n.distFromCenter - rippleRadiusWorld) / 55, 2)) * smoothstep(7.2, 7.5, t);
    const nodeCol = lerpColor(
      lerpColor([0.22, 0.42, 0.68], [0.68, 0.15, 0.16], stressBg),
      [1.25, 0.95, 0.35],
      Math.min(1, lit + waveFront)
    );
    const r = (n.size + lit * 1.4 + waveFront * 2.0) * camScale;
    const nodeA = Math.min(0.85, netBaseAlpha * (0.8 + 1.1 * lit + waveFront));
    canvas.drawCircle(p[0], p[1], r, nodeCol, nodeA, (2 + 5 * (lit + waveFront)) * camScale, 0.4, 0.3);
  }

  // Expanding golden harmonic rings in Act III
  if (t > 7.2) {
    for (let k = 0; k < 3; k++) {
      const rt = clamp((t - 7.25 - k * 0.48) / 2.3, 0.0, 1.0);
      if (rt > 0.01 && rt < 0.99) {
        const ringCenter = worldToScreen(675, 360);
        const rad = rt * 680 * camScale;
        const a = (1.0 - rt) * 0.38;
        canvas.drawArc(ringCenter[0], ringCenter[1], rad, 2.2, 0, Math.PI * 2, [1.25, 0.96, 0.32], a, 6, 0.35);
      }
    }
  }

  // --- 4. THREE FOREGROUND HUMAN CHARACTERS (HEROIC SCALE: 1.38x) ---
  const charScale = 1.38;

  // === FIGURE 1 (Left Adult) ===
  const f1Hit = smoothstep(0.10, 0.45, t);
  const f1Lunge = smoothstep(0.55, 1.10, t) * (1.0 - smoothstep(2.7, 3.5, t));
  const f1Heal = smoothstep(7.55, 8.35, t);
  const f1Stress = f1Hit * (1.0 - f1Heal);

  const fig1Screen = worldToScreen(245 + f1Lunge * 32, groundY);
  const fig1 = drawHumanFigure(canvas, {
    x: fig1Screen[0],
    y: fig1Screen[1],
    scale: 1.00 * charScale * camScale,
    facing: 1,
    spineLean: -0.08 * smoothstep(0.1, 0.4, t) * (1 - f1Lunge) + 0.28 * f1Lunge - 0.04 * f1Heal,
    crouch: 0.05 * f1Lunge,
    headTilt: 0.10 * f1Lunge - 0.06 * f1Heal,
    armL: {
      shoulderAngle: lerp(0.18, -0.45, f1Lunge),
      elbowAngle: lerp(0.35, -0.20, f1Lunge)
    },
    armR: {
      shoulderAngle: lerp(0.22, 1.30 * f1Lunge + 0.55 * f1Heal, 1.0),
      elbowAngle: lerp(0.35, 0.12 * (1 - f1Lunge) + 0.45 * f1Heal, 1.0)
    }
  }, {
    stress: f1Stress,
    calm: f1Heal,
    breath: 0.25 + 0.15 * Math.sin(t * 2.5),
    showAnatomy: 0.0,
    time: t,
    alpha: 1.0 - 0.45 * act2Zoom
  });

  // === FIGURE 2 (Center Protagonist) ===
  const f2Hit = smoothstep(0.75, 1.15, t);
  const f2Loom = smoothstep(0.95, 1.45, t) * (1.0 - smoothstep(2.60, 3.10, t));
  const f2Pause = smoothstep(2.60, 3.10, t);
  const inhale1 = smoothstep(3.00, 4.15, t);
  const inhale2 = smoothstep(4.20, 4.85, t);
  const exhale = smoothstep(4.95, 7.20, t);
  const f2Kneel = smoothstep(7.25, 8.15, t);

  const f2Breath = (0.18 + 0.62 * inhale1 + 0.20 * inhale2) * (1.0 - 0.72 * exhale) + 0.25 * f2Kneel;
  const f2AlveoliPop = smoothstep(4.18, 4.45, t) * (1.0 - smoothstep(5.15, 5.75, t));
  const f2VagusGlow = smoothstep(4.90, 5.35, t) * (1.0 - smoothstep(7.40, 8.20, t));
  const f2Calm = smoothstep(5.10, 6.80, t);
  const f2Stress = f2Hit * (1.0 - smoothstep(4.50, 5.85, t));

  const f2WorldX = 595 + f2Loom * 28 + f2Kneel * 65;
  const fig2Screen = worldToScreen(f2WorldX, groundY);

  const f2ArmRShoulder = f2Loom * 1.42 + f2Pause * (1 - f2Kneel) * (-0.28) + f2Kneel * 1.12;
  const f2ArmRElbow = f2Loom * 0.15 + f2Pause * (1 - f2Kneel) * 0.65 + f2Kneel * 0.28;
  const f2ArmLShoulder = f2Loom * 0.90 + f2Pause * (1 - f2Kneel) * (-0.38) + f2Kneel * 0.92;
  const f2ArmLElbow = f2Loom * 0.22 + f2Pause * (1 - f2Kneel) * 0.55 + f2Kneel * 0.35;

  const fig2 = drawHumanFigure(canvas, {
    x: fig2Screen[0],
    y: fig2Screen[1],
    scale: 1.04 * charScale * camScale,
    facing: 1,
    spineLean: 0.26 * f2Loom - 0.04 * (inhale1 + inhale2) * (1 - exhale) + 0.22 * f2Kneel,
    crouch: 0.76 * f2Kneel,
    headTilt: 0.15 * f2Loom - 0.08 * (inhale1 + inhale2) * (1 - exhale) + 0.18 * f2Kneel,
    armL: { shoulderAngle: f2ArmLShoulder, elbowAngle: f2ArmLElbow },
    armR: { shoulderAngle: f2ArmRShoulder, elbowAngle: f2ArmRElbow }
  }, {
    stress: f2Stress,
    calm: f2Calm,
    breath: clamp(f2Breath, 0.15, 1.0),
    alveoliPop: f2AlveoliPop,
    vagusGlow: f2VagusGlow,
    showAnatomy: smoothstep(2.55, 3.10, t) * (1.0 - smoothstep(7.10, 7.65, t)),
    time: t,
    alpha: 1.0
  });

  // === FIGURE 3 (Right Child) ===
  const f3Fear = smoothstep(1.35, 1.85, t) * (1.0 - smoothstep(5.20, 6.60, t));
  const f3Relief = smoothstep(5.40, 7.20, t);
  const f3Connect = smoothstep(7.35, 8.25, t);

  const f3WorldX = 935 + f3Fear * 20 - f3Connect * 58;
  const fig3Screen = worldToScreen(f3WorldX, groundY);

  const fig3 = drawHumanFigure(canvas, {
    x: fig3Screen[0],
    y: fig3Screen[1],
    scale: 0.68 * charScale * camScale,
    facing: -1,
    spineLean: -0.28 * f3Fear + 0.12 * f3Connect,
    crouch: 0.36 * f3Fear,
    headTilt: 0.20 * f3Fear - 0.12 * f3Connect,
    armL: {
      shoulderAngle: lerp(0.25, 1.45, f3Fear) * (1 - f3Connect) + 0.95 * f3Connect,
      elbowAngle: lerp(0.35, 1.15, f3Fear) * (1 - f3Connect) + 0.25 * f3Connect
    },
    armR: {
      shoulderAngle: lerp(0.30, 1.60, f3Fear) * (1 - f3Connect) + 1.08 * f3Connect,
      elbowAngle: lerp(0.40, 1.25, f3Fear) * (1 - f3Connect) + 0.22 * f3Connect
    }
  }, {
    stress: f3Fear * 0.85,
    calm: f3Connect,
    breath: 0.25 + 0.15 * Math.sin(t * 3.0) + 0.2 * f3Relief,
    showAnatomy: 0.0,
    time: t,
    alpha: 1.0
  });

  // --- 5. ACT I & II: JAGGED CRIMSON CONTAGION BOLTS & THE STASIS PAUSE ---
  // Bolt 1: External world -> Figure 1 (t = 0.05s .. 1.15s)
  if (t < 1.25) {
    const p1 = smoothstep(0.05, 0.45, t);
    const fade1 = 1.0 - smoothstep(0.75, 1.20, t);
    const start1 = worldToScreen(20, 280);
    drawJaggedBolt(canvas, start1[0], start1[1], fig1.heartPos[0], fig1.heartPos[1], p1, fade1, 11.0, camScale);
  }

  // Bolt 2: Figure 1 -> Figure 2 (t = 0.65s .. 2.45s)
  if (t >= 0.60 && t < 2.55) {
    const p2 = smoothstep(0.65, 1.15, t);
    const fade2 = 1.0 - smoothstep(1.95, 2.50, t);
    drawJaggedBolt(canvas, fig1.handFront[0], fig1.handFront[1], fig2.heartPos[0], fig2.heartPos[1], p2, fade2, 29.0, camScale);
  }

  // Bolt 3: Figure 2 -> Child (Launches at t = 1.00s, reaches child's shield zone by t = 1.50s, freezes in Stasis Shield at t = 2.45s, shatters into golden fireflies during Exhale t = 5.1s .. 6.8s)
  if (t >= 1.00 && t < 7.05) {
    const p3 = clamp(smoothstep(1.00, 1.50, t) * 0.88, 0.0, 0.88);
    const shatter = smoothstep(5.15, 6.75, t);
    const fade3 = 1.0 - smoothstep(6.45, 7.00, t);
    const startX = lerp(fig2.chest[0] + 22 * camScale, fig2.handFront[0], 1.0 - smoothstep(2.55, 3.15, t));
    const startY = lerp(fig2.chest[1], fig2.handFront[1], 1.0 - smoothstep(2.55, 3.15, t));
    const targetX = lerp(startX, fig3.head[0] - 28 * camScale, 0.88);
    const targetY = lerp(startY, fig3.chest[1], 0.88);

    drawJaggedBolt(canvas, startX, startY, targetX, targetY, p3 / 0.88, fade3, 53.0, camScale, shatter);

    // Stasis Barrier around the frozen tip of Bolt 3 (t = 2.45s .. 6.2s)
    const shieldAlpha = smoothstep(2.45, 2.80, t) * (1.0 - smoothstep(5.45, 6.25, t));
    if (shieldAlpha > 0.01) {
      const shR = (32 + 3 * Math.sin(t * 6.0)) * camScale;
      canvas.drawCircle(targetX, targetY, shR, [0.12, 0.65, 1.05], shieldAlpha * 0.20, 10 * camScale, 0.5, 0.3);
      canvas.drawArc(targetX, targetY, shR, 2.8 * camScale, 0, Math.PI * 2, [0.35, 1.05, 1.45], shieldAlpha * 0.88, 6 * camScale, 0.4);
    }
  }

  // --- 6. ACT II: BREATHING PACER HALO & AIRFLOW ---
  renderBreathingGuide(canvas, fig2, camScale, t);

  // --- 7. ACT III: THE GOLDEN ORB OF CARE & CO-REGULATION BRIDGE ---
  if (t >= 7.15) {
    const careAlpha = smoothstep(7.20, 7.85, t);
    const orbX = 0.5 * (fig2.handFront[0] + fig3.handFront[0]);
    const orbY = 0.5 * (fig2.handFront[1] + fig3.handFront[1]);
    const orbR = (16 + 3 * Math.sin(t * 4.0)) * camScale * careAlpha;

    canvas.drawCircle(orbX, orbY, orbR, [1.45, 1.08, 0.35], careAlpha * 0.85, 16 * camScale, 0.6, 0.5);
    drawHeartOrgan(canvas, orbX, orbY, orbR * 0.58, [1.65, 1.35, 0.55], careAlpha, 8 * camScale);

    const bridgePts23 = [];
    for (let i = 0; i <= 16; i++) {
      const u = i / 16;
      const bx = lerp(fig2.heartPos[0], fig3.heartPos[0], u);
      const by = lerp(fig2.heartPos[1], fig3.heartPos[1], u) - Math.sin(u * Math.PI) * 22 * camScale;
      bridgePts23.push([bx, by]);
    }
    canvas.drawPath(bridgePts23, 2.6 * camScale, [1.40, 1.02, 0.32], careAlpha * 0.85, 6 * camScale, 0.45);

    const heal1Alpha = smoothstep(7.45, 8.20, t);
    if (heal1Alpha > 0.01) {
      const bridgePts12 = [];
      for (let i = 0; i <= 20; i++) {
        const u = i / 20;
        const bx = lerp(fig2.heartPos[0], fig1.heartPos[0], u);
        const by = lerp(fig2.heartPos[1], fig1.heartPos[1], u) - Math.sin(u * Math.PI) * 32 * camScale;
        bridgePts12.push([bx, by]);
      }
      canvas.drawPath(bridgePts12, 2.4 * camScale, [1.30, 0.96, 0.30], heal1Alpha * 0.78, 6 * camScale, 0.40);
    }
  }

  // --- 8. CONTINUOUS LOWER AUTONOMIC WAVEFORM HUD ---
  renderAutonomicWaveform(canvas, t);

  // --- 9. RAZOR-SHARP LOWER-THIRD APHORISTIC CAPTIONS ---
  const cap1Alpha = smoothstep(0.10, 0.45, t) * (1.0 - smoothstep(2.40, 2.75, t));
  if (cap1Alpha > 0.01) {
    drawText(canvas, 'PAIN NOT TRANSFORMED IS TRANSMITTED', W * 0.5, 662, 18, [1.15, 0.65, 0.65], cap1Alpha, {
      align: 'center', tracking: 0.24, weight: 0.09, bgAlpha: 0.72, borderColor: [0.65, 0.18, 0.20]
    });
  }

  const cap2Alpha = smoothstep(2.75, 3.15, t) * (1.0 - smoothstep(6.95, 7.30, t));
  if (cap2Alpha > 0.01) {
    drawText(canvas, 'PAUSE · DOUBLE INHALE · LONG SLOW EXHALE', W * 0.5, 662, 18, [0.65, 1.15, 1.35], cap2Alpha, {
      align: 'center', tracking: 0.22, weight: 0.09, bgAlpha: 0.75, borderColor: [0.22, 0.68, 0.95]
    });
  }

  const cap3Alpha = smoothstep(7.25, 7.65, t);
  if (cap3Alpha > 0.01) {
    drawText(canvas, 'ONE BREATH BREAKS THE CHAIN · PASS ON CARE', W * 0.5, 662, 18, [1.25, 1.02, 0.52], cap3Alpha, {
      align: 'center', tracking: 0.22, weight: 0.09, bgAlpha: 0.75, borderColor: [0.85, 0.65, 0.22]
    });
  }
}

module.exports = { renderFrame };
