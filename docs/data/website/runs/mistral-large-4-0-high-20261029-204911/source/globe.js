// Hero globe: a point-cloud Earth with arcs of "help" flowing toward regions of high need.
import * as THREE from 'three';

// Approximate lat/lon hubs in regions where cost-effective health programs operate.
const HUBS = [
  [1, 36], [6, 20], [-1, 36], [7, 78], [23, 90],
  [-13, 34], [3, 101], [-3, 23], [15, 77], [0, 135], [-8, 125], [11, 40],
];

function latLonToVec(lat, lon, r) {
  const phi = (90 - lat) * Math.PI / 180;
  const theta = (lon + 180) * Math.PI / 180;
  return new THREE.Vector3(
    -r * Math.sin(phi) * Math.cos(theta),
    r * Math.cos(phi),
    r * Math.sin(phi) * Math.sin(theta),
  );
}

export function initGlobe(canvas) {
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  } catch (e) {
    canvas.style.display = 'none';
    return;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 120);
  camera.position.set(0, 0, 3.1);

  const group = new THREE.Group();
  group.rotation.z = 0.15;
  group.rotation.x = 0.28;
  scene.add(group);

  // --- Earth point cloud (fibonacci sphere) ---
  const R = 1, N = 2400;
  const pos = new Float32Array(N * 3);
  const col = new Float32Array(N * 3);
  const cA = new THREE.Color(0x5f8fd6); // deep blue
  const cB = new THREE.Color(0xf2b544); // amber
  const tmp = new THREE.Color();
  for (let i = 0; i < N; i++) {
    const y = 1 - (i / (N - 1)) * 2;
    const rad = Math.sqrt(Math.max(0, 1 - y * y));
    const th = i * 2.399963;
    pos[i * 3] = Math.cos(th) * rad * R;
    pos[i * 3 + 1] = y * R;
    pos[i * 3 + 2] = Math.sin(th) * rad * R;
    const t = Math.pow((y + 1) / 2, 2.2) * 0.55;
    tmp.copy(cA).lerp(cB, t);
    col[i * 3] = tmp.r; col[i * 3 + 1] = tmp.g; col[i * 3 + 2] = tmp.b;
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  geo.setAttribute('color', new THREE.BufferAttribute(col, 3));
  const points = new THREE.Points(geo, new THREE.PointsMaterial({
    size: 0.013, vertexColors: true, transparent: true, opacity: 0.95, sizeAttenuation: true,
  }));
  group.add(points);

  // faint wireframe shell
  const wire = new THREE.Mesh(
    new THREE.SphereGeometry(R * 1.002, 48, 32),
    new THREE.MeshBasicMaterial({ color: 0x2a3d5c, wireframe: true, transparent: true, opacity: 0.10 }),
  );
  group.add(wire);

  // --- background stars ---
  const SN = 550, sp = new Float32Array(SN * 3);
  for (let i = 0; i < SN; i++) {
    const v = new THREE.Vector3().randomDirection().multiplyScalar(25 + Math.random() * 40);
    sp[i * 3] = v.x; sp[i * 3 + 1] = v.y; sp[i * 3 + 2] = v.z;
  }
  const sgeo = new THREE.BufferGeometry();
  sgeo.setAttribute('position', new THREE.BufferAttribute(sp, 3));
  scene.add(new THREE.Points(sgeo, new THREE.PointsMaterial({
    color: 0xbfd4ff, size: 0.06, transparent: true, opacity: 0.45, sizeAttenuation: true,
  })));

  // --- arcs: pulses traveling from random points toward need hubs ---
  const ARC_N = 20;
  const arcs = [];
  const dotGeo = new THREE.SphereGeometry(0.017, 8, 8);
  function makeArc() {
    const hub = HUBS[(Math.random() * HUBS.length) | 0];
    const a = latLonToVec(hub[0] + (Math.random() * 36 - 18), hub[1] + (Math.random() * 48 - 24), R * 1.02);
    const b = latLonToVec(Math.random() * 160 - 80, Math.random() * 360 - 180, R * 1.02);
    const segs = 56;
    const pts = [];
    for (let i = 0; i <= segs; i++) {
      const t = i / segs;
      const v = a.clone().lerp(b, t).normalize().multiplyScalar(R * 1.02 + Math.sin(t * Math.PI) * 0.14);
      pts.push(v);
    }
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(pts),
      new THREE.LineBasicMaterial({ color: 0xf2b544, transparent: true, opacity: 0.20 }),
    );
    const dot = new THREE.Mesh(dotGeo, new THREE.MeshBasicMaterial({ color: 0xffd98a }));
    group.add(line); group.add(dot);
    return { pts, line, dot, t: Math.random(), speed: 0.10 + Math.random() * 0.22 };
  }
  for (let i = 0; i < ARC_N; i++) arcs.push(makeArc());

  // --- sizing ---
  function resize() {
    const w = canvas.clientWidth || 1, h = canvas.clientHeight || 1;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  if (typeof ResizeObserver !== 'undefined') new ResizeObserver(resize).observe(canvas);
  window.addEventListener('resize', resize, { passive: true });

  // --- gentle pointer parallax ---
  let mx = 0, my = 0;
  window.addEventListener('pointermove', (e) => {
    mx = e.clientX / window.innerWidth - 0.5;
    my = e.clientY / window.innerHeight - 0.5;
  }, { passive: true });

  // --- render loop (static single frame if reduced motion) ---
  const reduced = typeof matchMedia !== 'undefined' && matchMedia('(prefers-reduced-motion: reduce)').matches;
  const clock = new THREE.Clock();
  let raf = 0;
  function frame() {
    const dt = Math.min(clock.getDelta(), 0.05);
    group.rotation.y += dt * 0.055 + mx * 0.0005;
    group.rotation.x += (0.28 + my * 0.18 - group.rotation.x) * 0.02;
    for (const a of arcs) {
      a.t += a.speed * dt;
      if (a.t > 1) a.t = 0;
      const p = a.pts[Math.min(a.pts.length - 1, Math.floor(a.t * a.pts.length))];
      a.dot.position.copy(p);
      a.dot.scale.setScalar(0.6 + 0.9 * Math.sin(a.t * Math.PI));
    }
    renderer.render(scene, camera);
    if (!reduced) raf = requestAnimationFrame(frame);
  }
  frame();
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) cancelAnimationFrame(raf);
    else if (!reduced) { clock.getDelta(); raf = requestAnimationFrame(frame); }
  });
}
