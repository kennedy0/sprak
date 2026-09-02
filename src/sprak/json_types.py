from __future__ import annotations

from typing import Annotated, NotRequired, TypedDict


def field_no_op(*args, **kwargs): ...


try:
    from pydantic import Field
except ModuleNotFoundError:
    Field = field_no_op


class Atlas(TypedDict):
    """Contains data about all frames and sprites packed into the texture atlas"""

    frames: Annotated[dict[str, Frame], Field(description="All frames in the atlas")]
    sprites: Annotated[dict[str, Sprite], Field(description="All sprites in the atlas")]


class Frame(TypedDict):
    """A single image (or single frame of animation) in a sprite"""

    x: Annotated[int, Field(description="Frame x-position")]
    y: Annotated[int, Field(description="Frame y-position")]
    width: Annotated[int, Field(description="Frame width on the atlas, after trimming transparent edges")]
    height: Annotated[int, Field(description="Frame height on the atlas, after trimming transparent edges")]
    source_width: Annotated[int, Field(description="Width of the canvas in the original source file")]
    source_height: Annotated[int, Field(description="Height of the canvas in the original source file")]
    offset_x: Annotated[int, Field(description="The leftmost pixel's distance from the canvas edge")]
    offset_y: Annotated[int, Field(description="The topmost pixel's distance from the canvas edge")]
    frame_number: Annotated[NotRequired[int], Field(description="The frame number")]
    duration: Annotated[NotRequired[int], Field(description="The duration of the frame in milliseconds")]


class Rect(TypedDict):
    x: int
    y: int
    width: int
    height: int


class Sprite(TypedDict):
    """A collection of one or more frames"""

    frames: Annotated[list[str], Field(description="A list of frame names in the sprite")]
    animations: Annotated[
        NotRequired[dict[str, list[str]]],
        Field(description="Key-value pairs of named animations and the frame names used in each animation"),
    ]
    nine_slice: Annotated[
        NotRequired[list[Rect]],
        Field(
            description="An array of rectangles, from top-left to bottom-right, that subdivide the sprite for 9-slice scaling"
        ),
    ]


AtlasJSON = Atlas
FrameJSON = Frame
SpriteJSON = Sprite
RectJSON = Rect
