from pathlib import Path

from sprak.atlas import Atlas
from sprak.log import logger


def pack(
    src: str | Path | list[str] | list[Path],
    *,
    dst_zip: str | Path | None = None,
    dst_json: str | Path | None = None,
    dst_image: str | Path | None = None,
) -> None:
    atlas = Atlas()

    if isinstance(src, list):
        src_paths = [Path(s) for s in src]
    else:
        src_paths = [Path(src)]

    for path in src_paths:
        if path.is_dir():
            logger.info(f"adding source folder {path.absolute().as_posix()}")
            atlas.add_folder(path)
        else:
            logger.info(f"adding source file {path.absolute().as_posix()}")
            atlas.add_file(path)

    if dst_zip:
        logger.info(f"writing {Path(dst_zip).absolute().as_posix()}")
        atlas.write_zip(dst_zip)
    if dst_json:
        logger.info(f"writing {Path(dst_json).absolute().as_posix()}")
        atlas.write_json(dst_json)
    if dst_image:
        logger.info(f"writing {Path(dst_image).absolute().as_posix()}")
        atlas.write_image(dst_image)
