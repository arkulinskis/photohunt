/* Accessibility check (WCAG 2.2 A + AA), run inside the real app by tools/ui_test.py through tools/live/drive.mjs.
   1. axe-core (APP_MAKER/vendor/axe-core, injected by ui_test.py) on every page, signed out and signed in, light and
      dark: a "serious" or "critical" WCAG problem fails the run; smaller ones and best-practice hints are notes.
   2. Keyboard and screen-reader checks on the sign-in page: a real main heading, toggle buttons that say which one is
      on, autocomplete on the fields, the Google logo marked as decoration, errors read out, and the Privacy & Terms page
      keeping Tab inside.
   Add the app's own pages to PUBLIC and MEMBER below, and keyboard checks for its own pickers and forms
   (state.focus_key/refocus keep the focus on a choice when a RepeatingPanel redraws: test that here).
   Resolves to {ok, log}. Keep log lines ASCII (the Windows console). */
(async function () {
  /*AXE*/
  const PUBLIC = ['#landing', '#auth', '#auth/signup', '#join', '#join/CAKE42', '#tasks'];
  // member pages: memberPages() below (they need ids)

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
  const log = [], bad = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  async function until(fn, what, ms) {
    const end = Date.now() + (ms || 30000);
    while (Date.now() < end) { try { const v = fn(); if (v) return v; } catch (e) {} await sleep(150); }
    throw new Error('timed out waiting for: ' + what);
  }
  const $ = (s) => document.querySelector(s), $$ = (s) => Array.from(document.querySelectorAll(s));
  const vis = (e) => e && e.getBoundingClientRect().width > 0;
  const ascii = (s) => String(s).normalize('NFD').replace(/[^\x20-\x7e]/g, '');
  const ok = (cond, msg) => { if (cond) log.push('ok   ' + msg); else { bad.push(msg); log.push('FAIL ' + msg); } };
  function type(input, value) {
    input.focus(); input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true })); input.dispatchEvent(new Event('change', { bubbles: true }));
  }
  async function page(hash, ready) {
    if (location.hash !== hash) window.UI_READY = false;
    location.hash = hash;
    await until(() => window.UI_READY && location.hash === hash && (!ready || ready()), hash, 60000);
    await sleep(900);
  }
  if (!window.axe) { const s = document.createElement('script'); s.textContent = window.__AXE_SRC; document.head.appendChild(s); }

  async function scan(hash, ready) {
    await page(hash, ready);
    for (const theme of ['light', 'dark']) { window.UI.setTheme(theme); await sleep(900); /* let colour transitions and toasts settle */ await axeRun(hash + ' ' + theme); }
    window.UI.setTheme('auto');
  }
  async function axeRun(hash) {
    const res = await window.axe.run(document, {
      runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa', 'best-practice'] },
    });
    let serious = 0;
    for (const v of res.violations) {
      const wcag = v.tags.some((t) => /^wcag2/.test(t));
      const fail = wcag && (v.impact === 'serious' || v.impact === 'critical');
      const where = v.nodes.slice(0, 2).map((n) => ascii(n.target.join(' ')).slice(0, 70)).join(' | ');
      log.push((fail ? 'FAIL ' : 'note ') + hash + ' ' + v.id + ' (' + v.impact + ', ' + v.nodes.length + 'x): ' + where);
      if (fail) {
        serious++; bad.push(hash + ' ' + v.id);
        for (const n of v.nodes.slice(0, 3)) log.push('       ' + ascii(n.html).replace(/\s+/g, ' ').slice(0, 150) + ' :: ' + ascii((n.failureSummary || '').split(/\n/).slice(1).join(' ')).slice(0, 150));
      }
    }
    if (!serious) log.push('ok   ' + hash + ': no serious WCAG problems (' + res.passes.length + ' rules pass)');
  }

  try {
    // ---------------------------------------------------------------- the sign-in page
    await page('#auth', () => $$('.au-card input').length >= 2);
    ok(!!$('[role=heading][aria-level="1"]'), 'sign-in: the title is the main heading');
    const tabs = $$('.au-card .ui-seg button');
    ok(tabs.length === 2 && tabs[0].getAttribute('aria-pressed') === 'true' && tabs[1].getAttribute('aria-pressed') === 'false',
      'sign-in: Sign in / Create account say which one is chosen (aria-pressed)');
    ok(!$('.au-card [role=tablist]'), 'sign-in: no half-built tab list (the switch is a group of toggle buttons)');
    ok($$('.au-card input').some((i) => i.autocomplete === 'email') && $$('.au-card input').some((i) => i.autocomplete === 'current-password'),
      'sign-in: email and password have autocomplete');
    const g = $('.anvil-role-au-google img');
    ok(!g || g.getAttribute('alt') === '', 'sign-in: the Google logo is marked as decoration (alt="")');
    $$('.anvil-role-btn-block button').find((b) => vis(b) && /Sign in/.test(b.textContent)).click();  // empty form
    await until(() => $$('.au-card .anvil-role-msg-error').some(vis), 'the error');
    ok($$('.au-card .anvil-role-msg-error').find(vis).getAttribute('role') === 'alert', 'sign-in: the error is read out (role=alert)');
    const tick = $('.au-card input[type=checkbox]') || $('input[type=checkbox]');
    if (tick) {
      // a script's focus() doesn't always count as keyboard focus, so check the app's CSS: no app.css rule may drop the
      // outline of a focused tick box
      const kills = [];
      for (const sh of document.styleSheets) { if (!/app\.css/.test(sh.href || '')) continue; for (const r of sh.cssRules) if (r.selectorText && /:focus/.test(r.selectorText) && /outline:\s*(none|0)/.test(r.cssText) && /input|checkbox/.test(r.selectorText) && !/:not\(\[type=\"?checkbox\"?\]\)/.test(r.selectorText)) kills.push(r.selectorText); }
      ok(!kills.length, 'tick boxes keep their focus ring' + (kills.length ? ' (' + kills.join(', ') + ')' : ''));
    }

    // ---------------------------------------------------------------- Privacy & Terms keeps Tab inside
    const lk = $$('[data-lk-open]').find(vis);
    if (lk) {
      lk.click();
      await until(() => window.LegalKit && window.LegalKit.isOpen(), 'the Privacy page');
      const behind = Array.from(document.body.children).filter((e) => e.id !== 'lk-root' && e.tagName !== 'SCRIPT');
      ok(behind.length && behind.every((e) => e.inert), 'privacy page: the app behind it is inert (Tab stays inside)');
      window.LegalKit.close();
      ok(Array.from(document.body.children).every((e) => !e.inert), 'privacy page: closing it gives the app back');
    }

    // ---------------------------------------------------------------- axe on every page
    for (const h of PUBLIC) await scan(h);
    const tok = await playPages();
    await scan('#play/' + tok);
    await phCall('go', tok);
    await page('#landing');
    await scan('#play/' + tok, () => $$('.pt').length === 5);
    $$('.pt')[0].click();
    await until(() => $$('.anvil-modal').some((m) => vis(m) && m.querySelector('.fn')), 'find dialog');
    await sleep(1800);
    await axeRun('find dialog');
    $$('.anvil-modal button').find((b) => /Back to the cake/.test(b.textContent)).click();
    await sleep(600);
    // sign up so the member pages can be checked too
    await page('#auth/signup', () => $$('.au-card input').length >= 3);
    const inputs = $$('.au-card input[type=text], .au-card input[type=email], .au-card input[type=password]');
    type(inputs[0], 'Access Tester'); type(inputs[1], 'a11y' + Date.now() + '@example.com'); type(inputs[2], 'Hb-' + Math.random().toString(36).slice(2) + '-Kq7');
    const box = $('.au-card input[type=checkbox]'); if (box && !box.checked) box.click();
    $$('.anvil-role-btn-block button').find((b) => /Create account/.test(b.textContent)).click();
    await until(() => location.hash === '#home' && window.UI_READY, 'signed in', 30000);
    await until(() => !$$('[data-notify="container"], .anvil-notification').some(vis), 'the welcome toast to go', 9000);
    for (const h of await memberPages()) await scan(h);
    // dialogs a grown-up uses: hunt settings, treasure editor, task picker, share
    await page('#home', () => $$('.hc').length >= 4);
    $$('.anvil-role-btn-primary button').find((b) => /Bake a new hunt/.test(b.textContent)).click();
    await until(() => $$('.anvil-modal').some((m) => vis(m) && m.querySelector('.hs')), 'settings dialog');
    await sleep(1800);
    await axeRun('hunt settings dialog');
    $$('.anvil-modal button').find((b) => vis(b) && /Cancel/.test(b.textContent)).click();
    await sleep(600);
    log.push(bad.length ? 'PROBLEMS: ' + bad.join(' | ') : 'PASSED');
    return { ok: !bad.length, log: log };
  } catch (e) {
    log.push(String(e && e.message || e));
    return { ok: false, log: log };
  }
})();
