# PhotoHunt

Birthday-party photo treasure hunts for kids. A grown-up snaps 5 to 10 things around the house (or records spoken
clues, or picks party tasks), shows a QR code, and kids on a phone or tablet race to find and photograph the same
things. Every find lights a candle on a birthday cake; at the end the kids blow on the tablet to blow the candles out.
Built on [Anvil](https://anvil.works) as native Anvil Forms (Python + HTML templates, a layout, custom components,
RepeatingPanels).

- **App repo:** github.com/arkulinskis/photohunt (branch `master`). Anvil pulls `master`.
- **Live:** not published yet (planned https://photohunt.anvil.app)

## What it does

**For grown-ups (account, 16+)**
- **Party HQ** (`#home`): your hunts as cake cards (flavour colours, status, code), your kids, five example hunts to open,
  play or copy ("Make one like this").
- **Bake a hunt** (settings dialog): name, birthday kid + age, kind (Photo hunt, Voice hunt, Task party, Party mix, Photo bingo), cake
  flavour (strawberry, chocolate, vanilla, mint choc, blueberry, lemon), time limit (none to 1 hour), race (own cake each)
  or together (one team cake), start together (grown-up presses Start) or self-start (each kid's own clock), photo
  checking (Magic match with easy / just right / tricky, I check every photo, every photo counts), a message for the kids.
- **Hunt kitchen** (`#hunt/<id>`): snap treasures with the live camera or "Choose a photo", name + clue, a voice clue
  recorded in your voice, tasks from the library of 100 or written yourself (timer, "tap when done" or "snap a photo"),
  reorder, edit, delete, a recorded welcome message, Share (QR code, code, link, printable party card), copy, delete.
  Example hunts open read-only.
- **Live board** (`#live/<id>`, refreshes every 3 s): Start, +5 minutes, End, Play again; the clock; photos to check
  (your photo next to the kid's, yes / try again); players with candle bars, "Here" and "In the lead"; the team cake;
  the join QR for latecomers; what's happening.
- **Party album** (`#album/<id>`): results with stickers, every treasure with each kid's snap (polaroids), printable
  certificates (one page per kid), "Delete kids' photos".
- **Kids** (`#family`): kid profiles (first name, cake-topper avatar, colour) and each one's private Kids' corner link as a
  QR code (new link stops the old one).
- **100 party tasks** (`#tasks`, public): 7 categories, search, "Hear it" (a recorded voice per task, theme/assets/voices, `tools/make_task_voices.py`); signed-in grown-ups add ticked
  tasks to a task hunt.

**For kids (no account)**
- **Join** (`#join`, `#join/<code>`): type the 6-letter code or scan the QR in the app (BarcodeDetector or jsQR);
  name or team name, cake topper, colour, Let's hunt. The tablet remembers games and Kids' corners.
- **Play** (`#play/<token>`, no header): lobby (wait for Start, hear the welcome) or Go! (own clock), 3-2-1 countdown,
  the cake with one candle per treasure, big tiles (photo, mystery card for voice hunts, task star), the race
  scoreboard, the clock, sound on/off.
- **Find screen** (dialog): the photo or the riddle/clue read aloud (the grown-up's recording, the library task's recorded voice, or the device voice), task timer, live
  camera with a faint "ghost" of the grown-up's photo, Snap!, then You found it! (ding + sprinkles) / So close / Not
  quite, Ask a grown-up (a grown-ups-only sum, then yes/no on the spot) or send it to the grown-up's board.
- **The end**: full cake or time's up, place in the race, stickers (party hat, whole cake, first find, speedy, winner,
  sharp eyes, good ears, task star, team cake), blow out the candles (microphone; or tap), results.
- **Kids' corner** (`#kid/<token>`): hello, join a hunt with one tap (no name to type), my hunts, my sticker book.
- **Photo bingo** (kind `bingo`, for little ones): the treasures become a bingo card (2x2 up to 4, 3 across up to 9,
  then 4 across) of big pictures with names; opening one says "Find the teddy!" at once; found pictures get a stamp;
  a full row, column or diagonal is a BINGO (big banner, confetti, the row lights up, the Bingo! sticker); the full card
  lights every candle. Picking it for a new hunt sets no time limit and easy matching.
- **Task voices**: every library task has a friendly recorded voice (Kokoro af_heart, theme/assets/voices/<id>.mp3,
  `tools/make_task_voices.py`); a task the grown-up rewords, or a clip that won't play, falls back to the device voice.

**Magic match**: the browser makes a 212-number fingerprint of each photo (colour bins, edge directions, layout:
theme/assets/ph-cam.js `PH.sig64`); the server scores it against the grown-up's (server_code/Vision.py). Calibrated with
`python tools/testing/vision_test.py` (retakes vs different photos).

**Demo**: five example hunts drawn with cartoon objects (theme/assets/demo-*.svg, `tools/make_demo_art.py`): a finished
race with five players (album), the Try-me Hunt **CAKE42** anyone can play (any photo counts, no photos kept), a task party
in the lobby, a voice riddle hunt. Little Sam's Photo Bingo, code **BINGO9**, is open to anyone like CAKE42 (a 3x3 card).

## Setting it up in Anvil (once)

1. Anvil editor: **Create app → Clone from GitHub**, paste `https://github.com/arkulinskis/photohunt`.
2. Check the **Users** service (email + password, Continue with Google, sign-up on).
3. Accept the **Schema Mismatch** alert with **"The schema of the source code is correct"**.
4. Run it, sign up with the admin email first, then **Publish**.

<!-- libraries:start -->
## Libraries and outside services

What this project uses besides its own code. Generated by `APP_MAKER/tools/libraries.py`; to change it, edit `APP_MAKER/libraries/catalog.py` and re-run the script.

| Name | How it gets in | Used here for |
|---|---|---|
| [qrcode-generator](https://github.com/kazuhikoarase/qrcode-generator) | Loaded from a CDN | the QR code kids scan to join a hunt, and each Kids' corner link (its own copy, theme/assets/ph-qrgen.js) |
| [jsQR](https://github.com/cozmo/jsQR) | Loaded from a CDN | kids scan a hunt's QR code with the tablet camera inside the app (theme/assets/ph-qrscan.js) |
| [Google Fonts](https://fonts.google.com) | Loaded from a CDN | Grandstander, Nunito |

**Built into the browser:** Canvas 2D, Speech synthesis, Web Audio API, Camera, microphone and screen, MediaRecorder, BarcodeDetector, localStorage, Clipboard, File downloads (Blob).

**Anvil platform:** Anvil, Anvil Data Tables, Anvil JS bridge (anvil.js), Anvil Users, Anvil Google service.

**Build and test tools (not shipped):** axe-core, Node.js, Headless Chrome (DevTools Protocol), PyYAML.

<!-- libraries:end -->

## Working on it

See `.claude/skills/photohunt/SKILL.md`. In short:

```
python tools/check.py                    # Anvil's validator, JS syntax, asset hashes, server tests -> ALL CHECKS PASSED
python -I tools/ui_test.py               # the real app in the Anvil App Server (Docker) driven by headless Chrome
python -I tools/ui_test.py --shots DIR   # + screenshots of every page (desktop/phone, light/dark, guest/member)
git push origin master                   # deploy
```

## Project layout

```
client_code/    startup.py, router.py, state.py, auth.py, legal.py; Layouts/Shell, Pages/*, Components/*, Items/*, Dialogs/*
server_code/    common.py, Accounts.py, Admin.py, DemoData.py, Feedback.py, Game.py (rules), Hunts.py (grown-ups), Play.py (kids),
                Family.py, Media.py (photo/voice endpoints), Vision.py (Magic match), TaskLibrary.py, SchemaCheck.py, legal_server.py
theme/assets/   app.css, icons.css (generated), app-kit.js, theme.css (spinner), icon.svg + PNG icons,
                ph-art.js (cake, toppers, stickers, QR), ph-cam.js (camera, fingerprint, scanner, recorder, sounds, confetti),
                ph-qrgen.js (qrcode-generator, MIT), ph-qrscan.js (jsQR, Apache-2.0), demo-*.svg
tools/          check.py, assets.py, build_icons.py, make_icons.py, ui_test.py + ui/, live/drive.mjs, testing/
```
