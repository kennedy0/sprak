import logging
import sys
import time
import tomllib
from argparse import ArgumentParser
from pathlib import Path

from sprak import pack
from sprak.log import logger
from sprak.viewer import view_atlas_json_and_png, view_atlas_zip


def pack_sprites() -> None:
    parser = ArgumentParser(prog="sprak", description="Pack sprites into an atlas.")
    parser.add_argument("src", nargs="+", help="the source path(s) to scan for sprites")
    parser.add_argument("--fps", default=24, type=float, help="set GIF frame rate")
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="set verbosity; can be used multiple times to increase verbosity",
    )
    parser.add_argument("--version", action="version", version=_get_version_str())

    group = parser.add_argument_group("output")
    group.add_argument("--zip", metavar="FILE", help="write atlas to a ZIP file")
    group.add_argument("--json", metavar="FILE", help="write atlas to a JSON file")
    group.add_argument("--png", metavar="FILE", help="write atlas to a PNG file")
    group.add_argument("--gif", metavar="FILE", help="write packing animation to a GIF file")
    group.add_argument(
        "--debug-gif",
        metavar="FILE",
        help="write packing animation with debug info to a GIF file",
    )

    args = parser.parse_args(sys.argv[1:])

    if not args.zip and not args.json and not args.png and not args.gif and not args.debug_gif:
        parser.error("at lest one output option is required")

    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    start = time.time()
    pack(
        args.src,
        dst_zip=args.zip,
        dst_json=args.json,
        dst_png=args.png,
        dst_gif=args.gif,
        dst_debug_gif=args.debug_gif,
        fps=args.fps,
    )
    logger.info(f"sprites packed in {round(time.time() - start, 3)}s")


def view_atlas() -> None:
    parser = ArgumentParser(prog="sprak-view", description="View atlas image and metadata.")
    parser.add_argument(
        "atlas", nargs="+", help="the atlas file; can be either a single ZIP file, or separate JSON and PNG files"
    )
    args = parser.parse_args(sys.argv[1:])
    if len(args.atlas) == 1:
        view_atlas_zip(args.atlas[0])
    elif len(args.atlas) == 2:
        view_atlas_json_and_png(args.atlas)
    else:
        parser.error("must provide either one ZIP file, or separate JSON and PNG files")


def _get_version_str() -> str:
    pyproject_toml = Path(__file__).parent.parent.parent / "pyproject.toml"
    with pyproject_toml.open("rb") as fp:
        data = tomllib.load(fp)
        return data.get("project", {}).get("version", "")
