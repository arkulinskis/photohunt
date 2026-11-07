import anvil.server
from anvil import *

from ._anvil_designer import TreasureEditTemplate
from ... import ph


class TreasureEdit(TreasureEditTemplate):
    """Add or change one treasure: a thing to find (photo, name, clue, voice) or a task (text, voice, timer, proof).
    hunt = the hunt dict, treasure = the treasure dict ({} = new), kind = "find" or "task". Closes with the saved
    treasure, or None."""

    def __init__(self, hunt, treasure, kind, **properties):
        super().__init__(**properties)
        self.h, self.t = hunt, treasure or {}
        self.kind = self.t.get("kind") or kind
        self._photo = None      # new photo: (media, sig, url)
        self._remove_photo = False
        self._voice = None      # new recording: (media, seconds)
        self._remove_voice = False
        task = self.kind == "task"
        new = not self.t.get("id")
        self.dom_nodes["heading"].textContent = ("New task" if new else "Edit task") if task else ("New treasure" if new else "Edit treasure")
        self.photo_side.visible = not task
        self.task_opts.visible = task
        self.dom_nodes["name_cap"].textContent = "The task" if task else "What is it?"
        self.name_box.placeholder = "Do 10 jumping jacks!" if task else "The red teapot"
        self.dom_nodes["clue_cap"].innerHTML = "More about it <em>(optional)</em>" if task else "Clue <em>(optional, kids can hear it)</em>"
        self.clue_box.placeholder = "Count them out loud!" if task else "It lives in the kitchen and loves tea parties."
        self.recorder.prompt = "Record the task" if task else "Record the clue"
        self.recorder.voice_key = self.t.get("voice_key") or ""
        self.name_box.text = self.t.get("name", "")
        self.clue_box.text = self.t.get("clue", "") if self.t.get("clue") != self.t.get("name") else ""
        self.timer_drop.items = [("No timer", 0), ("10 seconds", 10), ("15 seconds", 15), ("20 seconds", 20), ("30 seconds", 30),
                                 ("1 minute", 60), ("2 minutes", 120)]
        self.timer_drop.selected_value = self.t.get("timer", 0) or 0
        self.proof_drop.items = [("Tapping \"I did it!\"", "done"), ("Snapping a photo", "photo")]
        self.proof_drop.selected_value = self.t.get("proof") or "done"
        voice_hunt = hunt.get("kind") == "voice"
        self.photo_hint.text = ("Kids won't see this photo until they find it: they hear your clue instead. The app uses it to check their snap."
                                if voice_hunt else "Snap it the way a kid would see it. The app compares their photo with yours.")
        self.cam_view.visible = False
        self._draw_photo()

    def _draw_photo(self):
        if self._photo:
            self.photo.src = self._photo[2]
        else:
            self.photo.src = ""
            self.photo.photo_key = "" if self._remove_photo else (self.t.get("photo_key") or "")
            self.photo.art = "" if self._remove_photo else (self.t.get("art") or "")
        has = bool(self._photo) or (not self._remove_photo and bool(self.t.get("photo_key") or self.t.get("art")))
        self.snap_button.text = "Take a new photo" if has else "Take a photo"
        self.unphoto_button.visible = has

    @handle("", "show")
    def form_show(self, **event_args):
        self.name_box.focus()

    @handle("snap_button", "click")
    def snap_button_click(self, **event_args):
        self.photo_view.visible = False
        self.cam_view.visible = True
        self.camera.start()

    @handle("cam_cancel", "click")
    def cam_cancel_click(self, **event_args):
        self.camera.stop()
        self.cam_view.visible, self.photo_view.visible = False, True

    @handle("camera", "snapped")
    def camera_snapped(self, media, sig, url, **event_args):
        self.camera.stop()
        self._photo, self._remove_photo = (media, sig, url), False
        self.cam_view.visible, self.photo_view.visible = False, True
        self._draw_photo()

    @handle("unphoto_button", "click")
    def unphoto_button_click(self, **event_args):
        self._photo, self._remove_photo = None, True
        self._draw_photo()

    @handle("recorder", "recorded")
    def recorder_recorded(self, media, seconds, **event_args):
        self._voice, self._remove_voice = (media, seconds), False

    @handle("recorder", "removed")
    def recorder_removed(self, **event_args):
        self._voice, self._remove_voice = None, True

    @handle("cancel_button", "click")
    def cancel_button_click(self, **event_args):
        self.camera.stop()
        self.raise_event("x-close-alert", value=None)

    @handle("save_button", "click")
    def save_button_click(self, **event_args):
        name = (self.name_box.text or "").strip()
        if not name:
            self.message.text = "Say what the task is." if self.kind == "task" else "Give it a name, like \"the red teapot\"."
            self.message.visible = True
            self.name_box.focus()
            return
        fields = {"kind": self.kind, "name": name, "clue": self.clue_box.text or "", "timer": self.timer_drop.selected_value,
                  "proof": self.proof_drop.selected_value if self.kind == "task" else "photo",
                  "remove_photo": self._remove_photo, "remove_voice": self._remove_voice}
        media, sig = (self._photo[0], self._photo[1]) if self._photo else (None, None)
        voice, secs = self._voice if self._voice else (None, 0)
        self.save_button.enabled = False
        try:
            r = anvil.server.call("save_treasure", self.h["id"], self.t.get("id"), fields, media, sig, voice, secs)
        finally:
            self.save_button.enabled = True
        if not r.get("ok"):
            self.message.text, self.message.visible = r.get("error") or "That didn't work.", True
            return
        self.camera.stop()
        self.raise_event("x-close-alert", value=r["treasure"])
