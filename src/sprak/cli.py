import logging
import sys
import time
from argparse import ArgumentDefaultsHelpFormatter, ArgumentParser

from sprak import pack
from sprak.log import logger


def pack_sprites() -> None:
    parser = ArgumentParser(prog="sprak", description="Pack sprites into an atlas.")
    parser.add_argument("src", nargs="+", help="the source path(s) to scan for sprites")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    group = parser.add_argument_group("output")
    group.add_argument("--zip", metavar="FILE", help="write the atlas to a ZIP file")
    group.add_argument("--json", metavar="FILE", help="write the atlas to a JSON file")
    group.add_argument("--png", metavar="FILE", help="write the atlas to a PNG file")
    group.add_argument("--gif", metavar="FILE", help="write the packing animation to a GIF file")
    group.add_argument(
        "--debug-gif", metavar="FILE", help="write the packing animation (with debug info) to a GIF file"
    )
    group.add_argument("--fps", default=24, type=float, help="")

    args = parser.parse_args(sys.argv[1:])

    if not args.zip and not args.json and not args.png and not args.gif and not args.debug_gif:
        parser.error("at lest one of --zip, --json, --png, --gif, or --debug-gif is required")

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


if __name__ == "__main__":
    pack_sprites()
