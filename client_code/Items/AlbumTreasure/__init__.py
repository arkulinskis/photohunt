from anvil import *

from ._anvil_designer import AlbumTreasureTemplate
from ... import state


class AlbumTreasure(AlbumTreasureTemplate):
    """A treasure in the party album: the grown-up's photo, then every kid's snap of it."""

    def __init__(self, **properties):
        super().__init__(**properties)
        t = self.item
        task = t["kind"] == "task"
        self.photo.visible = not task
        self.photo.photo_key, self.photo.art, self.photo.alt = t.get("photo_key") or "", t.get("art") or "", t["name"]
        self.name.text = ("Task: " if task else "") + t["name"]
        finds = t.get("finds") or []
        self.meta.text = state.plural(len(finds), "find")
        self.finds_panel.items = finds
        self.none.visible = not finds
