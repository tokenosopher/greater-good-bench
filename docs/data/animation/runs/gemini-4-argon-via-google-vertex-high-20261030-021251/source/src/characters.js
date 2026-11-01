'use strict';

/**
 * Articulated Human Figure & Inner Physiology (Lungs, Bronchi, Alveoli, Vagus Nerve, Heart)
 * Sculpted, warm, empathetic human silhouettes with high-contrast anatomical cutaway.
 */

function lerp(a, b, t) {
  return a + (b - a) * t;
}

function lerpColor(c1, c2, t) {
  return [
    lerp(c1[0], c2[0], t),
    lerp(c1[1], c2[1], t),
    lerp(c1[2], c2[2], t)
  ];
}

/**
 * Draw an organic glowing heart shape at (cx, cy) with scale r
 */
function drawHeartOrgan(canvas, cx, cy, r, color, alpha = 1.0, glow = 6.0) {
  canvas.drawCircle(cx - r * 0.28, cy - r * 0.18, r * 0.54, color, alpha, glow, 0.4, 0.2);
  canvas.drawCircle(cx + r * 0.28, cy - r * 0.18, r * 0.54, color, alpha, glow, 0.4, 0.2);
  canvas.drawCapsule(cx - r * 0.34, cy - r * 0.05, cx, cy + r * 0.66, r * 0.46, r * 0.12, color, alpha, glow * 0.35, 0.2);
  canvas.drawCapsule(cx + r * 0.34, cy - r * 0.05, cx, cy + r * 0.66, r * 0.46, r * 0.12, color, alpha, glow * 0.35, 0.2);
}

/**
 * Draw detailed anatomical lungs, trachea, bronchial tree, alveoli, and vagus nerve
 * inside a character's upper body with medical-illustration clarity.
 */
