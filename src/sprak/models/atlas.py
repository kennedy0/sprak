import json
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

from PIL import Image

from sprak.models.frame import Frame
from sprak.models.rect import Rect
from sprak.utilities import ffmpeg_utils


class Atlas:
    def __init__(self) -> None:
        # Tracks whether or not the frames have been packed
        self._frames_packed: bool = False

        # The list of empty rectangular regions that can store frames
        self._regions: list[Rect] = []

        # Stores the length of the progress message so it can be cleared
        self._progress_message_length = 0

        # The size of the atlas
        self.width: int = 64
        self.height: int = 64

        # The amount that the atlas increases in size
        self.step_size: int = 64

        # The list of frames in the atlas
        self.frames: list[Frame] = []

    def add_frames(self, frames: list[Frame]) -> None:
        """Add multiple frames to the atlas."""
        self.frames += frames

    def pack(self) -> None:
        """Pack all frames into the atlas."""
        print("Packing frames...")
        self.sort_frames_by_height()
        while True:
            if self.place_frames():
                break
            else:
                self.increase_atlas_size()

        print("Frame packing complete!")
        self._frames_packed = True

    def sort_frames_by_height(self) -> None:
        """Sort frames by height.
        This seems to leave the least amount of wasted space when we split regions horizontally.
        """
        self.frames.sort(key=lambda f: f.frame_height, reverse=True)

    def place_frames(self) -> bool:
        """Place all frames onto the atlas.
        If the function is successful (that is, it places all frames without running out of space), it will return True.
        Otherwise, it will return False.
        """
        self.reset_regions()
        for frame in self.frames:
            # Skip completely transparent images
            if not frame.image.getbbox():
                continue

            # Find a region that the frame fits in
            if region := self.find_region(frame):
                self.place_frame(frame, region)
            else:
                return False

        return True

    def reset_regions(self) -> None:
        """Reset the list of free regions."""
        self._regions = [Rect(0, 0, self.width, self.height)]

    def find_region(self, frame: Frame) -> Optional[Rect]:
        """Find a free region to pack a frame.
        If no valid position is found, None is returned.
        """
        for region in self._regions:
            if frame.frame_width <= region.w and frame.frame_height <= region.h:
                return region

        return None

    def place_frame(self, frame: Frame, region: Rect) -> None:
        """Place a frame onto the atlas."""
        frame.x = region.x
        frame.y = region.y

        # Split the leftover space in the region
        split_y = frame.y + frame.frame_height
        split_x = frame.x + frame.frame_width
        self.split_region(region, split_y, split_x)

        # Sort regions from smallest to largest area
        self._regions.sort(key=lambda r: r.w * r.h)

    def split_region(self, region: Rect, y: int, x: int) -> None:
        """Horizontally split a region into sub-regions.
                X
        +------+--------+
        |######|   top  |
        |######|        |
        +------+--------|
        |     bottom    | Y
        |               |
        +---------------+
        """
        # First remove the existing region
        self._regions.remove(region)

        # Top region
        top_w = region.right - x + 1
        top_h = y - region.top
        top = Rect(x, region.y, top_w, top_h)

        # Bottom region
        bottom_w = region.w
        bottom_h = region.bottom - y + 1
        bottom = Rect(region.x, y, bottom_w, bottom_h)

        # Add non-empty regions back to region list
        if not top.is_empty:
            self._regions.append(top)
        if not bottom.is_empty:
            self._regions.append(bottom)

    def increase_atlas_size(self) -> None:
        """Increase the size of the atlas."""
        self.width += self.step_size
        self.height += self.step_size

    def write_image(self, image_file: Path) -> None:
        """Write the atlas out to a file."""
        if not self._frames_packed:
            self.pack()

        print(f"Writing image ({self.width} x {self.height}): {image_file.as_posix()}")
        image = Image.new("RGBA", size=(self.width, self.height))
        for frame in self.frames:
            # Skip completely transparent images
            if not frame.image.getbbox():
                continue

            image.paste(frame.image, box=(frame.x, frame.y))

        image.save(image_file)

    def write_frame_data(self, data_file: Path) -> None:
        """Write the frame data to a file."""
        print(f"Writing frame data: {data_file.as_posix()}")

        # Sort frames alphabetically
        frames = sorted(self.frames, key=lambda f: f.name)

        # Convert frame data to dictionary
        frame_data = {}
        for frame in frames:
            frame_data[frame.name] = frame.to_dict()

        # Write frame data to file
        with data_file.open("w") as fp:
            data_str = json.dumps(frame_data, indent=2)
            fp.write(data_str)

    def render_animation(self, video_file: Path, resolution_x: int = 1280, resolution_y: int = 720) -> None:
        """Render an animation of the sprite packing to a file."""
        with TemporaryDirectory() as tmp:
            temp_dir = Path(tmp)
            temp_dir.mkdir(parents=True, exist_ok=True)

            image = Image.new("RGBA", size=(self.width, self.height))
            frame_number = 1
            for frame in self.frames:
                # Skip completely transparent images
                if not frame.image.getbbox():
                    continue

                image.paste(frame.image, box=(frame.x, frame.y))
                image.save(temp_dir / f"frame_{frame_number:08d}.png")
                frame_number += 1

            src = temp_dir / "frame_%08d.png"
            dst = video_file

            print(f"Rendering video: {video_file.as_posix()}")

            ffmpeg = ffmpeg_utils.find_ffmpeg_executable()
            cmd = [
                ffmpeg,
                "-y",
                "-hide_banner",
                "-loglevel",
                "quiet",
                "-framerate",
                "60",
                "-i",
                src.as_posix(),
                "-crf",
                "18",
                "-c:v",
                "libx264",
                "-vf",
                f"scale={resolution_x}:{resolution_y}:force_original_aspect_ratio=increase:flags=neighbor",
                "-pix_fmt",
                "yuv420p",
                dst.as_posix(),
            ]

            proc = subprocess.Popen(cmd)
            proc.communicate()
