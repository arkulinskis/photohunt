/* For screenshots of member pages: sign up a fresh account and give every page something to show, including the
   design kit's worst cases (a very long name, 0 / 1 / many items). Resolves to window.SEED = {hunt, live, album, play,
   kid, visitor}: the addresses tools/ui_test.py --shots opens. Treasures get real photos through "Choose a photo"
   (the demo drawings painted onto a canvas), so the kitchen and the kids' tiles look like a real hunt. */
(async function () {
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 30000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (e) => e && e.getBoundingClientRect().width > 0;
  const modal = () => $$('.anvil-modal').find((m) => vis(m) && m.querySelector('.ui'));
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
    input.dispatchEvent(new Event('blur', { bubbles: true }));
  }
  const phCall = async (n, ...a) => JSON.parse(await window.phCall(n, JSON.stringify(a)));
  async function bingoPage(cells) {  // photo bingo (BINGO9) with a finished row: snapped with the (fake) camera
    const qa = (s) => Array.from(document.querySelectorAll(s));
    const shown = (e) => e && e.getBoundingClientRect().width > 0;
    const b = (await phCall('join_hunt', 'BINGO9', 'Little Sam', 'heart', 'pink')).token;
    await phCall('go', b);
    window.UI_READY = false; location.hash = '#play/' + b;
    await until(() => window.UI_READY && qa('.pt.bingo').length === 9, 'bingo card', 40000);
    const todo = cells || [0, 1, 2];
    for (let n = 0; n < todo.length; n++) {
      qa('.pt.bingo')[todo[n]].click();
      (await until(() => qa('.anvil-modal button').find((x) => shown(x) && /I found it/.test(x.textContent)), 'bingo find dialog')).click();
      await until(() => { const v = document.querySelector('.anvil-modal .ph-cam video'); return v && v.videoWidth > 0; }, 'camera', 20000);
      document.querySelector('.anvil-modal .anvil-role-ph-shutter button').click();
      await until(() => !qa('.anvil-modal').some((m) => shown(m) && m.querySelector('.fn')) && qa('.pt.bingo.is-found').length === n + 1, 'bingo stamp', 30000);
    }
    await sleep(1800);  // the BINGO! banner has gone
    return b;
  }
  async function go(hash, ready) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && (!ready || ready()), hash, 40000);
  }
  async function demoFile(art) {
    const img = new Image(); img.src = '_/theme/demo-' + art + '.svg'; await img.decode();
    const cv = document.createElement('canvas'); cv.width = 600; cv.height = 600;
    cv.getContext('2d').drawImage(img, 0, 0, 600, 600);
    const blob = await new Promise((r) => cv.toBlob(r, 'image/jpeg', 0.9));
    return new File([blob], art + '.jpg', { type: 'image/jpeg' });
  }
  async function addTreasure(name, clue, art) {
    $$('.anvil-role-btn-primary button').find((b) => /Snap a treasure/.test(b.textContent)).click();
    await until(() => modal() && $('.te'), 'treasure dialog');
    $$('.te button').find((b) => /Take a photo/.test(b.textContent)).click();
    const input = await until(() => $('.te .ph-cam input[type=file]'), 'file input');
    const dt = new DataTransfer(); dt.items.add(await demoFile(art)); input.files = dt.files;
    input.dispatchEvent(new Event('change', { bubbles: true }));
    await until(() => $('.te .ph-photo img[src^="blob:"]'), 'photo');
    type($('.te-fields input'), name);
    if (clue) type($('.te-fields textarea'), clue);
    $$('.te .anvil-role-btn-primary button').find((b) => /Save/.test(b.textContent)).click();
    await until(() => !modal(), 'saved', 30000);
  }
  try {
    if (location.hash !== '#auth/signup') window.UI_READY = false;
    location.hash = '#auth/signup';
    await until(() => window.UI_READY && $$('.au-card input').length >= 3, 'sign-up');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]');
    type(inputs[0], 'Sam Rivera'); type(inputs[1], 'shots' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
    $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    await until(() => location.hash === '#home' && window.UI_READY, 'home', 60000);

    const hunt = (await phCall('create_hunt', { title: "Maximilian-Alexander's Seventh Birthday Treasure Hunt", kind: 'mix', flavour: 'strawberry',
      birthday_name: 'Maximilian', birthday_age: 7, time_limit: 15, message: 'Happy birthday Max! Find every treasure to light your candles.' })).hunt;
    const e = encodeURIComponent;
    await go('#hunt/' + e(hunt.id), () => $('.hk-head'));
    await addTreasure('The spotty teapot', 'It lives in the kitchen and loves tea parties.', 'teapot');
    await addTreasure('Mr. Buttons the bear', '', 'teddy');
    await addTreasure('A rainbow sock', 'Look where clean clothes live.', 'sock');
    await addTreasure('The cactus', '', 'plant');
    await phCall('add_library_tasks', hunt.id, ['m01', 's05']);
    await phCall('start_hunt', hunt.id);
    const kids = [(await phCall('add_kid', 'Mimi', 'dino', 'mint')).kid, (await phCall('add_kid', 'Bartholomew-Maximilian', 'rocket', 'blue')).kid];
    const play = (await phCall('kid_join', kids[0].token, hunt.code)).token;
    await phCall('kid_join', kids[1].token, hunt.code);
    const st = await phCall('play_state', play);
    const task = st.treasures.find((t) => t.kind === 'task' && t.proof === 'done');
    if (task) await phCall('submit_find', play, task.id);
    const visitor = (await phCall('join_hunt', 'CAKE42', 'Visiting Vera', 'flower', 'berry')).token;
    const bingo = await bingoPage([0, 1, 2, 4]);
    const hq = await phCall('get_hq');
    const demo = (hq.examples.find((h) => h.birthday_name === 'Mia') || hq.examples[0]).id;
    window.SEED = { hunt: '#hunt/' + e(hunt.id), live: '#live/' + e(hunt.id), album: '#album/' + e(demo), play: '#play/' + play,
                    kid: '#kid/' + kids[0].token, visitor: '#play/' + visitor, bingo: '#play/' + bingo };
    return window.SEED;
  } catch (err) {
    return { error: String(err && err.message || err) };
  }
})();
