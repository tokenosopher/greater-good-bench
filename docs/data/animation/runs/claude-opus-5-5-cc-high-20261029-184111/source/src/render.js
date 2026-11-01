// Usage:
//   node src/render.js video out.mp4          -> 10 s, 30 fps H.264
//   node src/render.js stills dir t1 t2 ...   -> JPEG previews at given times
const { spawn } = require('child_process');
const path = require('path');
const { Canvas } = require('./raster');
const { W, H, drawFrame } = require('./scene');

const FPS = 30, SECONDS = 10;

function ffmpeg(args) {
  const p = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
    '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-', ...args], { stdio: ['pipe', 'inherit', 'inherit'] });
  const done = new Promise((res, rej) => p.on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
  return { p, done };
}

async function write(stream, buf) {
  if (!stream.write(buf)) await new Promise(r => stream.once('drain', r));
}

async function main() {
  const [mode, out, ...rest] = process.argv.slice(2);
  const cv = new Canvas(W, H);
  if (mode === 'video') {
    const { p, done } = ffmpeg(['-c:v', 'libx264', '-preset', 'veryslow', '-crf', '20', '-tune', 'animation',
      '-pix_fmt', 'yuv420p', '-movflags', '+faststart', out]);
    for (let f = 0; f < FPS * SECONDS; f++) {
      drawFrame(cv, f / FPS);
      await write(p.stdin, cv.toBytes());
      if (f % 30 === 0) process.stderr.write(`frame ${f}\n`);
    }
    p.stdin.end();
    await done;
  } else if (mode === 'stills') {
    for (const ts of rest) {
      const t = parseFloat(ts);
      drawFrame(cv, t);
      const { p, done } = ffmpeg(['-frames:v', '1', '-q:v', '3', path.join(out, `t${ts}.jpg`)]);
      await write(p.stdin, cv.toBytes());
      p.stdin.end();
      await done;
    }
  }
}

main().catch(e => { console.error(e); process.exit(1); });
