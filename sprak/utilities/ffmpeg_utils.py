import os
import shutil
from pathlib import Path
from typing import Optional


def find_ffmpeg_executable() -> Optional[Path]:
    """ Find the installed ffmpeg. """
    if ffmpeg := os.getenv('SPRAK_FFMPEG_PATH'):
        return Path(ffmpeg)
    if ffmpeg := shutil.which("ffmpeg"):
        return Path(ffmpeg)
    else:
        e = RuntimeError(f"Could not find 'ffmpeg' executable.")
        e.add_note("Make sure ffmpeg is installed and on the system PATH, or set the SPRAK_FFMPEG_PATH variable.")
        raise e
