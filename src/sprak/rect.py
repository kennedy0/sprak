from __future__ import annotations

from typing import NamedTuple

from sprak.json_types import RectJSON


class Rect(NamedTuple):
    x: int
    y: int
    width: int
    height: int

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.height - 1

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.width - 1

    @property
    def area(self) -> int:
        return self.width * self.height

    @property
    def is_empty(self) -> bool:
        return self.area == 0

    @property
    def squareness(self) -> float:
        return min(self.width, self.height) / max(self.width, self.height)

    @property
    def pil_rect(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.width - 1, self.y + self.height - 1)

    def to_json(self) -> RectJSON:
        return {
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
        }

    @staticmethod
    def merge(a: Rect, b: Rect) -> Rect | None:
        """Attempt to merge 2 Rects together.
        A single Rect will be returned if it can be represented by a single larger Rect.
        Otherwise, None will be returned.
        """
        if a.y == b.y and a.height == b.height:
            if a.right == b.left - 1:
                # [ a ][ b ]
                return Rect(a.x, a.y, a.width + b.width, a.height)
            elif a.left == b.right + 1:
                # [ b ][ a ]
                return Rect(b.x, b.y, b.width + a.width, b.height)
        elif a.x == b.x and a.width == b.width:
            if a.bottom == b.top - 1:
                # [ a ]
                # [ b ]
                return Rect(a.x, a.y, a.width, a.height + b.height)
            elif a.top == b.bottom + 1:
                # [ b ]
                # [ a ]
                return Rect(b.x, b.y, b.width, b.height + a.height)
