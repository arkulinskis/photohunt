from anvil import *

from ._anvil_designer import PlayTileTemplate

STATE = {"found": "Found!", "review": "Checking...", "rejected": "Try again", "todo": ""}


class PlayTile(PlayTileTemplate):
    """A treasure on the kid's play screen: a big button with its picture (or a mystery card, or a task star), and
    Found! / Checking... / Try again. A click raises x-open. item = the play treasure dict (+ _bingo: a square on a
    photo bingo card, stamped when found; _line: part of a finished BINGO line)."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        task = t["kind"] == "task"
        st = t.get("state", "todo")
        mystery = (not task) and not (t.get("photo_key") or t.get("art"))
        self.dom_nodes["num"].textContent = str(t["position"])
        self.photo.visible = not task
        self.dom_nodes["task"].style.display = "grid" if task else "none"
        self.photo.photo_key = t.get("find_photo_key") if (st == "found" and t.get("find_photo_key") and mystery) else (t.get("photo_key") or "")
        self.photo.art = t.get("art") or ""
        self.photo.mystery = mystery and st != "found"
        self.photo.alt = "" if mystery else t["name"]
        if task:
            name = t["name"]
        elif mystery and st != "found":
            name = "Mystery treasure %d" % t["position"]
        else:
            name = t["name"]
        self.dom_nodes["name"].textContent = name
        self.dom_nodes["state"].textContent = STATE.get(st, "") if not (t.get("by") and st == "found") else "Found by " + t["by"]
        b = self.dom_nodes["btn"]
        for s in ("found", "review", "rejected", "todo"):
            b.classList.toggle("is-" + s, st == s)
        b.setAttribute("aria-label", "%s%s" % (name, (": " + STATE[st]) if STATE.get(st) else ""))
        b.setAttribute("data-key", t["id"])
        b.classList.toggle("bingo", bool(t.get("_bingo")))
        b.classList.toggle("in-line", bool(t.get("_line")))

    def btn_click(self, event):
        self.parent.raise_event("x-open", treasure=self.item)
