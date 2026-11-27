"""
logo.py — the company logo, uploaded at /settings — a LEAF
==========================================================
The logo used to be artwork committed under `assets/`. It is a /settings upload
now: nothing company-specific ships in the repository, and the company that
runs the application puts its own mark on its own documents.

Why the logo is RE-ENCODED, never stored as uploaded
----------------------------------------------------
`photo.py`'s reasons, one for one: a re-encode strips metadata, kills
polyglots, makes the stored size small and fixed, and lets the image live in
the database as a base64 data URI — the repo's convention for images (no
`/static`, ABOUT.md §1). Unlike a profile photo, a logo is **fitted, never
cropped**, keeps its transparency, and is written as PNG.

Three sizes are written, because each one rides on different pages:

    doc      256 px   the printed letterhead (print quality)
    nav       64 px   the app's top bar and rail
    favicon   32 px   the browser tab

Record shape (STORE["settings"]["logo"])::

    doc / nav / favicon   "data:image/png;base64,..."
    updated_at            "YYYY-MM-DD HH:MM:SS"
    updated_by            uid of whoever set it

⚠ `branding.apply_logo()` is the only reader, and it accepts only the exact
  shape written here — a record edited straight into MySQL can never put
  anything but a base64 PNG into an `<img src>`.

⚠ **Imports nothing from the app.** `settings.py` imports this module;
  `tests/test_import_directions.py` holds the leaf.
"""

import base64
import datetime
import io
import os
import warnings

MAX_BYTES = 5 * 1024 * 1024        # same ceiling as attachments and photos
MAX_PIXELS = 40_000_000             # refuse decompression bombs before decoding
SIZES = (("doc", 256), ("nav", 64), ("favicon", 32))
PREFIX = "data:image/png;base64,"
# A 256 px PNG of a real logo is ~10-60 KB; this is the hard ceiling on what a
# stored record can make every printed page carry.
MAX_STORED = 400 * 1024

SIGNATURES = (
    (b"\xff\xd8\xff", "JPEG"),
    (b"\x89PNG\r\n\x1a\n", "PNG"),
)
ALLOWED_LABEL = "PNG, JPEG or WebP"


def _sniff(head: bytes) -> str:
    for sig, fmt in SIGNATURES:
        if head.startswith(sig):
            return fmt
    if len(head) >= 12 and head[:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "WEBP"
    return ""


def _size_of(fs) -> int:
    stream = fs.stream
    here = stream.tell()
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(here, os.SEEK_SET)
    return int(size)


def _fit(img, side: int):
    """`img` scaled to fit a `side` x `side` transparent square, centred."""
    from PIL import Image

    work = img.copy()
    work.thumbnail((side, side), Image.LANCZOS)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.paste(work, ((side - work.width) // 2, (side - work.height) // 2), work)
    return canvas


def encode(fs) -> tuple:
    """
    `(record, error)` for one uploaded file. Exactly one of the two is empty.
    Order is size, then leading bytes, then decode — the cheap refusals first.
    """
    if fs is None or not (getattr(fs, "filename", "") or "").strip():
        return {}, "No logo file was chosen."
    size = _size_of(fs)
    if size <= 0:
        return {}, "That file is empty."
    if size > MAX_BYTES:
        return {}, (f"That file is {size / 1048576:.1f} MB and the limit is "
                    f"{MAX_BYTES / 1048576:.0f} MB.")
    raw = fs.stream.read(MAX_BYTES + 1)
    fmt = _sniff(raw[:16])
    if not fmt:
        return {}, f"That file is not a {ALLOWED_LABEL} image."
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return {}, "Logo upload is not available on this server yet."
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            old_limit = Image.MAX_IMAGE_PIXELS
            Image.MAX_IMAGE_PIXELS = MAX_PIXELS
            try:
                img = Image.open(io.BytesIO(raw))
                if (img.format or "").upper() != fmt:
                    return {}, f"That file is not a {ALLOWED_LABEL} image."
                img.load()
            finally:
                Image.MAX_IMAGE_PIXELS = old_limit
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        return {}, "That image is too large to process. Use a normal logo file."
    except Exception:
        return {}, "That image could not be read. Try saving it again as a PNG."
    img = ImageOps.exif_transpose(img).convert("RGBA")

    rec = {}
    for key, side in SIZES:
        out = io.BytesIO()
        _fit(img, side).save(out, "PNG", optimize=True)   # pixels only, no metadata
        uri = PREFIX + base64.b64encode(out.getvalue()).decode("ascii")
        if len(uri) > MAX_STORED:
            return {}, "That logo could not be made small enough. Try a simpler image."
        rec[key] = uri
    return rec, ""


def stamp(rec: dict, by: str) -> dict:
    """The record as stored: the three images plus who set it and when."""
    out = dict(rec)
    out["updated_at"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    out["updated_by"] = by or ""
    return out
