from pathlib import Path

from sprak.atlas import Atlas
from sprak.log import logger


def pack(
    src: str | Path | list[str] | list[Path],
    *,
    dst_zip: str | Path | None = None,
    dst_json: str | Path | None = None,
    dst_png: str | Path | None = None,
    dst_gif: str | Path | None = None,
    dst_debug_gif: str | Path | None = None,
    fps: float = 24,
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
    if dst_png:
        logger.info(f"writing {Path(dst_png).absolute().as_posix()}")
        atlas.write_png(dst_png)
    if dst_gif:
        logger.info(f"writing {Path(dst_gif).absolute().as_posix()}")
        atlas.write_gif(dst_gif, fps)
    if dst_debug_gif:
        logger.info(f"writing {Path(dst_debug_gif).absolute().as_posix()}")
        atlas.write_debug_gif(dst_debug_gif, fps)
