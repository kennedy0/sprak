from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Rect:
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

    def intersects(self, other: Rect) -> bool:
        """Check if this rectangle intersects another rectangle."""
        return (
            other.left <= self.right
            and self.left <= other.right
            and other.top <= self.bottom
            and self.top <= other.bottom
        )

    def as_tuple(self) -> tuple[int, int, int, int]:
        """Return a tuple in the form of (left, top, right, bottom)."""
        return self.left, self.top, self.right, self.bottom
