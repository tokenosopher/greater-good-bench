'use strict';

const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { HDRCanvas } = require('./renderer');
const { renderFrame } = require('./scene');
const { generateAudioWav } = require('./audio');

const WIDTH = 1280;
const HEIGHT = 720;
const FPS = 30;
const DURATION = 10.0;
const TOTAL_FRAMES = Math.round( FPS * DURATION );

async function main() {
  const startTime = Date.now();
  const outDir = path.join(__dirname, '..', 'output');
  fs.mkdirSync(outDir, { recursive: true });

  const wavPath = path.join(__dirname, '..', 'temp_audio.wav');
  const mp4Path = path.join(outDir, 'break_the_chain.mp4');

  console.log('1. Generating synchronized stereo audio track...');
  generateAudioWav(wavPath, DURATION, 44100);

  console.log(`2. Rendering ${TOTAL_FRAMES} HDR frames (${WIDTH}x${HEIGHT} @ ${FPS}fps)...`);
  const ffmpeg = spawn('ffmpeg', [
    '-y',
    '-loglevel', 'error',
    '-f', 'rawvideo',
    '-pix_fmt', 'rgb24',
    '-s', `${WIDTH}x${HEIGHT}`,
    '-r', String(FPS),
    '-i', 'pipe:0',
    '-i', wavPath,
    '-c:v', 'libx264',
    '-preset', 'slow',
    '-crf', '22',
    '-maxrate', '1250k',
    '-bufsize', '2500k',
    '-pix_fmt', 'yuv420p',
    '-c:a', 'aac',
    '-b:a', '128k',
    '-shortest',
    '-movflags', '+faststart',
    mp4Path
  ]);

  ffmpeg.stderr.on('data', (d) => process.stderr.write(d));

  const canvas = new HDRCanvas(WIDTH, HEIGHT);

  for (let frame = 0; frame < TOTAL_FRAMES; frame++) {
    const t = frame / FPS;
    renderFrame(canvas, t);
    const rgb = canvas.toSRGB();
    const buf = Buffer.from(rgb.buffer, rgb.byteOffset, rgb.byteLength);
    if (!ffmpeg.stdin.write(buf)) {
      await new Promise((resolve) => ffmpeg.stdin.once('drain', resolve));
    }
    if ((frame + 1) % 50 === 0 || frame === TOTAL_FRAMES - 1) {
      console.log(`   Rendered frame ${frame + 1} / ${TOTAL_FRAMES} (t = ${t.toFixed(2)}s)`);
    }
  }

  ffmpeg.stdin.end();
  await new Promise((resolve, reject) => {
    ffmpeg.on('close', (code) => (code === 0 ? resolve() : reject(new Error(`ffmpeg exited ${code}`))));
  });

  if (fs.existsSync(wavPath)) {
    fs.unlinkSync(wavPath);
  }

  const stat = fs.statSync(mp4Path);
  console.log(`Done in ${((Date.now() - startTime) / 1000).toFixed(2)}s! Output: ${mp4Path} (${(stat.size / 1024).toFixed(1)} KB)`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
