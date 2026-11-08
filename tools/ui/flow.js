/* The main journeys, run inside the real app (Anvil App Server) by tools/ui_test.py through tools/live/drive.mjs
   (Chrome with a fake camera and microphone). Resolves to {ok, log}. Keep log lines ASCII (the Windows console).
   1. A visitor plays the Try-me Hunt (CAKE42): join, Go, snap with the camera, a candle lights. Then photo bingo
      (BINGO9): three snaps in a row are a BINGO.
   2. A grown-up signs up, adds a kid, bakes a hunt, snaps two treasures (camera + Choose a photo), records a clue,
      switches to a party mix and adds library tasks, checks the share QR decodes to the join link, starts the hunt.
   3. The kid joins from their Kids' corner, finds a treasure (or a grown-up says yes), does a task.
   4. The live board shows it, the grown-up ends the hunt, the album shows the results and certificates.
   5. The task library, profile, dark mode, sign out. */
(async function () {
  const log = [], t0 = Date.now();
  const say = (m) => log.push(((Date.now() - t0) / 1000).toFixed(1) + 's ' + m);
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s);
  const $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (e) => e && e.getBoundingClientRect().width > 0 && getComputedStyle(e).visibility !== 'hidden';
  const norm = (s) => String(s || '').trim().replace(/\s+/g, ' ');
  const byText = (sel, text) => $$(sel).find((e) => vis(e) && norm(e.textContent) === text);
  const modal = () => $$('.anvil-modal').find((m) => vis(m) && m.querySelector('.ui'));
  async function click(sel, text, ms) {
    const el = await until(() => (text ? byText(sel, text) : $$(sel).find(vis)), sel + (text ? ' "' + text + '"' : ''), ms);
    el.scrollIntoView({ block: 'center' });
    el.click();
    return el;
  }
  function type(input, value) {
    input.focus();
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
    input.dispatchEvent(new Event('blur', { bubbles: true }));
  }
  async function page(hash, ready, what) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && ready(), what || hash, 40000);
    await sleep(400);
  }
  const ok = (cond, msg) => { if (!cond) throw new Error('FAILED: ' + msg); say('ok   ' + msg); };
  const closed = () => !modal();
  // a picture file for "Choose a photo": one of the demo drawings, painted onto a canvas
  async function demoFile(art) {
    const img = new Image();
    img.src = '_/theme/demo-' + art + '.svg';
    await img.decode();
    const cv = document.createElement('canvas'); cv.width = 600; cv.height = 600;
    cv.getContext('2d').drawImage(img, 0, 0, 600, 600);
    const blob = await new Promise((r) => cv.toBlob(r, 'image/jpeg', 0.9));
    return new File([blob], art + '.jpg', { type: 'image/jpeg' });
  }
  async function choosePhoto(input, art) {
    const dt = new DataTransfer();
    dt.items.add(await demoFile(art));
    input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function snapInModal() {
    await until(() => { const v = modal() && modal().querySelector('.ph-cam video'); return v && v.videoWidth > 0; }, 'the live camera (fake device)', 20000);
    await click('.anvil-modal .anvil-role-ph-shutter button');
  }

  try {
    // ---------------------------------------------------------------- 1. landing + a visitor plays the demo hunt
    await page('#landing', () => $('.lp-hero'), 'landing');
    ok($('.lp-hero a[href="#auth/signup"]'), 'landing: hero with a sign-up link');
    ok($('.lp-hero a[href="#join/CAKE42"]'), 'landing: Try the demo hunt');
    await until(() => $$('.lp-party .ph-candle').length === 4, 'the hero cake');
    ok($$('.lp-party .lp-pola').length === 4, 'landing: the cake with four polaroids');

    await page('#join', () => $('.anvil-role-jn-code-box'), 'join');
    type($('input.anvil-role-jn-code-box, .anvil-role-jn-code-box input'), 'cake42');
    await click('.anvil-role-btn-primary button', 'Find it');
    await until(() => location.hash === '#join/CAKE42' && window.UI_READY && byText('.anvil-role-page-title', 'Try-me Hunt'), 'the hunt card');
    ok(/5 treasures/.test($('.anvil-role-jn-meta').textContent), 'join: the hunt card says 5 treasures');
    await click('.anvil-role-btn-primary button', "Let's hunt!");
    await until(() => $$('.anvil-role-msg-error').some((e) => vis(e) && /name/.test(e.textContent)), 'name error');
    ok(true, 'join: asks for a name first');
    type($$('.jn-form input').find(vis), 'Visiting Vera');
    await click('.ph-topper-pick', 'Rocket');
    ok(byText('.ph-topper-pick', 'Rocket').getAttribute('aria-pressed') === 'true', 'join: the topper choice is pressed');
    await click('.anvil-role-btn-primary button', "Let's hunt!");
    await until(() => /^#play\//.test(location.hash) && window.UI_READY && $('.play-top'), 'play screen', 30000);
    ok(norm($('.anvil-role-play-me').textContent) === 'Visiting Vera', 'play: my name and topper at the top');
    ok(!vis($('.ui-header')), 'play: no header for kids');
    await click('.anvil-role-play-go button');
    await until(() => $$('.pt').length === 5 && !$('.ph-count'), 'tiles after the countdown', 20000);
    ok(/10:00|9:5\d/.test($('.anvil-role-play-clock').textContent), 'play: Go starts my 10 minute clock');
    $$('.pt')[0].click();
    await until(() => modal() && byText('.anvil-modal button', 'I found it! Take a picture'), 'find dialog');
    ok(modal().querySelector('.ph-photo img[src*="demo-teapot"]'), 'find: shows the treasure picture');
    await click('.anvil-modal button', 'I found it! Take a picture');
    await snapInModal();
    await until(() => byText('.anvil-modal .anvil-role-fn-verdict', 'You found it!'), 'found', 30000);
    ok(true, 'find: Snap! -> You found it! (demo hunts accept any photo)');
    await until(closed, 'dialog closes by itself', 8000);
    await until(() => /1 of 5/.test($('.anvil-role-play-count').textContent) && $$('.pt.is-found').length === 1, 'a candle is lit');
    ok($$('.play-cake .ph-candle.lit').length === 1, 'play: the cake has one lit candle');

    // ---------------------------------------------------------------- 1b. photo bingo (BINGO9): a 3x3 card, a full row is a BINGO
    await page('#join/BINGO9', () => byText('.anvil-role-page-title', "Little Sam's Photo Bingo"), 'the bingo hunt card');
    type($$('.jn-form input').find(vis), 'Tiny Tom');
    await click('.anvil-role-btn-primary button', "Let's hunt!");
    await until(() => /^#play\//.test(location.hash) && window.UI_READY && $('.play-top') && $('.anvil-role-play-go'), 'bingo play screen', 30000);
    await click('.anvil-role-play-go button');
    await until(() => $$('.pt.bingo').length === 9 && !$('.ph-count'), 'the bingo card', 20000);
    ok(getComputedStyle($('.anvil-role-play-bingo > div')).gridTemplateColumns.split(' ').length === 3, 'bingo: 9 big pictures in 3 columns');
    ok(norm($('.anvil-role-play-headline').textContent) === 'Photo bingo!', 'bingo: the headline');
    for (let i = 0; i < 3; i++) {
      $$('.pt.bingo')[i].click();
      await until(() => modal() && byText('.anvil-modal button', 'I found it! Take a picture'), 'bingo find dialog');
      await click('.anvil-modal button', 'I found it! Take a picture');
      await snapInModal();
      await until(() => byText('.anvil-modal .anvil-role-fn-verdict', 'You found it!'), 'bingo found', 30000);
      await until(closed, 'bingo dialog closes by itself', 8000);
      await until(() => $$('.pt.bingo.is-found').length === i + 1, 'stamp ' + (i + 1));
    }
    ok(vis($('.pt.bingo.is-found .pt-stamp')), 'bingo: found pictures get a stamp');
    await until(() => norm($('.anvil-role-play-headline').textContent) === 'BINGO!', 'BINGO!', 10000);
    ok($$('.pt.bingo.in-line').length === 3, 'bingo: a full row is a BINGO (the row lights up)');

    // ---------------------------------------------------------------- 2. a grown-up signs up (members-only page -> sign in -> back)
    await page('#family', () => true);
    await until(() => window.UI_READY && $$('.au-card input').length >= 2, 'redirected to sign in');
    await click('.au-card .ui-seg button', 'Create account');
    await until(() => $$('.au-card input').filter(vis).length >= 3, 'sign-up form');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]').filter(vis);
    type(inputs[0], 'Flow Tester'); type(inputs[1], 'flow' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]');
    if (tick && !tick.checked) tick.click();
    await click('.anvil-role-btn-block button', 'Create account');
    await until(() => location.hash === '#family' && window.UI_READY && $('.fam'), 'back on the kids page', 40000);
    ok(true, 'sign-up: signed in and sent on to the page they asked for');

    // add a kid -> the Kids' corner QR
    await click('.anvil-role-btn-primary button', 'Add a kid');
    await until(() => modal() && $('.ke input'), 'kid dialog');
    type($('.ke input'), 'Mimi');
    await click('.ke .ph-topper-pick', 'Dino');
    await click('.ke .ph-swatch', 'Mint');
    await click('.ke .anvil-role-btn-primary button', 'Save');
    await until(() => modal() && $('.kl .ph-qr svg'), "the Kids' corner QR");
    const kidLink = $('.kl input').value;
    ok(/#kid\/[\w-]{20,}/.test(kidLink), "family: the Kids' corner link and QR");
    const kidToken = kidLink.split('#kid/')[1];
    await click('.kl .anvil-role-btn-primary button', 'Done');
    await until(() => closed() && $$('.kc').length === 1, 'kid card');
    ok(/Mimi/.test($('.kc').textContent), 'family: the kid card');

    // ---------------------------------------------------------------- bake a hunt
    await page('#home', () => $('.hq') && $$('.hc').length >= 4, 'Party HQ');
    ok(/Example/.test($('.hq').textContent), 'HQ: the example hunts');
    await click('.anvil-role-btn-primary button', 'Bake a new hunt');
    await until(() => modal() && $('.hs input'), 'settings dialog');
    type($('.hs input'), 'Flow party hunt');
    type($$('.hs input')[1], 'Mimi');
    await click('.hs .ph-swatch', 'Lemon');
    await click('.hs .anvil-role-btn-primary button', 'Bake it');
    await until(() => /^#hunt\//.test(location.hash) && window.UI_READY && $('.hk-head'), 'the hunt kitchen', 30000);
    const huntId = decodeURIComponent(location.hash.slice(6));
    ok(byText('.anvil-role-page-title', 'Flow party hunt'), 'kitchen: the new hunt');
    const code = norm($('.anvil-role-ph-code-chip').textContent).replace('Code ', '');
    ok(/^[A-Z0-9]{6}$/.test(code), 'kitchen: a 6-letter code (' + code + ')');

    // treasure 1: camera snap + a recorded clue
    await click('.anvil-role-btn-primary button', 'Snap a treasure');
    await until(() => modal() && $('.te'), 'treasure dialog');
    await click('.te button', 'Take a photo');
    await snapInModal();
    await until(() => $('.te .ph-photo img[src^="blob:"]'), 'the snapshot');
    type($('.te-fields input'), 'Red teapot');
    type($('.te-fields textarea'), 'It lives in the kitchen.');
    await click('.te .ph-rec button', 'Record the clue');
    await sleep(1600);
    await click('.te .ph-rec button', 'Stop');
    await until(() => /New recording/.test($('.te .anvil-role-ph-rec-time').textContent), 'recording made');
    await click('.te .anvil-role-btn-primary button', 'Save');
    await until(() => closed() && $$('.tr').length === 1, 'treasure saved', 30000);
    ok(/Magic match ready/.test($('.tr').textContent) && /Voice clue/.test($('.tr').textContent), 'kitchen: photo + voice clue saved, Magic match ready');

    // treasure 2: Choose a photo (a file)
    await click('.anvil-role-btn-primary button', 'Snap a treasure');
    await until(() => modal() && $('.te'), 'treasure dialog');
    await click('.te button', 'Take a photo');
    await until(() => $('.te .ph-cam input[type=file]'), 'file input');
    await choosePhoto($('.te .ph-cam input[type=file]'), 'book');
    await until(() => $('.te .ph-photo img[src^="blob:"]'), 'the chosen photo');
    type($('.te-fields input'), 'Blue book');
    await click('.te .anvil-role-btn-primary button', 'Save');
    await until(() => closed() && $$('.tr').length === 2, 'second treasure', 30000);
    ok(true, 'kitchen: Choose a photo works too');
    $$('.tr')[1].querySelector('.anvil-role-ic-up button').click();
    await until(() => /Blue book/.test($$('.tr')[0].textContent), 'moved up');
    ok(true, 'kitchen: treasures can be reordered');

    // party mix + library tasks
    await click('.hk-actions button', 'Settings');
    await until(() => modal() && $('.hs'), 'settings');
    $$('.hs .ph-choice').find((b) => /Party mix/.test(b.textContent)).click();
    await click('.hs .anvil-role-btn-primary button', 'Save');
    await until(() => closed() && byText('.anvil-role-btn button', 'Add from 100 tasks'), 'mix buttons');
    await click('.anvil-role-btn button', 'Add from 100 tasks');
    await until(() => modal() && $$('.tp .tk').length === 100, 'library of 100');
    ok(true, 'task picker: 100 tasks');
    await click('.tp .anvil-role-ph-chip button', 'Wiggle and move (20)');
    await until(() => $$('.tp .tk').length === 20, 'category filter');
    $$('.tp .tk input[type=checkbox]')[0].click();
    $$('.tp .tk input[type=checkbox]')[3].click();
    await until(() => /2 tasks picked/.test($('.tp-foot').textContent), 'two picked');
    await click('.tp .anvil-role-btn-primary button', 'Add 2 tasks');
    await until(() => closed() && $$('.tr').length === 4, 'tasks added', 30000);
    ok(/Tap when done/.test($$('.tr')[2].textContent), 'kitchen: library tasks added');

    // share: the QR code decodes to the join link
    await click('.hk-actions .anvil-role-btn-primary button', 'Share');
    await until(() => modal() && $('.sh .ph-qr svg'), 'share dialog');
    ok(norm($('.sh .anvil-role-sh-code').textContent) === code, 'share: the code');
    const svg = $('.sh .ph-qr svg').outerHTML;
    await new Promise((res, rej) => { const s = document.createElement('script'); s.src = document.querySelector('meta[name="ph-qrscan"]').content; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
    const qimg = new Image(); qimg.src = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg); await qimg.decode();
    const qcv = document.createElement('canvas'); qcv.width = qcv.height = 400; qcv.getContext('2d').drawImage(qimg, 0, 0, 400, 400);
    const decoded = window.PH.decodeCanvas(qcv);
    ok(decoded && decoded.indexOf('#join/' + code) > 0, 'share: the QR code reads back as the join link');
    await click('.sh .anvil-role-btn-primary button', 'Done');
    await until(closed, 'share closed');

    // live board: start
    await page('#live/' + encodeURIComponent(huntId), () => $('.lv-head'), 'live board');
    ok(/Waiting to start/.test($('.lv-head').textContent), 'live: waiting to start');
    await click('.anvil-role-btn-primary button', 'Start the hunt');
    await until(() => /Hunt on!/.test($('.lv-head').textContent) && /1[45]:\d\d/.test($('.anvil-role-lv-clock-n').textContent), 'started');
    ok(true, 'live: Start -> Hunt on! with a 15 minute clock');

    // ---------------------------------------------------------------- 3. the kid plays from the Kids' corner
    window.UI_READY = false;
    location.hash = '#kid/' + kidToken + '/' + code;
    await until(() => /^#play\//.test(location.hash) && window.UI_READY && $$('.pt').length === 4, 'kid play screen', 40000);
    const kidPlay = location.hash;
    ok(norm($('.anvil-role-play-me').textContent) === 'Mimi', "kids' corner: joined as Mimi with one tap");
    $$('.pt').find((p) => /Red teapot/.test(p.textContent)).click();
    await until(() => modal() && byText('.anvil-modal button', 'I found it! Take a picture'), 'find dialog');
    ok(modal().querySelector('.ph-voice:not(:disabled)'), 'find: the recorded clue can be played');
    await click('.anvil-modal button', 'I found it! Take a picture');
    await until(() => { const v = modal() && modal().querySelector('.ph-cam video'); return v && v.videoWidth > 0; }, 'camera', 20000);
    ok(modal().querySelector('.ph-cam-ghost[src]'), 'find: the ghost of the grown-up photo over the camera');
    await click('.anvil-modal .anvil-role-ph-shutter button');
    await until(() => modal() && $$('.anvil-modal .anvil-role-fn-verdict').some((v) => vis(v) && !/Checking/.test(v.textContent)), 'a verdict', 30000);
    const verdict = norm($$('.anvil-modal .anvil-role-fn-verdict').find(vis).textContent);
    say('     magic match said: ' + verdict);
    if (verdict !== 'You found it!') {
      await click('.anvil-modal button', 'Ask a grown-up');
      const q = await until(() => $$('.anvil-modal .anvil-role-fn-gate-q').find(vis), 'the grown-up question');
      const m = norm(q.textContent).match(/(\d+) \+ (\d+)/);
      await click('.anvil-modal .fn-gate-a button', String(+m[1] + +m[2]));
      await click('.anvil-modal button', "Yes, that's it!");
      await until(() => byText('.anvil-modal .anvil-role-fn-verdict', 'You found it!'), 'grown-up said yes', 30000);
      ok(true, 'find: a grown-up says yes after the grown-ups-only sum');
    } else {
      ok(true, 'find: magic match found it');
    }
    await until(closed, 'dialog closes', 8000);
    // a wrong photo (a duck for the book): not quite -> ask a grown-up -> the sum -> yes
    $$('.pt').find((p) => /Blue book/.test(p.textContent)).click();
    await until(() => modal() && byText('.anvil-modal button', 'I found it! Take a picture'), 'find dialog');
    await click('.anvil-modal button', 'I found it! Take a picture');
    await until(() => modal() && modal().querySelector('.ph-cam input[type=file]'), 'camera');
    await choosePhoto(modal().querySelector('.ph-cam input[type=file]'), 'duck');
    await until(() => modal() && $$('.anvil-modal .anvil-role-fn-verdict').some((v) => vis(v) && !/Checking/.test(v.textContent)), 'a verdict', 30000);
    const wrong = norm($$('.anvil-modal .anvil-role-fn-verdict').find(vis).textContent);
    ok(wrong === 'Hmm, not quite!' || wrong === 'So close!', 'magic match: a duck is not the blue book (' + wrong + ')');
    await click('.anvil-modal button', 'Ask a grown-up');
    const gq = await until(() => $$('.anvil-modal .anvil-role-fn-gate-q').find(vis), 'the grown-up question');
    const gm = norm(gq.textContent).match(/(\d+) \+ (\d+)/);
    await click('.anvil-modal .fn-gate-a button', String(+gm[1] + +gm[2]));
    await click('.anvil-modal button', "Yes, that's it!");
    await until(() => byText('.anvil-modal .anvil-role-fn-verdict', 'You found it!'), 'grown-up said yes', 30000);
    ok(true, 'find: a grown-up says yes on the tablet after the grown-ups-only sum');
    await until(closed, 'dialog closes', 8000);
    // a task: "I did it!"
    $$('.pt').find((p) => p.querySelector('.pt-task').style.display !== 'none').click();
    await until(() => modal() && $$('.anvil-modal .anvil-role-fn-task-text').some(vis), 'task dialog');
    const did = byText('.anvil-modal button', 'I did it!') || byText('.anvil-modal button', 'I did it! Take a picture');
    did.click();
    if (/Take a picture/.test(did.textContent)) await snapInModal();
    await until(() => byText('.anvil-modal .anvil-role-fn-verdict', 'You did it!'), 'task done', 30000);
    await until(closed, 'dialog closes', 8000);
    await until(() => /3 of 4/.test($('.anvil-role-play-count').textContent), 'three candles');
    ok($$('.play-cake .ph-candle.lit').length === 3, 'play: three candles lit after two finds and a task');

    // ---------------------------------------------------------------- 4. live board, end, album
    await page('#live/' + encodeURIComponent(huntId), () => $$('.pr').length === 1, 'live board with the player');
    ok(/Mimi/.test($('.pr').textContent) && /3 of 4 found/.test($('.pr').textContent), 'live: Mimi has 3 of 4');
    ok($$('.fd').length >= 2, 'live: the activity feed');
    await click('.anvil-role-btn button', 'End the hunt');
    await click('.anvil-modal-content button', 'End the hunt');
    await until(() => /Finished/.test($('.lv-head').textContent) && byText('.anvil-role-btn button', 'Play again'), 'ended');
    ok(true, 'live: End the hunt -> Finished, Play again offered');
    await page(kidPlay, () => byText('.anvil-role-btn-primary button', 'Blow out the candles!'), 'the kid sees the result');
    ok($$('.play-stickers .ph-sticker').length >= 1, 'play: stickers at the end');
    await click('.anvil-role-btn-primary button', 'Blow out the candles!');
    await click('.anvil-role-btn button', 'Tap to blow');
    await until(() => $$('.play-cake .ph-smoke').length > 0, 'candles out');
    ok(/Hooray/.test($('.anvil-role-play-subline').textContent), 'play: blowing the candles out');
    await sleep(3600);
    ok(/Hooray/.test($('.anvil-role-play-subline').textContent) && !vis($('.anvil-role-play-subline + * .anvil-role-btn-primary')), 'play: the Hooray stays after the 3 s refresh');

    await page('#album/' + encodeURIComponent(huntId), () => $('.al-results') && $$('.rr').length >= 1, 'album');
    ok($$('.rr').length === 1 && /Mimi/.test($('.rr').textContent), 'album: the results');
    ok($$('.ap').length >= 1, 'album: the kid snaps');
    ok($$('.cert').length === 1, 'album: a certificate ready to print');

    // ---------------------------------------------------------------- 5. tasks page, profile, theme, sign out
    await page('#tasks', () => $$('.tk').length === 100, 'tasks page');
    type($('.tasks-tools input'), 'jump');
    await until(() => $$('.tk').length > 0 && $$('.tk').length < 10, 'search');
    ok($$('.tk').every((t) => /jump/i.test(t.textContent)), 'tasks: search finds jumping tasks');
    const clip = await fetch('_/theme/voices/m01.mp3');
    ok(clip.ok && (await clip.arrayBuffer()).byteLength > 4000, 'tasks: the recorded task voices are served');

    await page('#profile', () => $('.pf-grid'), 'profile');
    type($('.pf-grid input'), 'Flow Tester Two');
    await click('.pf-grid .anvil-role-btn-primary button', 'Save');
    await until(() => /Flow Tester Two/.test($('.pf-head').textContent), 'name saved');
    ok(true, 'profile: name saved');
    await click('.anvil-role-avatar button');
    await click('.ui-menu .ui-seg button', 'Dark');
    ok(document.documentElement.classList.contains('ui-dark'), 'menu: Dark switches the theme');
    await click('.ui-menu .ui-seg button', 'Auto');
    await click('.ui-menu button', 'Sign out');
    await until(() => location.hash === '#landing' && window.UI_READY && $('.ui-header .ui-btn.primary'), 'signed out');
    ok($$('.lp-saved .sv').length >= 2, "landing: this tablet remembers Mimi's corner and the games");

    say('PASSED');
    return { ok: true, log: log };
  } catch (e) {
    say(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
