from __future__ import annotations

from typing import NamedTuple


class Rect(NamedTuple):
    x: int
    y: int
    w: int
    h: int

    @property
    def top(self) -> int:
        return self.y

    @property
    def bottom(self) -> int:
        return self.y + self.h - 1

    @property
    def left(self) -> int:
        return self.x

    @property
    def right(self) -> int:
        return self.x + self.w - 1

    @property
    def area(self) -> int:
        return self.w * self.h

    @property
    def is_empty(self) -> bool:
        return self.area == 0

    @property
    def squareness(self) -> float:
        return min(self.w, self.h) / max(self.w, self.h)

    @property
    def pil_rect(self) -> tuple[int, int, int, int]:
        return (self.x, self.y, self.x + self.w - 1, self.y + self.h - 1)

    def to_json(self) -> dict:
        return {
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
        }

    @staticmethod
    def merge(a: Rect, b: Rect) -> Rect | None:
        """Attempt to merge 2 Rects together.
        A single Rect will be returned if it can be represented by a single larger Rect.
        Otherwise, None will be returned.
        """
        if a.y == b.y and a.h == b.h:
            if a.right == b.left - 1:
                # [ a ][ b ]
                return Rect(a.x, a.y, a.w + b.w, a.h)
            elif a.left == b.right + 1:
                # [ b ][ a ]
                return Rect(b.x, b.y, b.w + a.w, b.h)
        elif a.x == b.x and a.w == b.w:
            if a.bottom == b.top - 1:
                # [ a ]
                # [ b ]
                return Rect(a.x, a.y, a.w, a.h + b.h)
            elif a.top == b.bottom + 1:
                # [ b ]
                # [ a ]
                return Rect(b.x, b.y, b.w, b.h + a.h)
