"""Pre-render the Cascabel logo as desktop icon PNGs.

The logo SVG carries a large embedded raster on a huge A4 canvas. When a
desktop environment scales that SVG down to a tiny taskbar icon at display
time, its renderer downsamples the big raster in one crude step and the
artwork's faint semi-transparent edge feather turns into a light hairline
around the icon. Rendering every standard size once here - with a proper
area-averaged downscale from one big render - and installing the PNGs into
the user's icon theme means the desktop never has to scale the SVG itself.

Usage:
    python3 make_icons.py [icons_root]

With no argument the PNGs go to the user's hicolor dir
($XDG_DATA_HOME/icons/hicolor or ~/.local/share/icons/hicolor), where any
desktop entry with Icon=cascabel finds them.
"""

import os
import shutil
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QImage

from ui.logo_assets import harden_alpha, trimmed_logo_image

SIZES = (16, 22, 24, 32, 48, 64, 96, 128, 256)


def default_root():
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return data_home / "icons" / "hicolor"


def main(argv):
    root = Path(argv[1]) if len(argv) > 1 else default_root()

    square = trimmed_logo_image()
    if square is None or square.isNull():
        print("[make-icons] ERROR: could not render the Cascabel logo", file=sys.stderr)
        return 1

    written = 0
    for size in SIZES:
        out_dir = root / "{}x{}".format(size, size) / "apps"
        out_dir.mkdir(parents=True, exist_ok=True)
        png = square.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        ).convertToFormat(QImage.Format.Format_ARGB32)
        # Small icons get a hard 0/255 alpha edge so no background can bleed
        # through the rim and read as a white outline at taskbar sizes.
        if size <= 64:
            png = harden_alpha(png)
        if png.save(str(out_dir / "cascabel.png"), "PNG"):
            written += 1

    # Vector fallback for any size that was not pre-rendered. The cropped
    # CascabelIcon.svg (artwork only, transparent margins removed) is used
    # so even a naive rendering shows just the logo.
    scalable = root / "scalable" / "apps"
    scalable.mkdir(parents=True, exist_ok=True)
    vector_src = Path(__file__).resolve().parent / "ui" / "logo" / "CascabelIcon.svg"
    if vector_src.exists():
        shutil.copyfile(vector_src, scalable / "cascabel.svg")

    print("[make-icons] wrote {} PNGs + scalable SVG into {}".format(written, root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
