/* ph-cam.js: PhotoHunt's browser engines. Python reaches them through client_code/ph.py.
     camera      PH.camStart(video, facing) / PH.camStop() / PH.camSnap(video) -> {blob, url, sig}
     photos      PH.fromFile(file) -> {blob, url, sig}: shrinks to 1024 px JPEG and fingerprints it
     fingerprint PH.sig64(rgba) on a 64x64 picture (Vision.py on the server compares two of them)
     QR codes    PH.scanStart(video, onText) / PH.scanStop(): BarcodeDetector, else jsQR (ph-qrscan.js, loaded on demand)
     voice       PH.recStart(onLevel) / PH.recStop() -> {blob, seconds, url}; PH.playUrl(url, onEnd); PH.say(text, onEnd)
     party       PH.sfx(name), PH.confetti(), PH.blowStart(onLevel, onBlown) / PH.blowStop(), PH.countdown(n, onDone),
                 PH.banner(text) (the big BINGO!)
   Every function returns a Promise or plain values with primitives, so Python can await it (anvil.js). */
(function () {
  'use strict';
  var PH = window.PH = window.PH || {};
  var reduced = function () { return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; };

  /* ---------------------------------------------------------------- fingerprint */
  // rgba: 64*64*4 values (Uint8ClampedArray or plain array) of the middle 80% of a photo, scaled down.
  PH.sig64 = function (rgba) {
    var N = 64, i, x, y;
    var lum = new Float32Array(N * N), colour = new Float64Array(20);
    for (y = 0; y < N; y++) for (x = 0; x < N; x++) {
      i = (y * N + x) * 4;
      var r = rgba[i] / 255, g = rgba[i + 1] / 255, b = rgba[i + 2] / 255;
      lum[y * N + x] = 0.299 * r + 0.587 * g + 0.114 * b;
      var mx = Math.max(r, g, b), mn = Math.min(r, g, b), v = mx, s = mx ? (mx - mn) / mx : 0, h = 0;
      if (mx !== mn) {
        if (mx === r) h = ((g - b) / (mx - mn) + 6) % 6; else if (mx === g) h = (b - r) / (mx - mn) + 2; else h = (r - g) / (mx - mn) + 4;
        h *= 60;
      }
      var dx = (x - 31.5) / 32, dy = (y - 31.5) / 32, w = Math.exp(-(dx * dx + dy * dy) / (2 * 0.45 * 0.45));
      var bin = (s < 0.2 || v < 0.15) ? 16 + Math.min(3, Math.floor(v * 4)) : Math.floor(h / 45) % 8 * 2 + (s < 0.55 ? 0 : 1);
      colour[bin] += w;
    }
    var cs = 0; for (i = 0; i < 20; i++) cs += colour[i];
    var c = []; for (i = 0; i < 20; i++) c.push(cs ? colour[i] / cs : 0.05);
    // edges: 32x32 grey copy, Sobel, 8 directions in 4x4 cells
    var M = 32, g2 = new Float32Array(M * M);
    for (y = 0; y < M; y++) for (x = 0; x < M; x++) {
      g2[y * M + x] = (lum[(2 * y) * N + 2 * x] + lum[(2 * y) * N + 2 * x + 1] + lum[(2 * y + 1) * N + 2 * x] + lum[(2 * y + 1) * N + 2 * x + 1]) / 4;
    }
    var e = new Float64Array(128);
    for (y = 1; y < M - 1; y++) for (x = 1; x < M - 1; x++) {
      var p = function (xx, yy) { return g2[yy * M + xx]; };
      var gx = p(x + 1, y - 1) + 2 * p(x + 1, y) + p(x + 1, y + 1) - p(x - 1, y - 1) - 2 * p(x - 1, y) - p(x - 1, y + 1);
      var gy = p(x - 1, y + 1) + 2 * p(x, y + 1) + p(x + 1, y + 1) - p(x - 1, y - 1) - 2 * p(x, y - 1) - p(x + 1, y - 1);
      var mag = Math.sqrt(gx * gx + gy * gy);
      if (mag < 0.02) continue;
      var ang = Math.atan2(gy, gx); if (ang < 0) ang += Math.PI;
      var ob = Math.min(7, Math.floor(ang / Math.PI * 8)), cell = Math.floor(y / 8) * 4 + Math.floor(x / 8);
      e[cell * 8 + ob] += mag;
    }
    var en = 0; for (i = 0; i < 128; i++) en += e[i] * e[i];
    en = Math.sqrt(en) || 1;
    var ev = []; for (i = 0; i < 128; i++) ev.push(e[i] / en);
    // layout: 8x8 brightness, zero mean, unit spread
    var l = [], sum = 0;
    for (y = 0; y < 8; y++) for (x = 0; x < 8; x++) {
      var acc = 0;
      for (var yy = 0; yy < 8; yy++) for (var xx = 0; xx < 8; xx++) acc += lum[(y * 8 + yy) * N + x * 8 + xx];
      l.push(acc / 64); sum += acc / 64;
    }
    var mean = sum / 64, sd = 0;
    for (i = 0; i < 64; i++) { l[i] -= mean; sd += l[i] * l[i]; }
    sd = Math.sqrt(sd / 64) || 1;
    for (i = 0; i < 64; i++) l[i] = l[i] / sd;
    var r5 = function (v) { return Math.round(v * 100000) / 100000; };
    return { v: 1, c: c.map(r5), e: ev.map(r5), l: l.map(r5) };
  };

  function sigOf(source, sw, sh) {
    var cv = document.createElement('canvas'); cv.width = 64; cv.height = 64;
    var ctx = cv.getContext('2d');
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(source, sw * 0.1, sh * 0.1, sw * 0.8, sh * 0.8, 0, 0, 64, 64);
    return PH.sig64(ctx.getImageData(0, 0, 64, 64).data);
  }

  function finish(source, sw, sh) {
    var scale = Math.min(1, 1024 / Math.max(sw, sh));
    var cv = document.createElement('canvas');
    cv.width = Math.round(sw * scale); cv.height = Math.round(sh * scale);
    var ctx = cv.getContext('2d');
    ctx.imageSmoothingEnabled = true; ctx.imageSmoothingQuality = 'high';
    ctx.drawImage(source, 0, 0, cv.width, cv.height);
    var sig = sigOf(cv, cv.width, cv.height);
    return new Promise(function (res, rej) {
      cv.toBlob(function (blob) {
        if (!blob) { rej(new Error('Could not make the picture')); return; }
        res({ blob: blob, url: URL.createObjectURL(blob), sig: JSON.stringify(sig) });
      }, 'image/jpeg', 0.82);
    });
  }

  PH.fromFile = function (file) {
    return new Promise(function (res, rej) {
      var img = new Image(), url = URL.createObjectURL(file);
      img.onload = function () { finish(img, img.naturalWidth, img.naturalHeight).then(res, rej); URL.revokeObjectURL(url); };
      img.onerror = function () { rej(new Error('That file is not a picture we can read.')); };
      img.src = url;
    });
  };
  PH.fromInput = function (input) {   // the first file of an <input type=file>, or null
    var f = input && input.files && input.files[0];
    return f ? PH.fromFile(f) : Promise.resolve(null);
  };
  PH.fromUrl = function (src) {   // demo art and saved photos (same origin)
    return new Promise(function (res, rej) {
      var img = new Image();
      img.onload = function () { finish(img, img.naturalWidth || 600, img.naturalHeight || 600).then(res, rej); };
      img.onerror = function () { rej(new Error('Could not load the picture')); };
      img.src = src;
    });
  };

  /* ---------------------------------------------------------------- camera */
  var cam = { stream: null };
  PH.camOk = function () { return !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia); };
  PH.camStart = function (video, facing) {
    PH.camStop();
    if (!PH.camOk()) return Promise.reject(new Error('This browser has no camera access. Use "Choose a photo" instead.'));
    return navigator.mediaDevices.getUserMedia({ audio: false, video: { facingMode: { ideal: facing || 'environment' }, width: { ideal: 1280 }, height: { ideal: 960 } } })
      .then(function (stream) {
        cam.stream = stream;
        video.srcObject = stream; video.muted = true; video.setAttribute('playsinline', '');
        return video.play().then(function () { return true; });
      })
      .catch(function (e) {
        var why = (e && e.name === 'NotAllowedError') ? 'The camera is blocked. Allow it in the browser, or use "Choose a photo".' :
                  (e && e.name === 'NotFoundError') ? 'No camera was found. Use "Choose a photo" instead.' : 'The camera did not start. Try "Choose a photo".';
        throw new Error(why);
      });
  };
  PH.camStop = function () {
    if (cam.stream) { cam.stream.getTracks().forEach(function (t) { t.stop(); }); cam.stream = null; }
  };
  PH.camSnap = function (video) {
    var w = video.videoWidth || 640, h = video.videoHeight || 480;
    return finish(video, w, h);
  };

  /* ---------------------------------------------------------------- QR scanning */
  var scan = { timer: null, busy: false };
  function loadScanner() {
    if (window.jsQR) return Promise.resolve();
    var src = (document.querySelector('meta[name="ph-qrscan"]') || {}).content || '_/theme/ph-qrscan.js';
    return new Promise(function (res, rej) {
      var s = document.createElement('script'); s.src = src; s.onload = res; s.onerror = function () { rej(new Error('The scanner did not load')); };
      document.head.appendChild(s);
    });
  }
  PH.decodeCanvas = function (cv) {  // tests use it on a drawn QR code
    var d = cv.getContext('2d').getImageData(0, 0, cv.width, cv.height);
    var hit = window.jsQR && window.jsQR(d.data, d.width, d.height, { inversionAttempts: 'dontInvert' });
    return hit ? hit.data : null;
  };
  PH.scanStart = function (video, onText) {
    PH.scanStop();
    var detector = null;
    try { if ('BarcodeDetector' in window) detector = new window.BarcodeDetector({ formats: ['qr_code'] }); } catch (e) { detector = null; }
    var ready = detector ? Promise.resolve() : loadScanner();
    return PH.camStart(video, 'environment').then(function () { return ready; }).then(function () {
      var cv = document.createElement('canvas');
      scan.timer = setInterval(function () {
        if (scan.busy || !video.videoWidth) return;
        scan.busy = true;
        var done = function (text) { scan.busy = false; if (text && scan.timer) { PH.scanStop(); onText(text); } };
        if (detector) {
          detector.detect(video).then(function (codes) { done(codes && codes[0] && codes[0].rawValue); }, function () { done(null); });
        } else {
          var w = Math.min(640, video.videoWidth), h = Math.round(video.videoHeight * w / video.videoWidth);
          cv.width = w; cv.height = h; cv.getContext('2d').drawImage(video, 0, 0, w, h);
          done(PH.decodeCanvas(cv));
        }
      }, 250);
      return true;
    });
  };
  PH.scanStop = function () { if (scan.timer) clearInterval(scan.timer); scan.timer = null; scan.busy = false; PH.camStop(); };

  /* ---------------------------------------------------------------- voice recording and playback */
  var rec = { r: null, chunks: [], t0: 0, stream: null, raf: 0, resolve: null, timer: null };
  function pickType() {
    var types = ['audio/mp4;codecs=mp4a.40.2', 'audio/mp4', 'audio/webm;codecs=opus', 'audio/webm'];
    for (var i = 0; i < types.length; i++) if (window.MediaRecorder && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(types[i])) return types[i];
    return '';
  }
  PH.recOk = function () { return !!(window.MediaRecorder && navigator.mediaDevices && navigator.mediaDevices.getUserMedia); };
  PH.recStart = function (onLevel, maxSeconds) {
    PH.stopSound();
    if (!PH.recOk()) return Promise.reject(new Error('This browser cannot record sound.'));
    return navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } }).then(function (stream) {
      rec.stream = stream; rec.chunks = [];
      var type = pickType();
      rec.r = new MediaRecorder(stream, type ? { mimeType: type, audioBitsPerSecond: 64000 } : undefined);
      rec.r.ondataavailable = function (ev) { if (ev.data && ev.data.size) rec.chunks.push(ev.data); };
      rec.r.onstop = function () {
        var blob = new Blob(rec.chunks, { type: (rec.r.mimeType || type || 'audio/webm').split(';')[0] });
        var secs = Math.round((performance.now() - rec.t0) / 100) / 10;
        cleanupRec();
        if (rec.resolve) rec.resolve({ blob: blob, seconds: secs, url: URL.createObjectURL(blob) });
        rec.resolve = null;
      };
      rec.t0 = performance.now();
      rec.r.start(250);
      if (onLevel) {
        try {
          var ac = audioCtx(), src = ac.createMediaStreamSource(stream), an = ac.createAnalyser();
          an.fftSize = 512; src.connect(an);
          var buf = new Float32Array(an.fftSize);
          var loop = function () {
            an.getFloatTimeDomainData(buf);
            var s = 0; for (var i = 0; i < buf.length; i++) s += buf[i] * buf[i];
            onLevel(Math.min(1, Math.sqrt(s / buf.length) * 4), (performance.now() - rec.t0) / 1000);
            rec.raf = requestAnimationFrame(loop);
          };
          loop();
        } catch (e) { /* level meter is a nicety */ }
      }
      rec.timer = setTimeout(function () { if (rec.r && rec.r.state === 'recording') rec.r.stop(); }, (maxSeconds || 60) * 1000);
      return true;
    }, function (e) {
      throw new Error(e && e.name === 'NotAllowedError' ? 'The microphone is blocked. Allow it in the browser to record.' : 'The microphone did not start.');
    });
  };
  function cleanupRec() {
    cancelAnimationFrame(rec.raf); clearTimeout(rec.timer);
    if (rec.stream) rec.stream.getTracks().forEach(function (t) { t.stop(); });
    rec.stream = null;
  }
  PH.recStop = function () {
    return new Promise(function (res) {
      if (!rec.r || rec.r.state !== 'recording') { res(null); return; }
      rec.resolve = res; rec.r.stop();
    });
  };
  PH.recCancel = function () { rec.resolve = null; if (rec.r && rec.r.state === 'recording') rec.r.stop(); cleanupRec(); };

  var snd = { audio: null, speaking: false };
  PH.playUrl = function (url, onEnd) {
    PH.stopSound();
    var a = new Audio(url); snd.audio = a;
    var done = false;
    a.onended = function () { snd.audio = null; if (!done && onEnd) { done = true; onEnd(true); } };
    a.onerror = function () { snd.audio = null; if (!done && onEnd) { done = true; onEnd(false); } };
    return a.play().then(function () { return true; }, function () { if (!done && onEnd) { done = true; onEnd(false); } return false; });
  };
  /* A recorded library voice, or the device voice if the clip can't play (offline, old browser). */
  PH.playOrSay = function (url, text, onEnd) {
    return PH.playUrl(url, function (ok) {
      if (ok) { if (onEnd) onEnd(true); return; }
      PH.say(text, onEnd);
    });
  };
  PH.say = function (text, onEnd) {
    PH.stopSound();
    if (!window.speechSynthesis || !text) { if (onEnd) setTimeout(function () { onEnd(false); }, 0); return false; }
    var u = new SpeechSynthesisUtterance(String(text));
    u.rate = 0.92; u.pitch = 1.1;
    var voices = window.speechSynthesis.getVoices() || [];
    var en = voices.filter(function (v) { return /^en/i.test(v.lang); });
    var nice = en.filter(function (v) { return /female|samantha|google|natural|aria|jenny/i.test(v.name); })[0] || en[0];
    if (nice) u.voice = nice;
    u.onend = function () { snd.speaking = false; if (onEnd) onEnd(true); };
    u.onerror = function () { snd.speaking = false; if (onEnd) onEnd(false); };
    snd.speaking = true;
    window.speechSynthesis.speak(u);
    return true;
  };
  PH.stopSound = function () {
    if (snd.audio) { try { snd.audio.pause(); } catch (e) {} snd.audio = null; }
    if (window.speechSynthesis && snd.speaking) { window.speechSynthesis.cancel(); snd.speaking = false; }
  };

  /* ---------------------------------------------------------------- sound effects (synthesised, nothing to download) */
  var actx = null;
  function audioCtx() { if (!actx) actx = new (window.AudioContext || window.webkitAudioContext)(); if (actx.state === 'suspended') actx.resume(); return actx; }
  PH.muted = function () { try { return localStorage.getItem('photohunt.mute') === '1'; } catch (e) { return false; } };
  PH.setMuted = function (m) { try { localStorage.setItem('photohunt.mute', m ? '1' : '0'); } catch (e) {} };
  function tone(ac, freq, start, dur, type, vol) {
    var o = ac.createOscillator(), g = ac.createGain();
    o.type = type || 'sine'; o.frequency.setValueAtTime(freq, start);
    g.gain.setValueAtTime(0.0001, start); g.gain.exponentialRampToValueAtTime(vol || 0.2, start + 0.015);
    g.gain.exponentialRampToValueAtTime(0.0001, start + dur);
    o.connect(g); g.connect(ac.destination); o.start(start); o.stop(start + dur + 0.05);
  }
  PH.sfx = function (name) {
    if (PH.muted()) return;
    try {
      var ac = audioCtx(), t = ac.currentTime + 0.02;
      if (name === 'ding') { tone(ac, 988, t, 0.25, 'sine', 0.22); tone(ac, 1480, t + 0.09, 0.45, 'sine', 0.2); }
      else if (name === 'tada') { [523, 659, 784, 1047].forEach(function (f, i) { tone(ac, f, t + i * 0.11, 0.5, 'triangle', 0.18); }); tone(ac, 1568, t + 0.48, 0.8, 'sine', 0.12); }
      else if (name === 'oops') { tone(ac, 392, t, 0.18, 'triangle', 0.16); tone(ac, 311, t + 0.16, 0.3, 'triangle', 0.16); }
      else if (name === 'tick') { tone(ac, 1200, t, 0.06, 'square', 0.06); }
      else if (name === 'go') { tone(ac, 784, t, 0.15, 'square', 0.1); tone(ac, 1175, t + 0.12, 0.4, 'square', 0.1); }
      else if (name === 'pop') { tone(ac, 660, t, 0.08, 'sine', 0.18); tone(ac, 330, t + 0.04, 0.12, 'sine', 0.1); }
      else if (name === 'whoosh') {
        var n = ac.createBufferSource(), buf = ac.createBuffer(1, ac.sampleRate * 0.7, ac.sampleRate), d = buf.getChannelData(0);
        for (var i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * (1 - i / d.length);
        var f = ac.createBiquadFilter(); f.type = 'bandpass'; f.frequency.setValueAtTime(400, t); f.frequency.exponentialRampToValueAtTime(2400, t + 0.6);
        var g = ac.createGain(); g.gain.value = 0.35;
        n.buffer = buf; n.connect(f); f.connect(g); g.connect(ac.destination); n.start(t);
      }
    } catch (e) { /* sound is a nicety */ }
  };

  /* ---------------------------------------------------------------- confetti (sprinkles) */
  PH.confetti = function (ms) {
    if (reduced()) return;
    var cv = document.createElement('canvas');
    cv.className = 'ph-confetti'; cv.setAttribute('aria-hidden', 'true');
    cv.width = window.innerWidth; cv.height = window.innerHeight;
    document.body.appendChild(cv);
    var ctx = cv.getContext('2d'), cols = ['#FF6FA3', '#22B07F', '#4A7BF0', '#F5B700', '#FF8A3D', '#C2255C'], parts = [];
    for (var i = 0; i < 150; i++) {
      parts.push({ x: cv.width / 2 + (Math.random() - 0.5) * cv.width * 0.3, y: cv.height * 0.55, vx: (Math.random() - 0.5) * 14,
                   vy: -8 - Math.random() * 12, r: Math.random() * Math.PI, vr: (Math.random() - 0.5) * 0.4, c: cols[i % cols.length], w: 4 + Math.random() * 4 });
    }
    var t0 = performance.now(), dur = ms || 1900;
    (function frame(now) {
      var k = (now - t0) / dur;
      ctx.clearRect(0, 0, cv.width, cv.height);
      parts.forEach(function (p) {
        p.vy += 0.42; p.vx *= 0.99; p.x += p.vx; p.y += p.vy; p.r += p.vr;
        ctx.save(); ctx.globalAlpha = Math.max(0, 1 - Math.max(0, k - 0.7) / 0.3);
        ctx.translate(p.x, p.y); ctx.rotate(p.r); ctx.fillStyle = p.c;
        ctx.beginPath(); ctx.roundRect ? ctx.roundRect(-p.w, -2, p.w * 2, 4, 2) : ctx.rect(-p.w, -2, p.w * 2, 4); ctx.fill(); ctx.restore();
      });
      if (k < 1) requestAnimationFrame(frame); else cv.remove();
    })(t0);
  };

  /* ---------------------------------------------------------------- blow out the candles (microphone) */
  var blow = { stream: null, raf: 0 };
  PH.blowStart = function (onLevel, onBlown) {
    PH.blowStop();
    if (!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)) return Promise.reject(new Error('no microphone'));
    return navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: false } }).then(function (stream) {
      blow.stream = stream;
      var ac = audioCtx(), src = ac.createMediaStreamSource(stream), an = ac.createAnalyser();
      an.fftSize = 1024; src.connect(an);
      var buf = new Float32Array(an.fftSize), strong = 0, last = performance.now();
      var loop = function (now) {
        an.getFloatTimeDomainData(buf);
        var s = 0; for (var i = 0; i < buf.length; i++) s += buf[i] * buf[i];
        var rms = Math.sqrt(s / buf.length), dt = now - last; last = now;
        if (onLevel) onLevel(Math.min(1, rms * 5));
        strong = rms > 0.11 ? strong + dt : Math.max(0, strong - dt * 0.5);
        if (strong > 280) { PH.blowStop(); onBlown(); return; }
        blow.raf = requestAnimationFrame(loop);
      };
      blow.raf = requestAnimationFrame(loop);
      return true;
    });
  };
  PH.blowStop = function () {
    cancelAnimationFrame(blow.raf);
    if (blow.stream) blow.stream.getTracks().forEach(function (t) { t.stop(); });
    blow.stream = null;
  };

  /* ---------------------------------------------------------------- 3, 2, 1, go! */
  PH.countdown = function (n, onDone) {
    var el = document.createElement('div');
    el.className = 'ph-count'; el.setAttribute('role', 'status');
    document.body.appendChild(el);
    var k = n || 3;
    var step = function () {
      el.textContent = k > 0 ? String(k) : 'Go!';
      el.classList.remove('beat'); void el.offsetWidth; el.classList.add('beat');
      PH.sfx(k > 0 ? 'tick' : 'go');
      if (k-- > 0) setTimeout(step, 800); else setTimeout(function () { el.remove(); if (onDone) onDone(); }, 700);
    };
    step();
  };

  /* ---------------------------------------------------------------- BINGO! (photo bingo lines) */
  PH.banner = function (text) {
    var el = document.createElement('div');
    el.className = 'ph-count ph-bingo beat'; el.setAttribute('role', 'status');
    el.textContent = text || 'Bingo!';
    document.body.appendChild(el);
    PH.sfx('tada'); PH.confetti();
    setTimeout(function () { el.remove(); }, 1500);
  };
})();
