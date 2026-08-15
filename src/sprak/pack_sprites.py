import io
import json
import logging
import math
import zipfile
from pathlib import Path

import PIL
from PIL import Image

from .aseprite_utils import is_aseprite_file
from .rect import Rect
from .sprite import Sprite

logger = logging.getLogger("sprak")

PathList = str | Path | list[str] | list[Path]


def pack(src: PathList, dst_json: str | Path, dst_image: str | Path) -> None:
    """Pack sprites into separate json and image files."""
    atlas_json, atlas_image = pack_sprites_into_atlas(src)
    write_json(atlas_json, dst_json)
    write_image(atlas_image, dst_image)


def pack_and_zip(src: PathList, dst: str | Path) -> None:
    """Pack sprites into a zipped atlas file."""
    atlas_json, atlas_image = pack_sprites_into_atlas(src)
    write_zip(atlas_json, atlas_image, dst)


def pack_sprites_into_atlas(src: PathList) -> tuple[str, Image.Image]:
    """Pack sprites into an atlas.
    Returns a tuple of (atlas_json, atlas_image).
    """
    # Convert src to a list of paths
    if isinstance(src, list):
        src_paths = [Path(s) for s in src]
    else:
        src_paths = [Path(src)]

    # Collect sprites
    sprites = []
    for path in src_paths:
        logger.info(f"Collecting sprites from {path.absolute().as_posix()}")
        if path.is_file():
            sprite_name = get_sprite_name(path.parent, path)
            sprites += get_sprites(sprite_name, path)
        elif path.is_dir():
            for root, _, files in path.walk():
                for f in files:
                    file = root / f
                    sprite_name = get_sprite_name(path, file)
                    sprites += get_sprites(sprite_name, file)

    # Sort by height so that the tallest sprites are placed first
    sort_sprites_by_height(sprites)

    # Create atlas
    atlas_size = place_sprites(sprites)
    atlas_json = create_atlas_json(sprites)
    atlas_image = create_atlas_image(sprites, atlas_size)

    return atlas_json, atlas_image


def get_sprite_name(root: Path, file: Path) -> str:
    """Get a sprite name by using its relative path from the root directory."""
    return file.relative_to(root).as_posix().strip("/")


def get_sprites(name: str, file: Path) -> list[Sprite]:
    """Get sprites from a file.
    In the case of a normal image file, this will just be a single sprite, but other file formats (e.g. Aseprite) can produce multiple sprites.
    """
    logger.debug(f"Reading {file.as_posix()}")
    if is_aseprite_file(file):
        return sprites_from_aseprite(name, file)
    else:
        try:
            return [sprite_from_image(name, file)]
        except PIL.UnidentifiedImageError:
            logger.debug(f"Skipping non-image file: {file.as_posix()}")

    return []


def sprites_from_aseprite(name: str, file: Path) -> list[Sprite]:
    """Get all sprites from an aseprite file."""
    sprites = []
    return sprites


def sprite_from_image(name: str, file: Path) -> Sprite:
    """Get a sprite from an image file."""
    sprite = Sprite(name=name)
    with Image.open(file) as image:
        sprite.width = image.width
        sprite.height = image.height
        sprite.original_width = image.width
        sprite.original_height = image.height
        sprite.image = image.copy()
        if bbox := image.getbbox():
            left, upper, right, lower = bbox
            sprite.width = right - left
            sprite.height = lower - upper
            sprite.offset_x = left
            sprite.offset_y = upper
            sprite.image = image.crop(bbox)

    return sprite


def place_sprites(sprites: list[Sprite]) -> tuple[int, int]:
    """Place the sprites on the atlas.
    The size of the atlas is returned as a tuple of (width, height).
    """
    size = calculate_starting_size(sprites)

    while True:
        logger.debug(f"Placing sprites on atlas size of {size}x{size}")
        regions = [Rect(0, 0, size, size)]
        overflow = False
        for sprite in sprites:
            # Skip completely transparent images
            if sprite.is_empty:
                continue

            # Try to find a region that the sprite fits into
            if region := find_region(sprite, regions):
                # Place sprite
                sprite.x = region.x
                sprite.y = region.y

                # Split region
                regions.remove(region)
                split_x = sprite.x + sprite.width
                split_y = sprite.y + sprite.height
                regions += split_region(region, split_x, split_y)
                sort_rects_by_area(regions)
            else:
                logger.debug(f"{sprite.name} overflowed")
                overflow = True
                break

        # If the sprites overflowed on the atlas, try again with increased atlas size
        if overflow:
            size = get_next_power_of_2(size)
        else:
            break

    return (size, size)


