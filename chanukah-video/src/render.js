// usage: node render.js <dir> <out.mp4> [stillTimes,comma,separated]
const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const [dir, out, stills] = process.argv.slice(2);
const FPS = 30, DUR = 31.5;
(async () => {
  const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 } });
  await page.goto('file://' + path.resolve(dir, 'video.html'));
  await page.evaluate(() => window.ready);
  const grab = (t) => page.evaluate((t) => { render(t); return document.getElementById('c').toDataURL('image/jpeg', 0.93); }, t);
  if (stills) {
    for (const s of stills.split(',')) {
      const d = await grab(+s);
      fs.writeFileSync(path.join(out, `still_${s}.jpg`), Buffer.from(d.split(',')[1], 'base64'));
    }
    await browser.close(); return;
  }
  const ff = spawn('ffmpeg', ['-y', '-hide_banner', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(FPS), '-c:v', 'mjpeg', '-i', '-',
    '-i', path.join(dir, 'music.wav'), '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p',
    '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', '-shortest', out], { stdio: ['pipe', 'inherit', 'inherit'] });
  for (let f = 0; f < FPS * DUR; f++) {
    const d = await grab(f / FPS);
    if (!ff.stdin.write(Buffer.from(d.split(',')[1], 'base64'))) await new Promise(r => ff.stdin.once('drain', r));
  }
  ff.stdin.end();
  await new Promise(r => ff.on('close', r));
  await browser.close();
})();
