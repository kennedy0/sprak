from pathlib import Path
from tempfile import TemporaryDirectory

from aseprite_reader import AsepriteFile

from sprak.models.atlas import Atlas
from sprak.models.frame import Frame


class SpritePacker:
    def __init__(self) -> None:
        self._source_folders: list[Path] = []

    def add_source_folder(self, folder_path: Path) -> None:
        """Add a directory to the list of source paths that will be processed."""
        if not folder_path.is_dir():
            raise NotADirectoryError(f"{folder_path.as_posix()} must be a directory.")
        self._source_folders.append(folder_path)

    def pack(self, output_folder: Path, atlas_name: str = "atlas", render_animation: bool = False) -> None:
        """Pack sprites."""
        self._validate_output_folder(output_folder)

        frames = self._collect_frames()

        atlas = Atlas()
        atlas.add_frames(frames)
        atlas.write_image(output_folder / f"{atlas_name}.png")
        atlas.write_frame_data(output_folder / f"{atlas_name}.framedata")

        if render_animation:
            atlas.render_animation(output_folder / f"{atlas_name}.mp4")

    @staticmethod
    def _validate_output_folder(output_folder: Path) -> None:
        """Make sure output folder is valid."""
        if not output_folder.is_dir():
            raise NotADirectoryError(f"{output_folder.as_posix()} must be a directory.")

    def _collect_frames(self) -> list[Frame]:
        """Gather a list of frames from the source folders."""
        frames: list[Frame] = []
        for source_folder in self._source_folders:
            for root, dirs, files in source_folder.walk():
                for f in files:
                    file = root / f
                    match file.suffix.lower():
                        case ".png":
                            png_frame = self._png_to_frame(file)
                            frames.append(png_frame)
                        case ".aseprite":
                            aseprite_frames = self._aseprite_to_frames(file)
                            frames += aseprite_frames
        return frames

    def _png_to_frame(self, png_file_path: Path) -> Frame:
        """Create a frame from a PNG file."""
        frame_name = self._rel_path_without_extension(png_file_path)
        sprite_name = self._rel_path_without_extension(png_file_path)
        frame = Frame(frame_name, png_file_path)
        frame.metadata.update({"source_format": "png"})
        frame.metadata.update({"sprite_name": sprite_name})
        return frame

    def _aseprite_to_frames(self, aseprite_file_path: Path) -> list[Frame]:
        """Create frames from an Aseprite file.
        The creation of frames will differ based on whether there are multiple frames or tags in the Aseprite file.
        """
        frames = []
        aseprite_file = AsepriteFile(aseprite_file_path)

        with TemporaryDirectory() as tmp:
            # Create temporary directory
            temp_dir = Path(tmp)
            temp_dir.mkdir(parents=True, exist_ok=True)

            sprite_name = self._rel_path_without_extension(aseprite_file_path)

            # Render PNGs
            for frame_number, ase_frame in aseprite_file.iter_frames():
                # Render PNG
                png_file = temp_dir / f"{aseprite_file_path.stem}.{frame_number:04d}.png"
                aseprite_file.render(ase_frame, png_file)

                # Create a frame for the atlas
                frame_name = self._rel_path_without_extension(aseprite_file.file_path.with_name(png_file.name))
                frame = Frame(frame_name, png_file)

                # Get a list of tags for the frame
                tags = [t.name for t in aseprite_file.frame_tags(frame_number)]

                # Add metadata
                frame.metadata.update({"source_format": "aseprite"})
                frame.metadata.update({"sprite_name": sprite_name})
                frame.metadata.update({"tags": tags})
                frame.metadata.update({"duration": ase_frame.duration})
                frame.metadata.update({"frame_number": frame_number})

                # Add frame to list
                frames.append(frame)

        return frames

    def _rel_path_without_extension(self, file: Path) -> str:
        """Convert a file path to a relative path string, without an extension.
        The path is relative to the source folder.

        Examples

        File Name: C:/source_folder/Sprite.png
        Frame Name: Sprite

        File Name C:/source_folder/animation/Sprite.0001.png
        Frame Name: animation/Sprite.0001
        """
        # Get the relative path to the file from its source folder
        rel_path = None
        for source_folder in self._source_folders:
            if file.is_relative_to(source_folder):
                rel_path = file.relative_to(source_folder)

        # Raise an error if rel path wasn't found
        if not rel_path:
            raise RuntimeError(f"File is not relative to any source folders: {file.as_posix()}")

        # Strip extension
        no_ext = rel_path.with_suffix("")

        # Convert to forward slashes
        frame_name = no_ext.as_posix()
        return frame_name
