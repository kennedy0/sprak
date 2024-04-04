# sprak

`sprak` is a Python module for packing multiple sprites into a single texture atlas.

### What this is (and isn't)

I built `sprak` for myself to make my own game development workflow smoother; it is not a general-purpose tool.
As such, it's definitely missing features that you'd find in a commercially available program such as [TexturePacker](https://www.codeandweb.com/texturepacker).

It is also **not stable**.
I add and remove features when my needs change.

If you find `sprak` useful, I'd recommend forking the project and adapting it to your own needs.

### aseprite_reader

The `aseprite_reader` module provides an `AsepriteFile` class for reading and rendering Aseprite files.
Like `sprak`, I wrote this for my needs, so it only supports the Aseprite features that I happen to use.
Wherever possible, `AsepriteFile` will raise a `NotImplementedError` whenever it encounters unsupported behavior.

## Usage

```python
from pathlib import Path

from sprak import SpritePacker


src = Path("/path/to/src/folder")
dst = Path("/path/to/dst/folder")

packer = SpritePacker()
packer.add_source_folder(src)
packer.pack(dst)

```
