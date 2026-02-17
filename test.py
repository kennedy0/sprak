from pathlib import Path

from sprak import SpritePacker

src = Path("/home/akennedy/git/hexx/assets/sprites")
dst = Path.home() / "Desktop"


packer = SpritePacker()
packer.add_source_folder(src)
packer.pack(dst)
