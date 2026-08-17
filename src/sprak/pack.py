from pathlib import Path

from .atlas import Atlas


def pack(
    src: str | Path | list[str] | list[Path],
    *,
    dst_zip: str | Path | None = None,
    dst_json: str | Path | None = None,
    dst_image: str | Path | None = None,
) -> None:
    """Pack sprites into an atlas."""
    atlas = Atlas()

    if isinstance(src, list):
        src_paths = [Path(s) for s in src]
    else:
        src_paths = [Path(src)]

    for path in src_paths:
        if path.is_dir():
            atlas.add_folder(path)
        else:
            atlas.add_file(path)

    if dst_zip:
        atlas.write_zip(dst_zip)
    if dst_json:
        atlas.write_json(dst_json)
    if dst_image:
        atlas.write_image(dst_image)