def calculate_starting_size(sprites: list[Sprite]) -> int:
    """Calculate the starting size of the atlas.
    We assume the algorithm will be 100% efficient, meaning that the area of the atlas will be exactly the sum of the areas of the sprites.
    Of course it won't, but rounding to the next power of 2 gives us some padding, which is a reasonable place to start.
    """
    area = math.sqrt(sum([s.width * s.height for s in sprites]))
    return round_to_power_of_2(area)


def find_region(sprite: Sprite, regions: list[Rect]) -> Rect | None:
    """Find a region that the sprite fits into."""
    for region in regions:
        if sprite.width <= region.w and sprite.height <= region.h:
            return region

    return None


def split_region(region: Rect, x: int, y: int) -> list[Rect]:
    """Horizontally split a region into top and bottom sub-regions.
           X
    ┌──────┬────────┐
    │░░░░░░│  top   │
    │░░░░░░│        │
    ├──────┴────────┤ Y
    │    bottom     │
    │               │
    └───────────────┘
    """
    sub_regions = []

    top_w = region.right - x + 1
    top_h = y - region.top
    top = Rect(x, region.y, top_w, top_h)

    bottom_w = region.w
    bottom_h = region.bottom - y + 1
    bottom = Rect(region.x, y, bottom_w, bottom_h)

    # Add non-empty regions back to region list
    if not top.is_empty:
        sub_regions.append(top)
    if not bottom.is_empty:
        sub_regions.append(bottom)

    return sub_regions


def create_atlas_json(sprites: list[Sprite]) -> str:
    """Create an atlas json string from the sprites."""
    return json.dumps(sorted([s.to_dict() for s in sprites], key=lambda x: x.get("name")), indent=2)


def create_atlas_image(sprites: list[Sprite], atlas_size: tuple[int, int]) -> Image.Image:
    """Create an atlas image from the sprites."""
    atlas_image = Image.new("RGBA", atlas_size)

    for sprite in sprites:
        if sprite.image:
            atlas_image.paste(sprite.image, box=(sprite.x, sprite.y))

    return atlas_image


def round_to_power_of_2(value: float) -> int:
    """Round a value up to its closest power of 2."""
    result = 2

    while value > result:
        result *= 2

    return result


def get_next_power_of_2(value: float) -> int:
    """Given a value, get the next power of 2 that is greater than the value."""
    result = 2

    while value >= result:
        result *= 2

    return result


def sort_sprites_by_height(sprites: list[Sprite]) -> None:
    """Sort sprites from tallest to shortest."""
    sprites.sort(key=lambda sprite: sprite.height, reverse=True)


def sort_sprites_by_name(sprites: list[Sprite]) -> None:
    """Sort sprites alphabetically by name."""
    sprites.sort(key=lambda sprite: sprite.name)


def sort_rects_by_area(rects: list[Rect]) -> None:
    """Sort rects from smallest to largest area."""
    rects.sort(key=lambda rect: rect.w * rect.h)


def write_json(atlas_json: str, file: str | Path) -> None:
    """Write the atlas json data to a zip file."""
    file = Path(file)
    logger.info(f"Writing {file.absolute().as_posix()}")
    with file.open("w") as fp:
        fp.write(atlas_json)


def write_image(atlas_image: Image.Image, file: str | Path) -> None:
    """Write the atlas image data to a file."""
    file = Path(file)
    logger.info(f"Writing {file.absolute().as_posix()}")
    atlas_image.save(file)


def write_zip(atlas_json: str, atlas_image: Image.Image, file: str | Path) -> None:
    """Write the atlas to a zip file."""
    file = Path(file)
    logger.info(f"Writing {file.absolute().as_posix()}")
    image_buffer = io.BytesIO()
    atlas_image.save(image_buffer, format="PNG")
    image_bytes = image_buffer.getvalue()
    with zipfile.ZipFile(file, mode="w", compression=zipfile.ZIP_STORED) as zf:
        zf.writestr("json", atlas_json)
        zf.writestr("png", image_bytes)
