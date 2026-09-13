from __future__ import annotations

import io

from PIL import Image, ImageTk


def bytes_to_pil_image(
    image_data: bytes,
) -> Image.Image:
    """Convert image bytes to PIL Image."""

    stream = io.BytesIO(
        image_data
    )

    image = Image.open(stream)

    return image.copy()


def bytes_to_tk_image(
    image_data: bytes,
    max_width: int = 180,
    max_height: int = 240,
) -> ImageTk.PhotoImage:
    """
    Convert image bytes to a resized Tkinter image.
    """

    image = bytes_to_pil_image(
        image_data
    )

    image.thumbnail(
        (max_width, max_height),
        Image.Resampling.LANCZOS,
    )

    return ImageTk.PhotoImage(
        image
    )