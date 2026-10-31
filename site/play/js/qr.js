// QR: drawing the delivery's code (qrcode-generator) and reading one (BarcodeDetector where the browser has it,
// jsQR from vendor/ where it does not, as on iOS). Both libraries are copied into vendor/, nothing is loaded from a CDN.
import qrcode from '../vendor/qrcode-generator.js';

// A <canvas> with the QR of `text`, or null when it does not fit (about 2.3 KB). `px` is the size of a module.
export function drawQr(text, px = 6) {
  let qr = null;
  for (const level of ['M', 'L']) {
    try {
      const q = qrcode(0, level);
      q.addData(text, 'Byte');
      q.make();
      qr = q;
      break;
    } catch (e) { /* too long for this level: try the lighter one */ }
  }
  if (!qr) return null;
  const n = qr.getModuleCount(), quiet = 4, size = (n + quiet * 2) * px;
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, size, size);
  ctx.fillStyle = '#000';
  for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (qr.isDark(r, c)) ctx.fillRect((c + quiet) * px, (r + quiet) * px, px, px);
  return canvas;
}

let jsqrLoading = null;
function loadJsQr() {
  if (window.jsQR) return Promise.resolve(window.jsQR);
  if (!jsqrLoading) {
    jsqrLoading = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = new URL('../vendor/jsQR.js', import.meta.url);
      s.onload = () => resolve(window.jsQR);
      s.onerror = () => { jsqrLoading = null; reject(new Error('jsQR')); };
      document.head.append(s);
    });
  }
  return jsqrLoading;
}

// The text of the QR in `imageData` (as canvas.getImageData gives it), or null. Always the jsQR path.
export async function decodeImageData(imageData) {
  const jsQR = await loadJsQr();
  const r = jsQR(imageData.data, imageData.width, imageData.height, { inversionAttempts: 'attemptBoth' });
  return r ? r.data : null;
}

let detector;
async function nativeDetector() {
  if (detector !== undefined) return detector;
  detector = null;
  try {
    if ('BarcodeDetector' in window) {
      const formats = await window.BarcodeDetector.getSupportedFormats();
      if (formats.includes('qr_code')) detector = new window.BarcodeDetector({ formats: ['qr_code'] });
    }
  } catch (e) { detector = null; }
  return detector;
}

// `source`: a <video>, <canvas>, <img> or ImageBitmap.
export async function decodeSource(source) {
  const d = await nativeDetector();
  if (d) {
    try {
      const found = await d.detect(source);
      if (found.length) return found[0].rawValue;
    } catch (e) { /* fall through to jsQR */ }
  }
  const w = source.videoWidth || source.naturalWidth || source.width, hgt = source.videoHeight || source.naturalHeight || source.height;
  if (!w || !hgt) return null;
  const canvas = document.createElement('canvas');
  canvas.width = w; canvas.height = hgt;
  const ctx = canvas.getContext('2d', { willReadFrequently: true });
  ctx.drawImage(source, 0, 0, w, hgt);
  return decodeImageData(ctx.getImageData(0, 0, w, hgt));
}

export async function decodeFile(file) {
  const bitmap = await createImageBitmap(file);
  try { return await decodeSource(bitmap); } finally { bitmap.close && bitmap.close(); }
}

// Opens the camera in `video` and calls onText(text) with the first QR it reads. Returns stop().
export async function scanCamera(video, onText) {
  const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' }, audio: false });
  video.srcObject = stream;
  video.setAttribute('playsinline', '');
  await video.play();
  let alive = true;
  const stop = () => { alive = false; stream.getTracks().forEach((tr) => tr.stop()); video.srcObject = null; };
  (async () => {
    while (alive) {
      try {
        const text = await decodeSource(video);
        if (text && alive) { onText(text); }
      } catch (e) { /* a frame that fails is just skipped */ }
      await new Promise((r) => setTimeout(r, 200));
    }
  })();
  return stop;
}
