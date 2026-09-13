from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class WatermarkConfig:
    """
    Configuration used by the watermark engine.
    """

    watermark_type: str = "text"

    text: str = "CONFIDENTIAL"

    image_path: Optional[str] = None

    font_size: int = 48

    opacity: float = 0.30

    rotation: float = -45.0

    scale: float = 1.0

    position: str = "center"

    font_name: str = "Helvetica-Bold"

    text_color: tuple[float, float, float] = (
        0.45,
        0.45,
        0.45,
    )

    def validate(self) -> None:
        """
        Validate watermark configuration.
        """

        if self.watermark_type not in {
            "text",
            "image",
        }:
            raise ValueError(
                "Watermark type must be 'text' or 'image'."
            )

        if self.watermark_type == "text":

            if not self.text.strip():
                raise ValueError(
                    "Watermark text cannot be empty."
                )

        if self.watermark_type == "image":

            if not self.image_path:
                raise ValueError(
                    "Please select a watermark image."
                )

            path = Path(
                self.image_path
            )

            if not path.exists():
                raise ValueError(
                    "The selected watermark image does not exist."
                )

            if path.suffix.lower() not in {
                ".png",
                ".jpg",
                ".jpeg",
                ".webp",
            }:
                raise ValueError(
                    "Supported image formats: PNG, JPG, JPEG and WEBP."
                )

        if not 0.0 < self.opacity <= 1.0:
            raise ValueError(
                "Opacity must be between 0 and 1."
            )

        if not -360.0 <= self.rotation <= 360.0:
            raise ValueError(
                "Rotation must be between -360 and 360 degrees."
            )

        if self.scale <= 0:
            raise ValueError(
                "Scale must be greater than zero."
            )

        valid_positions = {
            "top-left",
            "top-center",
            "top-right",
            "center-left",
            "center",
            "center-right",
            "bottom-left",
            "bottom-center",
            "bottom-right",
        }

        if self.position not in valid_positions:
            raise ValueError(
                f"Invalid watermark position: {self.position}"
            )