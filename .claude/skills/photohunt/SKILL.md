---
name: photohunt
description: Context, workflow and recipes for PhotoHunt (folder photohunt), the user's Anvil app built as native Anvil Forms (Python + HTML templates, a layout, custom components, RepeatingPanels). Birthday-party photo treasure hunts: grown-ups snap things around the house, kids scan a QR code and find and photograph them to light candles on a cake. Load this before any feature request, bug fix, restyle, content change or deploy for this app.
---

# PhotoHunt: working on the app

**What it is:** grown-ups (accounts) bake hunts: photos of things to find, spoken clues, party tasks (100 in a library).
Kids (no accounts) join with a code/QR on a tablet, find and snap each thing, Magic match (or a grown-up) confirms, a
candle lights. Areas: Party HQ, hunt kitchen, live board, party album, kids + Kids' corner, the public task library, and
the kids' join / play / find screens. README.md lists every feature.

**Where it lives:**
- Folder `C:\Users\arkvi\Documents\CLAUDE\photohunt\` = the git clone of **github.com/arkulinskis/photohunt**, branch `master`.
  "git" layout: the folder *is* the Anvil app. Anvil pulls master; pushing is the deploy. Live: not published yet.
- Made from `C:\Users\arkvi\Documents\CLAUDE\APP_MAKER\template-forms` (native Anvil Forms, Nov 2026). Anvil's own agent
  skills describe the same model: `client-forms`, `data-models`, `server-code`, `client-modules`, `anvil-yaml`
  (github.com/anvil-works/anvil-agent-references; see APP_MAKER/ANVIL_NOTES.md, "Native Anvil Forms").
- **README.md** lists every feature. Keep it up to date.

**What the user wants:** "kids birthday party like a birthday cake". Strawberry-milk page #FFF4F6, raspberry brand
#C2255C, candle-flame accent #FFC234, chocolate ink #3A1E2A; dark mode = a chocolate cake (#22131A, brand #FF7DAA).
Grandstander (display) + Nunito (body), 22px radius, soft pink shadows, sprinkles only on the cake and in confetti.
The cake (PH.cake) is the brand: one candle per treasure. Kid screens: huge tiles, 48px+ targets, sounds (muteable),
no header. Loader preset "fill". Claude assumes
details and builds; Claude deploys. Mobile-first: every page must fit 390 px. Light and dark.

## Workflow for any change

1. `git pull --ff-only` (Anvil commits "Edited ..." when the user changes something in the IDE; read those commits).
2. Edit: a page's template and Python side by side (`client_code/Pages/X/form_template.html` + `__init__.py`).
3. `python tools/check.py` (no -I) -> **ALL CHECKS PASSED**: Anvil's validator (`anvil validate`, type-checks every
   template and Python file against Anvil's API), JS syntax, asset hashes (`tools/assets.py`), server tests.
   Needs the Anvil CLI once: `npm install -g @anvil-works/anvil-cli`.
4. `python -I tools/ui_test.py` (Docker Desktop running) -> **ALL UI TESTS PASSED**: the folder runs as-is in the
   open-source Anvil App Server (container `photohunt-dev`) and headless Chrome walks tools/ui/flow.js, phone.js
   (true 390 px, no sideways scroll), admin.js and a11y.js (axe-core WCAG 2.2 AA on every page, light + dark, plus
   keyboard checks). Client edits show on reload; server edits need `--restart`. `--only a11y.js` runs one script.
   `--shots DIR` = screenshots of every page, desktop + phone, light + dark, guest + member: Read them.
5. Commit only your files as arkulinskis with the Co-Authored-By line; `git push origin master`.
   New tables/columns: tell the user to accept the **Schema Mismatch** alert ("The schema of the source code is correct").

## Architecture

```
anvil.yaml                 startup: module `startup`; db_schema; services; head_html (fonts, Prepsto, theme assets with ?v=)
client_code/
  startup.py               get_me, Privacy & Terms kit, router.start()
  router.py                PAGES (who may open each page), NAV (main menu), _form (page -> Form), go/href/replace
  state.py                 me(), call() (expected {"ok": False} -> toast + None), toast(), store, set_attr, dates
  auth.py                  sign in / up / reset / Continue with Google / sign out
  legal.py                 Privacy & Terms (installed from APP_MAKER/legal-kit; don't edit here)
  Layouts/Shell            header + account menu + footer + phone tab bar; slot "content"; refresh(page)
  Pages/                   Landing, Auth, Home (EXAMPLE), Profile, Admin (overview, feedback, users, demo data)
  Components/              custom components (Initials = the example); wrap any JS engine here
  Items/                   RepeatingPanel item templates: NavLink, ItemCard (EXAMPLE), FeedbackRow, UserRow
  Dialogs/                 dialog Forms for alert(): AddItem (EXAMPLE)
server_code/               common.py (C.*), Accounts, Admin, DemoData, Feedback, ExampleItems (EXAMPLE), SchemaCheck
theme/assets/              app.css (tokens + pages + the role layer), icons.css (generated), app-kit.js, theme.css
                           (loading spinner), icon.svg + PNGs (tools/make_icons.py)
tools/                     check.py, assets.py, build_icons.py, make_icons.py, ui_test.py + ui/, live/drive.mjs, testing/
```

## How things are done here

- **Page** = `client_code/Pages/X/` with `<anvil-form layout="PhotoHunt.Layouts.Shell"><anvil-block slot="content">`
  and `class X(XTemplate)` taking `args=()` (the URL parts after `#x/`). Register it in router.py: `PAGES`, `_form`,
  and `NAV` if it belongs in the menu (max 4). Add its address to tools/ui/phone.js and its journey to flow.js.
- **The layout is reused between pages** (open_form keeps the Shell when the layout matches): anything in the Shell
  that depends on the user or the page goes in `Shell.refresh(page)`.
- **Navigation** = plain `<a href="#page">`; in code `router.go("page", arg)`; build links with `router.href`.
- **Static copy** = plain HTML in the template. **Text that changes** = a `Label` (role for the look).
- **Actions** = Anvil `Button` + `@handle("name", "click")`, roles `["btn", "btn-primary", "ic-plus"]`. Button roles
  are aliases of `.ui-btn` in app.css: `btn-primary`, `btn-ghost`, `btn-danger` + `btn-solid`, `btn-sm`, `btn-lg`,
  `btn-icon`, `btn-block`. Icons: role `ic-<name>` on Buttons/Links, `<i class="ic ic-<name>">` in HTML
  (names in app-kit.js `UI.ICONS`; add one there and run tools/build_icons.py).
- **Inputs** = TextBox / TextArea / DropDown / CheckBox (styled by app.css through `.ui input`, `.ui textarea`).
  Read `.text` / `.selected_value` / `.checked`; `pressed_enter` for Enter.
- **Plain HTML that changes** = `anvil:name="x"`, then `self.x.visible`, `self.x.classes["on"] = ...`,
  `self.x.style[...]`; attributes with `state.set_attr(self.x, "href", ...)`. Native clicks:
  `anvil:on-dom:click="self.x_click"` + `def x_click(self, event)`.
- **Lists** = `RepeatingPanel` + an `Items/` Form; never build repeated HTML strings. Bind fields in the item template
  (`bind:text="self.item['title']"`). Grid/flex CSS goes on the panel's items container: `.anvil-role-<role> > div`.
  Item -> page: `self.parent.raise_event("x-something", ...)` + `panel.add_event_handler("x-something", ...)`.
  Role `contents` lets a panel's items join the surrounding grid.
- **Dialogs** = a Form in `Dialogs/`, `alert(Form(...), buttons=[], role="app-dialog")`; it closes itself with
  `self.raise_event("x-close-alert", value=...)`. Yes/no: `confirm(text, title=..., buttons=[("Cancel", False), ("Delete", True)])`.
- **Toasts** = `state.toast(msg, "ok" | "error")` (Anvil Notification with roles).
- **Server calls** = `state.call("fn", ...)` for normal flows (expected `{"ok": False, "error"}` -> toast, returns None);
  a page that shows a friendly state instead (not found, private) calls `anvil.server.call` and checks `ok` itself.
  Server functions: `@anvil.server.callable(require_user=True)`, `C.require_user()` / `C.require_admin()`, ownership
  checks, return plain dicts (`C.ok(...)` / `C.fail("...")`), never other people's emails. Tables are `client: none`.
- **JavaScript** only for engines Python is too slow for (canvas, SVG drawing, WebGL, audio, maps, PDF): put it in
  `theme/assets/<name>.js`, load it in head_html (then `python tools/assets.py`), wrap it in one Python module
  (`from anvil.js import window`) and/or a `Components/` custom component. Little Hero Books is the worked example.

- **Accessibility (WCAG 2.2 AA, the legal bar; 2026-11-04)**: tools/ui/a11y.js runs axe-core on every page (light +
  dark, guest + member) and fails on serious problems; add new pages to its PUBLIC/MEMBER lists. The rules:
  - Text colours reach 4.5:1 on every surface: check new tokens (`--c-faint`, `--c-accent` used as text, status
    colours on their `-soft` fills). Text on good/bad/warn fills is `var(--c-on-status)` (white light, ink dark).
  - Every field has a name: wrap it in `<label class="ui-field"><span>Caption</span>...</label>`, or
    `state.set_control_attr(box, "aria-label", "...")` when the caption isn't a label (set it AFTER `.items` on a
    DropDown: Anvil rebuilds the select). Name/email/phone/password get `autocomplete` (set_control_attr).
  - The page's title Label is a heading: `state.heading(label, 1)` (one per page; Labels render as divs).
  - Toggle buttons say they're on: `.ui-seg` buttons get aria-pressed from the "on" class automatically (app-kit.js);
    elsewhere `state.set_control_attr(btn, "aria-pressed", ...)`. Never `role="tablist"` without real tabs.
  - Messages that appear are read out: roles msg-error/msg-note get role alert/status automatically; other changing
    Labels: `state.live(label)`. Hidden text just for screen readers: Label role `sr`.
  - When a click redraws a RepeatingPanel, keep the keyboard's place: give the item's button a `data-key` and call
    `state.refocus(panel, key)` after the event (PlanPlate's Items/Chip). Buttons have no `.focus()`: `state.focus(btn)`.
  - Images: content images get real alt text (photos: their caption); decorative ones `alt=""`; a Button icon image
    is set to alt="" automatically. Hidden anti-spam fields: `tabindex=-1`, `autocomplete=off`.

- **Design kit (2026-11-05)**: `APP_MAKER/design/README.md` is the bar for every visual change (craft floor, the
  "AI-made" tells, motion rules, worst-case data). app.css carries its CSS between `design-kit:start/end` (easing and
  duration tokens, browser surfaces, text wrapping, press feedback, gentle reduced motion): every transition uses
  `--ease-*` / `--dur-*`, no `ease-in`, no `transition: all`, no eyebrow labels, no gradient text. Checks:
  `python -I APP_MAKER/tools/design_check.py photohunt` (source; check.py prints its summary) and tools/ui/design.js
  (rendered, desktop + phone, inside ui_test.py; add new pages to its PUBLIC/MEMBER). Deliberate exceptions:
  `design-ok: <rule>` comment on the line.

## Recipes

- **New table or column:** `db_schema` in anvil.yaml (same shape as the existing tables, `client: none`), then add it
  to server tests. Deploy, then the Schema Mismatch step. Personal data -> the legal kit (below).
- **New server function:** in a server module + tests in tools/testing/test_server.py (happy path, bad input,
  someone not allowed; public ones in `PUBLIC`).
- **Demo content:** DemoData.py (`is_demo=True`, `DEMO_TABLES`, children first).
- **Restyle:** tokens at the top of app.css (light and dark blocks), fonts in head_html, the spinner in theme.css
  (`python -I APP_MAKER/tools/loaders.py apply photohunt <preset>`), `LEGAL_THEME` in startup.py.
- **Icon:** edit theme/assets/icon.svg, `python -I tools/make_icons.py`, then `python tools/assets.py`.

## App recipes

- **Rules of a hunt** live in server_code/Game.py (win_style race/together, start_mode together/self, match_mode
  magic/judge/honour, status draft/live/finished, tick() finishes on time, after_find() finishes cakes, stickers_for()).
  Self-start hunts never auto-finish (a sibling may play later).
- **Magic match thresholds**: Vision.THRESHOLD + REVIEW_BAND. Change them only with `python tools/testing/vision_test.py`
  (it fails if "normal" rejects >10% of retakes or accepts >8% of different photos).
- **Photos/voice**: Media.py serves `/_/api/photo/<key>` and `/_/api/voice/<key>` (ranges). The browser shrinks photos
  to 1024 px JPEG (ph-cam.js) and sends the fingerprint with them. Demo rows use `demo_art` (theme/assets/demo-<name>.svg)
  instead of media: `python -I tools/make_demo_art.py` redraws them.
- **New task in the library**: server_code/TaskLibrary.py `_RAW` (keep exactly 100, or change the assert and the copy
  that says 100: landing, Tasks page, task picker, README). Never reuse an id.
- **Test hook**: startup.py sets `window.phCall(name, argsJson)` so tools/ui/*.js can make hunts quickly.
- **Kids' pages** (router.KID_PAGES) get the Shell class `no-chrome` (no header, footer, tab bar).

- **Photo bingo**: Game.bingo_cols / bingo_lines / bingo_done (server), Play.state adds `bingo: {cols, lines, count}`;
  the Play page sets the tiles panel's roles `play-bingo bingo-c<cols>` and items `_bingo/_line`, and calls
  `PH.banner("BINGO!")` when the count goes up. The sticker is `bingo` (Game.stickers_for, ph.STICKERS, ph-art.js).
- **Task voices**: theme/assets/voices/<task id>.mp3. After adding or rewording a library task run
  `"C:\Program Files\Python311\python.exe" tools/make_task_voices.py --check` (records missing ones; pass ids to redo),
  then `python tools/assets.py`. test_server.py fails if a task has no clip. Game.lib_voice() sends the id only while the
  treasure's text still matches the library text; VoiceButton.lib_id plays it (PH.playOrSay falls back to the device voice).
- **Open example hunts**: CAKE42 and BINGO9 (ph.OPEN_DEMOS); DemoData.ensure_loaded reloads demo data that predates BINGO9.

## Gotchas

- A top-level page Form and a Form shown in alert() have `parent` None: guard timers with a shown/hidden flag
  (Live, Play, Dialogs/Find), never `self.parent is None`.
- Demo data loads on the first get_hq *or* hunt_preview (so CAKE42 works for a first visitor).
- headless tests use Chrome's fake camera and mic (drive.mjs flags); two fake-camera snapshots match each other, so the
  flow test uses "Choose a photo" with a different drawing to test the "not quite -> ask a grown-up" path.

- The local App Server (1.18) lags hosted Anvil: no `HtmlComponent.attrs` (use state.set_attr), `Notification(role=)`
  raises (state.toast falls back), notifications are `.anvil-alert[data-notify]`, components are wrapped in
  `<anvil-dropzone>` (app.css: `display: contents`). app.css styles both. Test on hosted Anvil too for big changes.
- Anvil's alert() without `large=True` is a 300 px modal: our role `app-dialog` widens it.
- Headless Chrome: Anvil's service worker breaks reused profiles (drive.mjs bypasses it); phone width needs device
  emulation (`MOBILE=390,844`), windows can't go below ~500 px.
- `require_secure_passwords` rejects leaked passwords: tests use random ones.
- Heredocs in the Bash tool mangle quotes: write files with the Write tool.
- A script's `el.focus()` doesn't always match `:focus-visible`, so tests check focus rings through the CSS rules,
  not computed styles. Never put `outline: none` on `input:focus` without `:not([type=checkbox]):not([type=radio])`.
- Never write Anvil's theme-colour token pattern (percent, `color:`, name, percent) in theme.css.

## Privacy & Terms (legal kit)

From `C:/Users/arkvi/Documents/CLAUDE/APP_MAKER/legal-kit`: change `apps/photohunt.json`, then there
`python -I build.py photohunt && python -I install.py photohunt` (writes theme/assets/legal-kit.js,
client_code/legal.py, server_code/legal_server.py and the head_html tag), then `python tools/assets.py` and deploy.
Sign-up keeps the tick box (`legal.consent_field()` in Pages/Auth). Feedback = Prepsto only ("Submit feedback").
- Client and server modules share ONE Python package: a server module can't have the same name as a client
  package or module (server `Items.py` + client `Items/` = "Cannot resolve imported module"). The template's example
  server module is `ExampleItems.py` for that reason.
