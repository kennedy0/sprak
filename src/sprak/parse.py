import re
from pathlib import Path
from typing import NamedTuple

SPRITE_ANIM_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<animation>\w+)\.(?P<frame>\d+)$", re.IGNORECASE)
SPRITE_FRAME_RE = re.compile(r"^(?P<sprite>[\w/]+)\.(?P<frame>\d+)$", re.IGNORECASE)


class ParsedFilenameResult(NamedTuple):
    sprite_name: str
    animation_name: str | None
    frame_number: int | None


def parse_filename(file: str | Path) -> ParsedFilenameResult:
    """Parse a filename to find the sprite name, animation name, and frame number."""
    filename = Path(file).stem

    if match := SPRITE_ANIM_FRAME_RE.match(filename):
        sprite_name = match.group("sprite")
        animation_name = match.group("animation")
        frame_number = int(match.group("frame"))
    elif match := SPRITE_FRAME_RE.match(filename):
        sprite_name = match.group("sprite")
        animation_name = None
        frame_number = int(match.group("frame"))
    else:
        sprite_name = filename
        animation_name = None
        frame_number = None

    return ParsedFilenameResult(sprite_name, animation_name, frame_number)
