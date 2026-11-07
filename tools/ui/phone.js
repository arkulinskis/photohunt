/* Phone-width check (run at 390 px wide by tools/ui_test.py): every page loads without errors and without sideways
   scrolling, signed out and signed in. Resolves to {ok, log}. */
(async function () {
  const log = [], bad = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 20000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function check(hash, ready) {
    if (location.hash !== hash) window.UI_READY = false;  // the old page stays until the router runs
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && (!ready || ready()), hash, 30000);
    await sleep(500);
    const w = document.documentElement.scrollWidth, vw = Math.min(window.innerWidth, screen.width);
    const wide = $$('body *').filter((e) => { const r = e.getBoundingClientRect(); return r.width && r.right > vw + 1; })
      .slice(0, 3).map((e) => e.tagName.toLowerCase() + '.' + String(e.className).split(' ').slice(0, 2).join('.'));
    if (w > vw + 1) bad.push(hash + ' scrolls sideways (' + w + ' > ' + vw + ') ' + wide.join(' '));
    log.push((w > vw + 1 ? 'WIDE ' : 'ok   ') + hash + ' (' + w + ')');
  }

  // PhotoHunt: pages with ids in the address are made through the app's own server calls (window.phCall, startup.py)
  const phCall = async (n, ...a) => JSON.parse(await window.phCall(n, JSON.stringify(a)));
  async function playPages() {  // a visitor's game in the Try-me Hunt: the Go screen, then the hunt itself
    const j = await phCall('join_hunt', 'CAKE42', 'Page Tester', 'star', 'pink');
    return j.token;
  }
  async function memberPages() {
    const hq = await phCall('get_hq');
    const demo = (hq.examples.find((h) => h.birthday_name === 'Mia') || hq.examples[0]).id;
    const mine = (await phCall('create_hunt', { title: 'Check hunt for Maximilian-Alexander-Geburtstagskuchen', kind: 'mix', birthday_name: 'Maximilian', birthday_age: 7, time_limit: 10 })).hunt;
    await phCall('add_library_tasks', mine.id, ['m01', 'f01', 'k02']);
    await phCall('start_hunt', mine.id);
    const kid = (await phCall('add_kid', 'Mimi', 'heart', 'pink')).kid;
    await phCall('kid_join', kid.token, mine.code);
    const e = encodeURIComponent;
    return ['#home', '#family', '#tasks', '#hunt/' + e(demo), '#album/' + e(demo), '#hunt/' + e(mine.id), '#live/' + e(mine.id), '#kid/' + kid.token, '#profile'];
  }
  try {
    for (const h of ['#landing', '#auth', '#auth/signup', '#join', '#join/CAKE42', '#tasks']) await check(h);
    const tok = await playPages();
    await check('#play/' + tok);
    await phCall('go', tok);
    await check('#landing');
    await check('#play/' + tok, () => $$('.pt').length === 5);
    $$('.pt')[0].click();
    await until(() => $$('.anvil-modal').some((m) => m.getBoundingClientRect().width > 0 && m.querySelector('.fn')), 'find dialog');
    await sleep(600);
    { const w = document.documentElement.scrollWidth, sw = Math.min(window.innerWidth, screen.width);
      if (w > sw + 1) bad.push('find dialog scrolls sideways (' + w + ')'); log.push((w > sw + 1 ? 'WIDE ' : 'ok   ') + 'find dialog (' + w + ')'); }
    $$('.anvil-modal button').find((b) => /Back to the cake/.test(b.textContent)).click();
    await sleep(500);
    // sign up so the member pages can be checked too
    location.hash = '#auth/signup';
    await until(() => window.UI_READY && $$('.au-card input').length >= 3, 'sign-up form');
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]');
    type(inputs[0], 'Phone Tester'); type(inputs[1], 'phone' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const tick = $('.au-card input[type=checkbox]'); if (tick && !tick.checked) tick.click();
    $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    await until(() => location.hash === '#home' && window.UI_READY, 'signed in', 30000);
    for (const h of await memberPages()) await check(h);
    log.push(bad.length ? 'PROBLEMS: ' + bad.join(' | ') : 'PASSED');
    return { ok: !bad.length, log: log };
  } catch (e) {
    log.push(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
