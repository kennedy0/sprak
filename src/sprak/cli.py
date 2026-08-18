import logging
import sys
import time
from argparse import ArgumentParser

from sprak import pack
from sprak.log import logger


def pack_sprites() -> None:
    parser = ArgumentParser(prog="sprak", description="Pack sprites into an atlas.")
    parser.add_argument("src", nargs="+", help="the source path(s) to scan for sprites")
    parser.add_argument("-v", "--verbose", action="count", default=0)

    group = parser.add_argument_group("output")
    group.add_argument("--zip", metavar="FILE", help="write the atlas to a ZIP file")
    group.add_argument("--json", metavar="FILE", help="write the atlas to a JSON file")
    group.add_argument("--image", metavar="FILE", help="write the atlas to a image file")

    args = parser.parse_args(sys.argv[1:])

    if not args.zip and not args.json and not args.image:
        parser.error("at lest one of --zip, --json, or --image is required")

    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    start = time.time()
    pack(args.src, dst_zip=args.zip, dst_json=args.json, dst_image=args.image)
    logger.info(f"sprites packed in {round(time.time() - start, 3)}s")


if __name__ == "__main__":
    pack_sprites()
