"""Cascabel logo artwork rendered from the SVGs in ui/logo.

Cascabel.svg is the app logo (window/taskbar icon) and doubles as the play
(triangle) button artwork; CascabelPause.svg is the matching pause (two
stripes) artwork. Both files were exported on a large A4 canvas with the
artwork sitting in the middle surrounded by wide transparent margins, so
each file is rendered once and the transparent border is trimmed off the
alpha channel automatically - the trim always follows the artwork, no
matter what margins a re-export brings.
"""

import sys
from pathlib import Path

from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QGuiApplication, QIcon, QImage, QPainter, QPixmap

try:
    from PySide6.QtSvg import QSvgRenderer
except ImportError:  # QtSvg missing: the drawn vector fallbacks kick in.
    QSvgRenderer = None

from . import drawn_icons

# Rendering the full A4 viewBox this wide puts the ~1116-unit square artwork
# at ~460 px, crisp even for the big touch button on 3x HiDPI screens.
_RENDER_WIDTH = 1024

# Alpha (0-255) under which a pixel counts as transparent while trimming.
# The artwork's faintest edge feather lives below this: leaving it out keeps
# the trimmed edge crisp, so it cannot read as a light rim once the logo is
# scaled down to taskbar icon sizes.
_TRIM_THRESHOLD = 64

_LOGO_FILES = {
    "play": "Cascabel.svg",        # logo + play button artwork
    "pause": "CascabelPause.svg",  # pause button artwork
}

# kind -> square, margin-trimmed QImage, built on first use.
_trimmed_cache = {}


def _logo_path(name):
    """Absolute path of a logo SVG, in dev checkouts and frozen builds."""
    if getattr(sys, "frozen", False):
        # PyInstaller unpacks bundled data into sys._MEIPASS; ui/logo ships
        # as a datas entry in Cascabel.spec.
        meipass = getattr(sys, "_MEIPASS", None)
        base = Path(meipass) if meipass else Path(sys.executable).resolve().parent
        return base / "ui" / "logo" / name
    return Path(__file__).resolve().parent / "logo" / name


def _alpha_bounds(image):
    """Bounding rect of the visible artwork, or None when fully transparent."""
    alpha = image.convertToFormat(QImage.Format.Format_Alpha8)
    stride = alpha.bytesPerLine()
    raw = bytes(alpha.constBits())
    width = alpha.width()
    height = alpha.height()
    threshold = _TRIM_THRESHOLD

    def row_visible(y):
        return max(raw[y * stride : y * stride + width]) >= threshold

    top = 0
    while top < height and not row_visible(top):
        top += 1
    if top >= height:
        return None
    bottom = height - 1
    while not row_visible(bottom):
        bottom -= 1

    def col_visible(x):
        return any(raw[y * stride + x] >= threshold for y in range(top, bottom + 1))

    left = 0
    while not col_visible(left):
        left += 1
    right = width - 1
    while not col_visible(right):
        right -= 1
    return QRect(left, top, right - left + 1, bottom - top + 1)


def _pad_square(image):
    """Center a trimmed image on a transparent square (aspect-safe scaling)."""
    side = max(image.width(), image.height())
    square = QImage(side, side, QImage.Format.Format_ARGB32_Premultiplied)
    square.fill(Qt.GlobalColor.transparent)
    painter = QPainter(square)
    painter.drawImage((side - image.width()) // 2, (side - image.height()) // 2, image)
    painter.end()
    return square


def _render_square(path):
    """Render one logo SVG with its transparent margins trimmed off."""
    if QSvgRenderer is None:
        return None
    try:
        renderer = QSvgRenderer(str(path))
    except Exception:
        return None
    if not renderer.isValid():
        return None

    view_box = renderer.viewBoxF()
    if view_box.width() <= 0 or view_box.height() <= 0:
        return None

    width = _RENDER_WIDTH
    height = max(1, round(width * view_box.height() / view_box.width()))
    image = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    image.fill(Qt.GlobalColor.transparent)
    painter = QPainter(image)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    renderer.render(painter)
    painter.end()

    bounds = _alpha_bounds(image)
    if bounds is None or bounds.width() <= 0 or bounds.height() <= 0:
        return None
    return _pad_square(image.copy(bounds))


def _trimmed_square(kind):
    """Cached square artwork for "play" or "pause" (None if unavailable)."""
    if kind not in _trimmed_cache:
        _trimmed_cache[kind] = _render_square(_logo_path(_LOGO_FILES[kind]))
    return _trimmed_cache[kind]


def _device_pixel_ratio():
    """Device pixel ratio to render at (HiDPI screens need > 1)."""
    app = QGuiApplication.instance()
    if app is None:
        return 1.0
    screen = app.primaryScreen()
    if screen is None:
        return 1.0
    return max(1.0, float(screen.devicePixelRatio()))


def _scaled_pixmap(square, size):
    """DPR-aware pixmap of the square artwork at the requested logical size."""
    dpr = _device_pixel_ratio()
    physical = max(1, int(round(float(size) * dpr)))
    pixmap = QPixmap.fromImage(square).scaled(
        physical,
        physical,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    pixmap.setDevicePixelRatio(physical / float(size))
    return pixmap


def play_icon(size, color=None):
    """Play button artwork: the Cascabel logo with its margins trimmed.

    `color` is accepted so call sites stay identical to the drawn_icons
    helpers; the SVG carries its own colors, so it is ignored.
    """
    square = _trimmed_square("play")
    if square is None:
        return drawn_icons.play_icon(size, color or "#f2f2f2")
    return _scaled_pixmap(square, size)


def pause_icon(size, color=None):
    """Pause button artwork: the CascabelPause logo with margins trimmed."""
    square = _trimmed_square("pause")
    if square is None:
        return drawn_icons.pause_icon(size, color or "#f2f2f2")
    return _scaled_pixmap(square, size)


def harden_alpha(image, threshold=128):
    """Snap semi-transparent pixels to fully opaque or fully transparent.

    Taskbar / titlebar icons sit on unpredictable backgrounds: every
    partial-alpha pixel on the artwork's edge lets the background bleed
    through, and on a light background the whole anti-aliased rim reads as a
    white outline. A hard 0/255 alpha edge has no feather, so nothing can
    bleed through on any background - at the small sizes where this is
    applied the crisp edge also just looks better.
    """
    result = image.convertToFormat(QImage.Format.Format_ARGB32)
    opaque = 0xFF000000
    for y in range(result.height()):
        for x in range(result.width()):
            pixel = result.pixel(x, y)
            alpha = (pixel >> 24) & 0xFF
            if 0 < alpha < 255:
                result.setPixel(x, y, (pixel | opaque) if alpha >= threshold else 0)
    return result


def app_icon():
    """Window/taskbar icon built from the trimmed Cascabel logo."""
    square = _trimmed_square("play")
    if square is None:
        return QIcon()
    source = QPixmap.fromImage(square)
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pixmap = source.scaled(
            size,
            size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        if size <= 64:
            pixmap = QPixmap.fromImage(harden_alpha(pixmap.toImage()))
        icon.addPixmap(pixmap)
    return icon


def trimmed_logo_image():
    """The margin-trimmed, square-padded logo as a QImage (None if unavailable)."""
    return _trimmed_square("play")


def logo_pixmap(size):
    """The trimmed Cascabel logo as a plain pixmap for misc UI uses."""
    square = _trimmed_square("play")
    if square is None:
        return QPixmap()
    return _scaled_pixmap(square, size)
