from __future__ import annotations

from pathlib import Path

from PIL import Image

from sprak.rect import Rect


class Frame:
    def __init__(self, name: str, file: str | Path) -> None:
        self.name = name
        self.file = Path(file)

        with Image.open(file) as image:
            source_width = image.width
            source_height = image.height

            if bbox := image.getbbox():
                left, upper, right, lower = bbox
                width = right - left
                height = lower - upper
                offset_x = left
                offset_y = upper
                image = image.crop(bbox)
            else:
                width = 0
                height = 0
                offset_x = 0
                offset_y = 0
                image = image.copy()

        self.x: int = 0
        self.y: int = 0
        self.width: int = width
        self.height: int = height
        self.source_width: int = source_width
        self.source_height: int = source_height
        self.offset_x: int = offset_x
        self.offset_y: int = offset_y
        self.frame_number: int = 0
        self.duration: int = 0
        self.image: Image.Image = image

        self._debug_placement_order = -1
        self._debug_region_used: Rect | None = None
        self._debug_regions_split: list[Rect] = []

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def is_empty(self) -> bool:
        return self.area == 0

    def to_json(self) -> dict:
        d = {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "source_width": self.source_width,
            "source_height": self.source_height,
            "offset_x": self.offset_x,
            "offset_y": self.offset_y,
        }

        if self.frame_number:
            d["frame_number"] = self.frame_number

        if self.duration:
            d["duration"] = self.duration

        return d