function drawDetailedPhysiology(canvas, joints, params) {
  const {
    scale = 1.0,
    facing = 1,
    lungFill = 0.2,      // 0..1 overall lung inflation
    alveoliPop = 0.0,    // 0..1 second-inhale alveolar recruitment flash
    vagusGlow = 0.0,     // 0..1 exhale parasympathetic vagal activation
    calmLevel = 0.0,     // 0..1 golden coherence
    detailAlpha = 1.0,
    time = 0.0
  } = params;

  if (detailAlpha <= 0.01) return;

  const { head, neck, chest, nose, shoulderCenter, pelvis } = joints;

  // 0. Deep dark anatomical cutaway inside the ribcage so internal structures have crisp contrast
  canvas.drawCapsule(
    shoulderCenter[0], shoulderCenter[1] + 5 * scale,
    pelvis[0], pelvis[1] - 10 * scale,
    22 * scale * (1.0 + 0.14 * lungFill),
    15 * scale,
    [0.015, 0.03, 0.07],
    0.88 * detailAlpha,
    2 * scale,
    0.0
  );

  // 1. Left & Right Lung Lobes separated clearly across the central mediastinum
  const expScale = 0.82 + 0.30 * lungFill;
  const lungW = 16.5 * scale * expScale;
  const lungH = 34 * scale * (0.84 + 0.26 * lungFill);

  const baseLungCol = lerpColor([0.04, 0.20, 0.38], [0.07, 0.38, 0.64], Math.min(1, lungFill * 1.1));
  const lungCol = lerpColor(baseLungCol, [0.10, 0.44, 0.42], vagusGlow * 0.6);

  const lCx = chest[0] - 14.5 * scale * expScale;
  const rCx = chest[0] + 14.5 * scale * expScale;
  const lCy = chest[1] - 3 * scale;

  const lobeAlpha = (0.65 + 0.25 * lungFill) * detailAlpha;
  // Left Lung Lobe
  canvas.drawCapsule(
    lCx + 2 * scale, lCy - lungH * 0.42,
    lCx - 3 * scale, lCy + lungH * 0.42,
    lungW * 0.42, lungW * 0.64,
    lungCol, lobeAlpha, 2 * scale, 0.0
  );
  // Right Lung Lobe
  canvas.drawCapsule(
    rCx - 2 * scale, lCy - lungH * 0.42,
    rCx + 3 * scale, lCy + lungH * 0.42,
    lungW * 0.42, lungW * 0.64,
    lungCol, lobeAlpha, 2 * scale, 0.0
  );

  // Diaphragm muscle arc beneath the lungs (contracts downward on inhale, relaxes upward on exhale)
  const diaphY = lCy + lungH * 0.58 + (lungFill - 0.3) * 6 * scale;
  const diaphCol = lerpColor([0.18, 0.65, 0.90], [1.10, 0.84, 0.28], vagusGlow);
  const diaphPts = [];
  for (let i = 0; i <= 14; i++) {
    const u = i / 14;
    const dx = lerp(lCx - lungW * 0.62, rCx + lungW * 0.62, u);
    const arch = Math.sin(u * Math.PI) * (9.5 - 5.5 * lungFill) * scale;
    diaphPts.push([dx, diaphY - arch]);
  }
  canvas.drawPath(diaphPts, 1.7 * scale, diaphCol, 0.85 * detailAlpha, 2 * scale, 0.1);

  // 2. Nasal Airway, Pharynx & Trachea
  const carina = [chest[0], chest[1] - 10 * scale];
  const throat = [neck[0] + facing * 1.5 * scale, neck[1]];
  const airwayCol = lerpColor([0.22, 0.72, 1.02], [0.48, 1.05, 1.35], lungFill);
  canvas.drawPath(
    [nose, [head[0] + facing * 2 * scale, head[1] + 5 * scale], throat, carina],
    (t) => (1.3 + t * 1.1) * scale,
    airwayCol,
    0.88 * detailAlpha,
    2 * scale,
    0.1
  );

  // 3. Delicate Bronchial Tree & Perimeter Alveolar Sacs (no central white blowout!)
  const branches = [
    // Left bronchial tree
    { start: carina, mid: [lCx + 3.5 * scale, lCy - 5 * scale], tips: [
      [lCx - 4 * scale, lCy - 16 * scale],
      [lCx - 10 * scale, lCy - 6 * scale],
      [lCx - 11 * scale, lCy + 7 * scale],
      [lCx - 4 * scale, lCy + 15 * scale]
    ]},
    // Right bronchial tree
    { start: carina, mid: [rCx - 3.5 * scale, lCy - 5 * scale], tips: [
      [rCx + 4 * scale, lCy - 16 * scale],
      [rCx + 10 * scale, lCy - 6 * scale],
      [rCx + 11 * scale, lCy + 7 * scale],
      [rCx + 4 * scale, lCy + 15 * scale]
    ]}
  ];

  const bronchAlpha = (0.60 + 0.35 * lungFill) * detailAlpha;
  for (const b of branches) {
    canvas.drawCapsule(b.start[0], b.start[1], b.mid[0], b.mid[1], 1.8 * scale, 1.3 * scale, airwayCol, bronchAlpha, 1 * scale, 0.0);
    for (let i = 0; i < b.tips.length; i++) {
      const tip = b.tips[i];
      canvas.drawCapsule(b.mid[0], b.mid[1], tip[0], tip[1], 1.2 * scale, 0.75 * scale, airwayCol, bronchAlpha, 1 * scale, 0.0);

      // Crisp alveolar pearl at each bronchiole tip (flares during 2nd top-up inhale!)
      const alvR = (1.5 + 0.9 * lungFill + 1.3 * alveoliPop) * scale;
      const alvCol = lerpColor([0.28, 0.85, 1.15], [0.85, 1.35, 1.55], alveoliPop);
      const alvAlpha = (0.60 + 0.40 * Math.max(lungFill, alveoliPop)) * detailAlpha;
      canvas.drawCircle(tip[0], tip[1], alvR, alvCol, alvAlpha, (1.5 + 3.5 * alveoliPop) * scale, 0.35, 0.15);
    }
  }

  // 4. Brainstem & Vagus Nerve (Cranial Nerve X) descending from Brain -> Heart -> Diaphragm
  const brainPos = [head[0] - facing * 2 * scale, head[1] - 2 * scale];
  const heartPos = [chest[0] + 1.5 * scale, chest[1] + 5 * scale];
  const vagusCol = lerpColor([0.28, 0.65, 0.85], [1.35, 1.00, 0.25], Math.min(1, vagusGlow + calmLevel));
  const vagusAlpha = (0.50 + 0.50 * Math.max(vagusGlow, calmLevel * 0.8)) * detailAlpha;

  const vagusPath = [
    brainPos,
    [neck[0] - facing * 3 * scale, neck[1]],
    [chest[0] - facing * 3.5 * scale, chest[1] - 5 * scale],
    heartPos,
    [chest[0], diaphY - 2 * scale]
  ];
  canvas.drawPath(vagusPath, (1.3 + 0.9 * vagusGlow) * scale, vagusCol, vagusAlpha, (2 + 4 * vagusGlow) * scale, 0.25);

  if (vagusGlow > 0.05) {
    for (let p = 0; p < 3; p++) {
      const u = ((time * 0.85 + p * 0.33) % 1.0);
      const seg = u * (vagusPath.length - 1);
      const idx = Math.min(vagusPath.length - 2, Math.floor(seg));
      const frac = seg - idx;
      const px = lerp(vagusPath[idx][0], vagusPath[idx + 1][0], frac);
      const py = lerp(vagusPath[idx][1], vagusPath[idx + 1][1], frac);
      canvas.drawCircle(px, py, 2.5 * scale, [1.40, 1.10, 0.35], vagusGlow * detailAlpha, 4 * scale, 0.5, 0.35);
    }
  }

  canvas.drawCircle(brainPos[0], brainPos[1] - 2 * scale, 4.5 * scale, vagusCol, 0.60 * vagusAlpha, 4 * scale, 0.3, 0.2);
}

