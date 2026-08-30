from __future__ import annotations

from typing import NotRequired, TypedDict


class Atlas(TypedDict):
    frames: dict[str, Frame]
    sprites: dict[str, Sprite]


class Sprite(TypedDict):
    frames: list[str]
    animations: NotRequired[dict[str, list[str]]]
    slice9: NotRequired[list[Rect]]


class Frame(TypedDict):
    x: int
    y: int
    width: int
    height: int
    source_width: int
    source_height: int
    offset_x: int
    offset_y: int
    frame_number: NotRequired[int]
    duration: NotRequired[int]


class Rect(TypedDict):
    x: int
    y: int
    w: int
    h: int


AtlasJSON = Atlas
SpriteJSON = Sprite
FrameJSON = Frame
RectJSON = Rect
