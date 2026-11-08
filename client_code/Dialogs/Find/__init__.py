import random

import anvil.server
from anvil import *
from anvil.js import window

from ._anvil_designer import FindTemplate
from ... import ph


class Find(FindTemplate):
    """The kid's screen for one treasure: see it (or hear the clue), take a picture, find out if it matches.
    For tasks: hear it, run the timer, then "I did it!" or a photo. A grown-up can say yes on the spot after a little
    sum only grown-ups solve quickly. Closes with the newest play state (or None if nothing changed)."""

    def __init__(self, treasure, hunt, token, total, **properties):
        super().__init__(**properties)
        self.t, self.h, self.token = treasure, hunt, token
        self.result_state = None
        self._media = None
        self._sig = None
        self._find_id = None
        self._tick = 0
        self._left = 0
        self._gate_answer = 0
        self._gate_then = ""
        self._hidden = False
        task = treasure["kind"] == "task"
        mystery = (not task) and not (treasure.get("photo_key") or treasure.get("art"))
        self.mystery = mystery
        self.number.text = ("Task %d of %d" if task else "Treasure %d of %d") % (treasure["position"], total)
        self.title.text = "Mystery treasure" if mystery else treasure["name"]
        self.pic_box.visible = not task
        self.task_box.visible = task
        self.task_text.text = treasure["clue"] or treasure["name"] if task else ""
        self.photo.photo_key, self.photo.art, self.photo.mystery = treasure.get("photo_key") or "", treasure.get("art") or "", mystery
        self.photo.alt = treasure["name"] if not mystery else ""
        clue_text = treasure.get("clue") or ""
        speak = (treasure["clue"] or treasure["name"]) if task else (clue_text or ("Find %s!" % treasure["name"] if not mystery else ""))
        self.voice.voice_key, self.voice.text = treasure.get("voice_key") or "", speak
        self.voice.lib_id = (treasure.get("lib_voice") or "") if task else ""
        self.voice.label = "Hear the task" if task else ("Hear the riddle" if mystery else "Hear the clue")
        self.voice.visible = bool(treasure.get("voice_key") or speak)
        self.clue.text = "" if task else clue_text
        self.clue.visible = bool(self.clue.text)
        self.timer_box.visible = task and bool(treasure.get("timer"))
        self.timer_label.text = ph.clock(treasure.get("timer") or 0)
        ghost = "" if mystery else ph.photo_url(treasure.get("photo_key"), treasure.get("art"))
        self.camera.ghost_url = ghost or ""
        self._mode("show")
        little = hunt.get("kind") == "bingo"   # photo bingo: little ones hear "Find the teddy!" straight away
        if little and not task and not clue_text:
            nm = treasure["name"]
            self.voice.text = ("Find the %s!" % nm.lower()) if len(nm.split()) <= 2 else ("Find %s!" % nm)
        if mystery or little or (task and (treasure.get("voice_key") or treasure.get("lib_voice"))):
            window.setTimeout(lambda: self.voice.play(True), 350)

    # ---- which parts show
    def _mode(self, mode):
        task = self.t["kind"] == "task"
        photo_proof = (not task) or self.t.get("proof") == "photo"
        self.mode = mode
        self.show_box.visible = mode == "show"
        self.cam_box.visible = mode == "camera"
        self.result_box.visible = mode in ("result", "confirm")
        self.gate_box.visible = mode == "gate"
        self.found_button.visible = mode == "show" and photo_proof
        self.found_button.text = "I did it! Take a picture" if task else "I found it! Take a picture"
        self.done_button.visible = mode == "show" and not photo_proof
        self.yes_button.visible = mode == "confirm"
        self.retry_button.visible = False
        self.ask_button.visible = False
        self.send_button.visible = False
        self.back_button.visible = mode != "checking"
        self.back_button.text = "Back to the cake" if mode != "camera" else "Not yet"
        self.message.visible = False
        if mode != "camera":
            self.camera.stop()

    # ---- task timer
    @handle("timer_button", "click")
    def timer_button_click(self, **event_args):
        if self._tick:
            return
        self._left = int(self.t.get("timer") or 0)
        self.timer_button.enabled = False
        self._tick = window.setInterval(self._step, 1000)
        ph.sfx("go")

    def _step(self):
        self._left -= 1
        self.timer_label.text = ph.clock(self._left)
        if self._left <= 3 and self._left > 0:
            ph.sfx("tick")
        if self._left <= 0:
            window.clearInterval(self._tick)
            self._tick = 0
            self.timer_button.enabled = True
            self.timer_button.text = "Again"
            ph.sfx("tada")

    # ---- taking the picture
    @handle("found_button", "click")
    def found_button_click(self, **event_args):
        ph.stop_sound()
        self._mode("camera")
        self.camera.start()

    @handle("retry_button", "click")
    def retry_button_click(self, **event_args):
        self._mode("camera")
        self.camera.start()

    @handle("camera", "snapped")
    def camera_snapped(self, media, sig, url, **event_args):
        self._media, self._sig = media, sig
        self.snap.src = url
        self._submit(False)

    @handle("done_button", "click")
    def done_button_click(self, **event_args):
        ph.stop_sound()
        self._media, self._sig = None, None
        self.snap.visible = False
        self._submit(False)

    def _submit(self, ask):
        self._mode("result")
        self.verdict.text, self.verdict_sub.text = "Checking...", ""
        r = anvil.server.call("submit_find", self.token, self.t["id"], self._media, self._sig, ask)
        if not r.get("ok"):
            self._mode("show")
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.result_state = r
        mine = next((x for x in r["treasures"] if x["id"] == self.t["id"]), {})
        self._find_id = mine.get("find_id")
        self._show_result(r.get("result"), r.get("message") or "")

    def _show_result(self, result, message):
        self._mode("result")
        task = self.t["kind"] == "task"
        if result == "found":
            ph.sfx("ding")
            ph.confetti()
            self.verdict.text = "You did it!" if task else "You found it!"
            self.verdict_sub.text = "A candle is lit on the cake!"
            self.back_button.text = "Back to the cake"
            window.setTimeout(self._auto_close, 1900)
        elif result == "review":
            ph.sfx("pop")
            self.verdict.text = "A grown-up will check it"
            self.verdict_sub.text = "Keep hunting! Is a grown-up next to you?"
            self.ask_button.text, self.ask_button.visible = "A grown-up is here", True
            self._gate_then = "approve"
        elif result == "close":
            ph.sfx("oops")
            self.verdict.text = "So close!"
            self.verdict_sub.text = "Ask a grown-up to check it, or try again."
            self.retry_button.visible = True
            self.ask_button.text, self.ask_button.visible = "Ask a grown-up", True
            self.send_button.visible = True
            self._gate_then = "confirm"
        else:
            ph.sfx("oops")
            self.verdict.text = "Hmm, not quite!"
            self.verdict_sub.text = message if message and "not quite" not in message.lower() else "Look again and try another picture."
            self.retry_button.visible = True
            self.ask_button.text, self.ask_button.visible = "Ask a grown-up", True
            self.send_button.visible = True
            self._gate_then = "confirm"

    def _auto_close(self):
        if self.mode == "result" and not self._hidden:
            self.raise_event("x-close-alert", value=self.result_state)

    # ---- grown-up check: a quick sum, then yes / no
    @handle("ask_button", "click")
    def ask_button_click(self, **event_args):
        a, b = random.randint(6, 15), random.randint(4, 9)
        self._gate_answer = a + b
        wrong = set()
        while len(wrong) < 2:
            w = a + b + random.choice([-3, -2, -1, 1, 2, 3])
            if w != a + b:
                wrong.add(w)
        answers = [a + b] + list(wrong)
        random.shuffle(answers)
        self.gate_q.text = "Grown-ups only: what is %d + %d?" % (a, b)
        for btn, v in zip((self.a1, self.a2, self.a3), answers):
            btn.text = str(v)
            btn.tag = v
        self._mode("gate")

    @handle("a1", "click")
    def a1_click(self, **event_args):
        self._answer(self.a1.tag)

    @handle("a2", "click")
    def a2_click(self, **event_args):
        self._answer(self.a2.tag)

    @handle("a3", "click")
    def a3_click(self, **event_args):
        self._answer(self.a3.tag)

    def _answer(self, value):
        if value != self._gate_answer:
            ph.sfx("oops")
            self._mode("result")
            self.verdict.text, self.verdict_sub.text = "Oops!", "That's a grown-up question. Ask a grown-up to help."
            self.retry_button.visible = True
            return
        if self._gate_then == "approve" and self._find_id:
            self._approve()
            return
        self._mode("confirm")
        self.verdict.text = "Grown-up: is this the right thing?"
        self.verdict_sub.text = "The task: " + (self.t["clue"] or self.t["name"]) if self.t["kind"] == "task" else "It should be: " + self.t["name"]
        self.retry_button.text, self.retry_button.visible = "No, try again", True

    @handle("yes_button", "click")
    def yes_button_click(self, **event_args):
        r = anvil.server.call("submit_find", self.token, self.t["id"], self._media, self._sig, True)
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.result_state = r
        mine = next((x for x in r["treasures"] if x["id"] == self.t["id"]), {})
        self._find_id = mine.get("find_id")
        if mine.get("state") == "found":
            self._show_result("found", "")
            return
        self._approve()

    def _approve(self):
        r = anvil.server.call("grownup_check", self.token, self._find_id, True)
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.result_state = r
        self._show_result("found", "")

    @handle("send_button", "click")
    def send_button_click(self, **event_args):
        self._submit(True)

    @handle("back_button", "click")
    def back_button_click(self, **event_args):
        ph.stop_sound()
        self.raise_event("x-close-alert", value=self.result_state)

    @handle("", "hide")
    def form_hide(self, **event_args):
        self._hidden = True
        self.camera.stop()
        if self._tick:
            window.clearInterval(self._tick)
            self._tick = 0