/**
 * Render an articulated human figure with warm sculptural silhouette and inner physiology.
 */
function drawHumanFigure(canvas, pose, style) {
  const {
    x, y,
    scale = 1.0,
    facing = 1,
    spineLean = 0.0,
    crouch = 0.0,
    headTilt = 0.0,
    armL = { shoulderAngle: 0.3, elbowAngle: 0.5 },
    armR = { shoulderAngle: -0.3, elbowAngle: -0.4 },
    stress = 0.0,
    calm = 0.0,
    breath = 0.2,
    alveoliPop = 0.0,
    vagusGlow = 0.0,
    showAnatomy = 0.0,
    time = 0.0,
    alpha = 1.0
  } = { ...pose, ...style };

  if (alpha <= 0.01) return null;

  const crouchDrop = crouch * 44 * scale;
  const pelvis = [
    x - Math.sin(spineLean) * 8 * scale,
    y - (94 * scale - crouchDrop)
  ];

  const torsoLen = 70 * scale;
  const chest = [
    pelvis[0] + Math.sin(spineLean) * torsoLen * 0.66,
    pelvis[1] - Math.cos(spineLean) * torsoLen * 0.66
  ];
  const shoulderCenter = [
    pelvis[0] + Math.sin(spineLean) * torsoLen,
    pelvis[1] - Math.cos(spineLean) * torsoLen
  ];
  const neck = [
    shoulderCenter[0] + Math.sin(spineLean * 0.8) * 15 * scale,
    shoulderCenter[1] - Math.cos(spineLean * 0.8) * 15 * scale
  ];
  const headAngle = spineLean * 0.6 + headTilt;
  const head = [
    neck[0] + Math.sin(headAngle) * 18 * scale,
    neck[1] - Math.cos(headAngle) * 18 * scale
  ];
  const nose = [
    head[0] + facing * Math.cos(headAngle * 0.5) * 14.8 * scale,
    head[1] + Math.sin(headAngle * 0.5) * 3 * scale + 1.5 * scale
  ];
  const mouth = [
    head[0] + facing * Math.cos(headAngle * 0.5) * 13.5 * scale,
    head[1] + Math.sin(headAngle * 0.5) * 3 * scale + 7.5 * scale
  ];

  // Legs
  const footBack = [x - facing * (16 + crouch * 18) * scale, y];
  const footFront = [x + facing * (18 + crouch * 12) * scale, y];

  const kneeBack = [
    lerp(pelvis[0] - facing * 8 * scale, footBack[0] + facing * 18 * scale, 0.52) + facing * crouch * 18 * scale,
    lerp(pelvis[1], footBack[1], 0.52 + crouch * 0.34)
  ];
  const kneeFront = [
    lerp(pelvis[0] + facing * 8 * scale, footFront[0], 0.5) + facing * crouch * 24 * scale,
    lerp(pelvis[1], footFront[1], 0.5 - crouch * 0.08)
  ];

  // Arms
  const upperArmLen = 40 * scale;
  const foreArmLen = 38 * scale;

  const shBack = [shoulderCenter[0] - facing * 8 * scale, shoulderCenter[1] + 4 * scale];
  const elBack = [
    shBack[0] + facing * Math.sin(armL.shoulderAngle) * upperArmLen,
    shBack[1] + Math.cos(armL.shoulderAngle) * upperArmLen
  ];
  const handBack = [
    elBack[0] + facing * Math.sin(armL.shoulderAngle + armL.elbowAngle) * foreArmLen,
    elBack[1] + Math.cos(armL.shoulderAngle + armL.elbowAngle) * foreArmLen
  ];

  const shFront = [shoulderCenter[0] + facing * 6 * scale, shoulderCenter[1] + 4 * scale];
  const elFront = [
    shFront[0] + facing * Math.sin(armR.shoulderAngle) * upperArmLen,
    shFront[1] + Math.cos(armR.shoulderAngle) * upperArmLen
  ];
  const handFront = [
    elFront[0] + facing * Math.sin(armR.shoulderAngle + armR.elbowAngle) * foreArmLen,
    elFront[1] + Math.cos(armR.shoulderAngle + armR.elbowAngle) * foreArmLen
  ];

  // Palette
  const baseBody = lerpColor([0.09, 0.16, 0.27], [0.26, 0.07, 0.10], stress * 0.75);
  const bodyCol = lerpColor(baseBody, [0.10, 0.23, 0.31], calm * 0.85);
  const backLimbCol = [bodyCol[0] * 0.72, bodyCol[1] * 0.72, bodyCol[2] * 0.75];

  const baseRim = lerpColor([0.26, 0.52, 0.80], [1.10, 0.18, 0.16], stress);
  const rimCol = lerpColor(baseRim, [1.15, 0.86, 0.34], calm);

  const bodyAlpha = 0.94 * alpha;
  const chestExpand = (1.0 + 0.12 * breath) * scale;

  // --- 0. UNIFIED OUTER RIM AURA (drawn BEFORE body fill so there are no internal seams!) ---
  canvas.drawCapsule(shoulderCenter[0], shoulderCenter[1], pelvis[0], pelvis[1], 24.5 * chestExpand, 17 * scale, rimCol, 0.65 * alpha, 5 * scale, 0.2);
  canvas.drawCapsule(shoulderCenter[0], shoulderCenter[1], head[0], head[1], 10 * scale, 16.2 * scale, rimCol, 0.65 * alpha, 5 * scale, 0.2);
  const chin = [head[0] + facing * 6.0 * scale, head[1] + 9.5 * scale];
  canvas.drawCapsule(head[0] + facing * 2 * scale, head[1] + 1 * scale, chin[0], chin[1], 13 * scale, 8.0 * scale, rimCol, 0.60 * alpha, 4 * scale, 0.2);
  const frontArmAlpha = (1.0 - 0.65 * showAnatomy) * bodyAlpha;
  canvas.drawCapsule(shFront[0], shFront[1], elFront[0], elFront[1], 10.2 * scale, 8.0 * scale, rimCol, 0.50 * frontArmAlpha, 3 * scale, 0.15);
  canvas.drawCapsule(elFront[0], elFront[1], handFront[0], handFront[1], 8.0 * scale, 5.6 * scale, rimCol, 0.50 * frontArmAlpha, 3 * scale, 0.15);

  // --- 1. BACK LIMBS ---
  canvas.drawCapsule(pelvis[0] - facing * 5 * scale, pelvis[1], kneeBack[0], kneeBack[1], 12.5 * scale, 9 * scale, backLimbCol, bodyAlpha, 1 * scale);
  canvas.drawCapsule(kneeBack[0], kneeBack[1], footBack[0], footBack[1], 9 * scale, 5.8 * scale, backLimbCol, bodyAlpha, 1 * scale);
  canvas.drawCapsule(footBack[0], footBack[1], footBack[0] + facing * 12 * scale, footBack[1], 5.8 * scale, 4.2 * scale, backLimbCol, bodyAlpha);

  canvas.drawCapsule(shBack[0], shBack[1], elBack[0], elBack[1], 9 * scale, 7.2 * scale, backLimbCol, bodyAlpha, 2 * scale);
  canvas.drawCapsule(elBack[0], elBack[1], handBack[0], handBack[1], 7.2 * scale, 5.0 * scale, backLimbCol, bodyAlpha, 2 * scale);
  canvas.drawCircle(handBack[0], handBack[1], 5.2 * scale, rimCol, 0.55 * alpha, 3 * scale, 0.3, 0.15);

  // --- 2. SEAMLESS TORSO, NECK & HEAD SILHOUETTE ---
  canvas.drawCapsule(shoulderCenter[0], shoulderCenter[1], chest[0], chest[1], 22.0 * chestExpand, 20.0 * chestExpand, bodyCol, bodyAlpha, 1 * scale);
  canvas.drawCapsule(chest[0], chest[1], pelvis[0], pelvis[1], 20.0 * chestExpand, 15.2 * scale, bodyCol, bodyAlpha, 1 * scale);
  canvas.drawCapsule(shoulderCenter[0], shoulderCenter[1], head[0], head[1], 8.5 * scale, 14.8 * scale, bodyCol, bodyAlpha, 1 * scale);
  canvas.drawCapsule(head[0] + facing * 2 * scale, head[1] + 1 * scale, chin[0], chin[1], 11.8 * scale, 7.0 * scale, bodyCol, bodyAlpha, 1 * scale);

  // Subtle eye light
  const eyePos = [head[0] + facing * 9.0 * scale, head[1] - 1.5 * scale];
  const eyeCol = lerpColor([0.65, 0.88, 1.15], [1.25, 1.05, 0.55], calm);
  canvas.drawCircle(eyePos[0], eyePos[1], 1.9 * scale, eyeCol, 0.85 * alpha, 2 * scale, 0.3, 0.2);

  // --- 3. INNER PHYSIOLOGY ---
  const joints = { head, neck, chest, pelvis, nose, mouth, shoulderCenter, handFront, handBack };

  if (showAnatomy > 0.01) {
    drawDetailedPhysiology(canvas, joints, {
      scale,
      facing,
      lungFill: breath,
      alveoliPop,
      vagusGlow,
      stressLevel: stress,
      calmLevel: calm,
      detailAlpha: showAnatomy * alpha,
      time
    });
  }

  // --- 4. FRONT LIMBS ---
  canvas.drawCapsule(pelvis[0] + facing * 5 * scale, pelvis[1], kneeFront[0], kneeFront[1], 13 * scale, 9.5 * scale, bodyCol, bodyAlpha, 1 * scale);
  canvas.drawCapsule(kneeFront[0], kneeFront[1], footFront[0], footFront[1], 9.5 * scale, 6.0 * scale, bodyCol, bodyAlpha, 1 * scale);
  canvas.drawCapsule(footFront[0], footFront[1], footFront[0] + facing * 13 * scale, footFront[1], 6.0 * scale, 4.5 * scale, bodyCol, bodyAlpha);

  canvas.drawCapsule(shFront[0], shFront[1], elFront[0], elFront[1], 9.0 * scale, 7.0 * scale, bodyCol, frontArmAlpha, 1 * scale);
  canvas.drawCapsule(elFront[0], elFront[1], handFront[0], handFront[1], 7.0 * scale, 4.8 * scale, bodyCol, frontArmAlpha, 1 * scale);
  canvas.drawCircle(handFront[0], handFront[1], 5.5 * scale, rimCol, 0.75 * frontArmAlpha, 4 * scale, 0.3, 0.2);

  // --- 5. HEART ORGAN (drawn last so it always glows visibly inside the chest) ---
  const heartRateFreq = lerp(1.2, 3.4, stress);
  const beatPulse = 1.0 + (0.12 + 0.14 * stress) * Math.pow(Math.max(0, Math.sin(time * Math.PI * 2 * heartRateFreq)), 3);
  const heartR = 7.8 * scale * beatPulse;
  const heartBaseCol = lerpColor([0.32, 0.82, 1.18], [1.55, 0.20, 0.18], stress);
  const heartCol = lerpColor(heartBaseCol, [1.50, 1.10, 0.32], calm);
  const heartPos = [chest[0] + facing * 2.0 * scale, chest[1] + 5 * scale];

  drawHeartOrgan(canvas, heartPos[0], heartPos[1], heartR, heartCol, 0.95 * alpha, 6 * scale);

  return { ...joints, heartPos };
}

module.exports = { drawHumanFigure, drawHeartOrgan, lerp, lerpColor };
