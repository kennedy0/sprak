from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Atlas:
    frames: dict[str, Frame] = field(metadata={"description": "Atlas frames"})
    sprites: dict[str, Sprite] = field(metadata={"description": "Atlas sprites"})


@dataclass
class Sprite:
    """This is a sprite!"""

    frames: list[str] = field(metadata={"description": "A list of all frame names in the sprite"})
    animations: dict[str, list[str]] = field(default_factory=dict)
    slice9: list[Rect] = field(default_factory=list)


@dataclass
class Frame:
    x: int
    y: int
    width: int
    height: int
    source_width: int
    source_height: int
    offset_x: int
    offset_y: int
    frame_number: int = field(default=0)
    duration: int = field(default=0)


@dataclass
class Rect:
    x: int = field(metadata={"description": "x position of the rectangle"})
    y: int = field(metadata={"description": "y position of the rectangle"})
    w: int
    h: int


AtlasJSON = Atlas
SpriteJSON = Sprite
FrameJSON = Frame
RectJSON = Rect
