const puppeteer = require('puppeteer-core');
const http = require('http');
const fs = require('fs');
const path = require('path');

const args = process.argv.slice(2);
const isPreview = args.includes('--preview');
const getArg = (name, def) => {
  const idx = args.indexOf(name);
  return idx !== -1 && args[idx + 1] ? args[idx + 1] : def;
};

const startFrame = parseInt(getArg('--start', '0'), 10);
const endFrame = parseInt(getArg('--end', '599'), 10);
const assetDir = path.resolve(getArg('--assets', '/var/tmp/rome_ai_3d'));
const outDir = path.resolve(getArg('--out', isPreview ? '/var/tmp/rome_ai_3d_preview' : '/var/tmp/rome_ai_3d_frames'));
const clientJsPath = path.resolve(getArg('--client', path.join(__dirname, 'rome_ai_3d_client.js')));
const threeDir = path.resolve(getArg('--three', path.join(__dirname, 'node_modules/three/build')));

fs.mkdirSync(outDir, { recursive: true });

const server = http.createServer((req, res) => {
  if (req.url === '/') {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(`<!DOCTYPE html><html><head><meta charset="utf-8">
    <style>body{margin:0;overflow:hidden;background:#000;}canvas{display:none;}</style>
    </head><body>
    <canvas id="glCanvas" width="1920" height="1080"></canvas>
    <canvas id="hudCanvas" width="1920" height="1080"></canvas>
    <canvas id="outCanvas" width="1920" height="1080"></canvas>
    <script type="module">
      import * as THREE from '/three.module.js';
      window.THREE = THREE;
      const s = document.createElement('script');
      s.src = '/client.js';
      s.onload = async () => {
        await window.initRomeAI3D();
        window.__READY = true;
      };
      document.body.appendChild(s);
    </script>
    </body></html>`);
  } else if (req.url === '/three.module.js' || req.url === '/three.core.js') {
    res.writeHead(200, { 'Content-Type': 'application/javascript' });
    res.end(fs.readFileSync(path.join(threeDir, path.basename(req.url))));
  } else if (req.url === '/client.js') {
    res.writeHead(200, { 'Content-Type': 'application/javascript' });
    res.end(fs.readFileSync(clientJsPath));
  } else if (req.url.startsWith('/ai3d/')) {
    const fname = path.basename(req.url);
    const fpath = path.join(assetDir, fname);
    if (fs.existsSync(fpath)) {
      res.writeHead(200, { 'Content-Type': fname.endsWith('.png') ? 'image/png' : 'image/jpeg' });
      res.end(fs.readFileSync(fpath));
    } else {
      res.writeHead(404); res.end();
    }
  } else {
    res.writeHead(204); res.end();
  }
});

(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const port = server.address().port;
  const chromeCandidates = [
    process.env.CHROME_BIN,
    '/usr/bin/google-chrome',
    '/usr/bin/google-chrome-stable',
    '/usr/bin/chromium',
    '/usr/bin/chromium-browser'
  ].filter(Boolean);
  const execPath = chromeCandidates.find(p => fs.existsSync(p));
  const browser = await puppeteer.launch({
    executablePath: execPath,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--enable-webgl', '--ignore-gpu-blocklist', '--use-gl=angle', '--use-angle=swiftshader-webgl', '--window-size=1920,1080']
  });
  const page = await browser.newPage();
  page.on('pageerror', err => console.error('ERR:', err.toString()));
  await page.setViewport({ width: 1920, height: 1080, deviceScaleFactor: 1 });
  await page.goto(`http://127.0.0.1:${port}/`, { waitUntil: 'networkidle0' });
  await page.waitForFunction('window.__READY === true', { timeout: 30000 });

  if (isPreview) {
    const previewTimes = [0.8, 2.8, 4.8, 7.0, 8.8, 11.0, 12.8, 15.0, 16.8, 19.2];
    for (let i = 0; i < previewTimes.length; i++) {
      const t = previewTimes[i];
      const dataUrl = await page.evaluate(t => window.renderFrameAt(t), t);
      const b64 = dataUrl.split(',')[1];
      fs.writeFileSync(path.join(outDir, `p_${String(i).padStart(2, '0')}.jpg`), Buffer.from(b64, 'base64'));
    }
    console.log('Rendered 10 AI-3D preview frames!');
  } else {
    const fps = 30;
    for (let f = startFrame; f <= endFrame; f++) {
      const t = f / fps;
      const dataUrl = await page.evaluate(t => window.renderFrameAt(t), t);
      const b64 = dataUrl.split(',')[1];
      fs.writeFileSync(path.join(outDir, `frame_${String(f).padStart(4, '0')}.jpg`), Buffer.from(b64, 'base64'));
      if ((f - startFrame) % 10 === 0 || f === endFrame) {
        console.log(`Rendered frame ${f} (${startFrame}..${endFrame})`);
      }
    }
  }
  await browser.close();
  server.close();
})();
