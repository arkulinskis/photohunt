import anvil.js
import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import ShowTemplate
from ... import ph, router, state

SECONDS = 5          # each slide stays this long while playing
MAX_SNAPS = 8        # kids' photos on one treasure slide


class Show(ShowTemplate):
    """#show/<id>, the party show: a full-screen slideshow of the party for the TV while the cake comes out. A title
    card, every treasure with the grown-up's photo and the kids' snaps, one award card per kid, then a happy-birthday
    finale. Plays by itself (Pause, Back, Next, arrow keys, space); only the hunt's owner (or an example hunt).
    Uses album() so it shows exactly what the album shows (deleted photos stay deleted)."""

    def __init__(self, args=(), **properties):
        super().__init__(**properties)
        self.hid = args[0] if args else ""
        self.slides: list = []
        self.i = 0
        self.playing = not _reduced_motion()
        self._shown = False
        self._timer = 0
        self._elapsed = 0.0
        self._keys = anvil.js.report_exceptions(self._key)
        state.heading(self.headline, 1)
        self.snaps_panel.role = ["show-snaps"]
        r: dict = {"ok": False}
        if self.hid:
            try:
                r = anvil.server.call("album", self.hid)
            except Exception:
                r = {"ok": False}
        self.gone.visible = not r.get("ok")
        self.main.visible = bool(r.get("ok"))
        if r.get("ok"):
            self._build(r)
            state.set_attr(self.back_link, "href", router.href("album", self.hid))
            self._go(0)

    # ---- the slides
    def _build(self, r):
        h = r["hunt"]
        total = len(r["treasures"])
        who = h.get("birthday_name") or ""
        players = r["players"]
        self.h = h
        self.slides = [{"kind": "title", "title": h["title"],
                        "sub": ("%s's party · %s · %s" % (who, state.plural(len(players), "hunter"), state.plural(r["photos"], "photo")))
                        if who else "%s · %s" % (state.plural(len(players), "hunter"), state.plural(r["photos"], "photo")),
                        "total": total}]
        for t in r["treasures"]:
            finds = t.get("finds") or []
            if not finds:
                continue
            names = [f["player"] for f in finds]
            if len(names) == 1:
                found_by = "Found by %s" % names[0]
            elif len(names) <= 4:
                found_by = "Found by %s and %s" % (", ".join(names[:-1]), names[-1])
            else:
                found_by = "%d hunters found it" % len(names)
            if t.get("kind") == "task":
                found_by = found_by.replace("Found by", "Done by").replace("found it", "did it")
            self.slides.append({"kind": "treasure", "title": t.get("name") or "A treasure", "sub": found_by,
                                "photo_key": t.get("photo_key") or "", "art": t.get("art") or "",
                                "snaps": finds[:MAX_SNAPS]})
        for p in players:
            if not p.get("award"):
                continue
            self.slides.append({"kind": "award", "title": p["name"], "award": p["award"], "topper": p["topper"],
                                "colour": p["colour"],
                                "sub": "%d of %d candles" % (p.get("found", 0), p.get("total", total))})
        self.slides.append({"kind": "finale", "title": ("Happy birthday, %s!" % who) if who else "Thanks for hunting!",
                            "sub": "Every hunter is a winner today. Time for cake!", "total": total})

    def _go(self, i):
        if not self.slides:
            return
        self.i = i % len(self.slides)
        self._elapsed = 0.0
        s = self.slides[self.i]
        k = s["kind"]
        self.cake_box.visible = k in ("title", "finale")
        self.pics_box.visible = k == "treasure"
        self.star_box.visible = k == "award"
        for kind in ("title", "treasure", "award", "finale"):
            self.slide.classes["show-" + kind] = kind == k
        node = anvil.js.get_dom_node(self.slide)
        if node is not None:   # play the slide's entrance again
            node.style.animation = "none"
            _ = node.offsetWidth
            node.style.animation = ""
        self.headline.text = s["title"]
        self.subline.text = s.get("sub") or ""
        self.award.award = s.get("award") if k == "award" else None
        if k in ("title", "finale"):
            self.cake.flavour = self.h.get("flavour") or "strawberry"
            self.cake.total = max(1, s.get("total") or 1)
            self.cake.lit = self.cake.total
            self.cake.blown = False
        if k == "treasure":
            has_orig = bool(s["photo_key"] or s["art"])
            self.orig_box.visible = has_orig
            self.orig.photo_key, self.orig.art = s["photo_key"], s["art"]
            self.orig.alt = "The grown-up's photo of %s" % s["title"]
            self.snaps_panel.items = s["snaps"]
            self.snaps_panel.role = ["show-snaps", "show-snaps-%d" % min(len(s["snaps"]), MAX_SNAPS)]
        if k == "award":
            self.topper.topper, self.topper.colour = s["topper"], s["colour"]
        self.counter.text = "%d / %d" % (self.i + 1, len(self.slides))
        self._bar()
        if k == "finale" and self._shown:
            ph.confetti()
            ph.sfx("tada")
        elif k == "award" and self._shown and self.playing:
            ph.sfx("ding")

    def _bar(self):
        frac = min(1.0, self._elapsed / SECONDS) if self.playing else 0
        whole = (self.i + frac) / max(1, len(self.slides))
        self.dom_nodes["bar"].style.transform = "scaleX(%.3f)" % whole

    def _tick(self):
        if not self._shown or not self.playing or not self.slides:
            return
        self._elapsed += 0.5
        if self._elapsed >= SECONDS:
            if self.i >= len(self.slides) - 1:
                self._set_playing(False)    # the finale stays up
                return
            self._go(self.i + 1)
        else:
            self._bar()

    def _set_playing(self, on):
        self.playing = bool(on)
        self.play_button.text = "Pause" if self.playing else "Play"
        self.play_button.role = ["btn", "btn-primary", "ic-pause" if self.playing else "ic-play"]
        self._elapsed = 0.0
        self._bar()

    # ---- page life
    @handle("", "show")
    def form_show(self, **event_args):
        self._shown = True
        window.document.addEventListener("keydown", self._keys)
        if self.slides and not self._timer:
            self._timer = window.setInterval(self._tick, 500)
        self._set_playing(self.playing)

    @handle("", "hide")
    def form_hide(self, **event_args):
        self._shown = False
        window.document.removeEventListener("keydown", self._keys)
        if self._timer:
            window.clearInterval(self._timer)
            self._timer = 0
        self._exit_fullscreen()

    def _key(self, event):
        if not self._shown or not self.slides:
            return
        tag = str(getattr(event.target, "tagName", "") or "").lower()
        if tag in ("input", "textarea", "select"):
            return
        key = event.key
        if key in ("ArrowRight", "PageDown"):
            event.preventDefault()
            self.next_button_click()
        elif key in ("ArrowLeft", "PageUp"):
            event.preventDefault()
            self.prev_button_click()
        elif key == " " and tag != "button":
            event.preventDefault()
            self.play_button_click()

    # ---- controls
    @handle("prev_button", "click")
    def prev_button_click(self, **event_args):
        self._go(self.i - 1)

    @handle("next_button", "click")
    def next_button_click(self, **event_args):
        self._go(self.i + 1)

    @handle("play_button", "click")
    def play_button_click(self, **event_args):
        if not self.playing and self.i >= len(self.slides) - 1:
            self._go(0)   # Play at the end starts the show again
        self._set_playing(not self.playing)

    @handle("full_button", "click")
    def full_button_click(self, **event_args):
        doc = window.document
        if doc.fullscreenElement:
            self._exit_fullscreen()
            return
        node = doc.documentElement
        req = getattr(node, "requestFullscreen", None) if node is not None else None
        try:
            if req is None:
                raise RuntimeError("no fullscreen")
            req()
        except Exception:
            state.toast("This browser can't go full screen. Use the TV's or browser's zoom instead.", "error")

    def _exit_fullscreen(self):
        doc = window.document
        try:
            if doc.fullscreenElement:
                doc.exitFullscreen()
        except Exception:
            pass


def _reduced_motion():
    try:
        return bool(getattr(window.matchMedia("(prefers-reduced-motion: reduce)"), "matches", False))
    except Exception:
        return False
