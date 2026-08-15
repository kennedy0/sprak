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
    def is_empty(self) -> bool:
        """Check if this rectangle has an area of zero."""
        return self.w == 0 or self.h == 0
