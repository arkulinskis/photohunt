from anvil import *

from ._anvil_designer import StickerItemTemplate


class StickerItem(StickerItemTemplate):
    """A sticker in a sticker book or a result. item = {id, count, size}."""

    def __init__(self, **properties):
        super().__init__(**properties)
        s = self.item
        self.sticker.sticker = s["id"]
        self.sticker.count = s.get("count", 0)
        self.sticker.size = s.get("size", 56)
