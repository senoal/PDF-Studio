from __future__ import annotations

import io
from pathlib import Path

from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from app.core.watermark import WatermarkConfig


class WatermarkService:

    def __init__(self):
        pass

    # ==========================================================
    # PUBLIC API
    # ==========================================================

    def apply_watermark(
        self,
        input_file: str,
        output_file: str,
        config: WatermarkConfig,
        page_indexes: list[int] | None = None,
    ):
        """
        Apply watermark to a PDF.

        page_indexes:
            None -> all pages
            list -> zero-based page indexes
        """

        input_path = Path(
            input_file
        )

        output_path = Path(
            output_file
        )

        if not input_path.exists():
            return (
                False,
                "Source PDF does not exist.",
            )

        try:

            config.validate()

            reader = PdfReader(
                str(input_path)
            )

            writer = PdfWriter()

            total_pages = len(
                reader.pages
            )

            if total_pages == 0:
                return (
                    False,
                    "The PDF contains no pages.",
                )

            if page_indexes is None:

                target_pages = set(
                    range(total_pages)
                )

            else:

                target_pages = set(
                    page_indexes
                )

                for index in target_pages:

                    if index < 0 or index >= total_pages:

                        return (
                            False,
                            (
                                f"Invalid page index: "
                                f"{index + 1}"
                            ),
                        )

            for index, page in enumerate(
                reader.pages
            ):

                if index in target_pages:

                    page_width = float(
                        page.mediabox.width
                    )

                    page_height = float(
                        page.mediabox.height
                    )

                    overlay = (
                        self._create_overlay(
                            page_width=page_width,
                            page_height=page_height,
                            config=config,
                        )
                    )

                    page.merge_page(
                        overlay
                    )

                writer.add_page(
                    page
                )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with output_path.open(
                "wb"
            ) as file:

                writer.write(
                    file
                )

            return (
                True,
                (
                    f"Watermark applied successfully "
                    f"to {len(target_pages)} page(s)."
                ),
            )

        except Exception as exc:

            return (
                False,
                str(exc),
            )

    # ==========================================================
    # OVERLAY
    # ==========================================================

    def _create_overlay(
        self,
        page_width: float,
        page_height: float,
        config: WatermarkConfig,
    ):

        buffer = io.BytesIO()

        pdf = canvas.Canvas(
            buffer,
            pagesize=(
                page_width,
                page_height,
            ),
        )

        if config.watermark_type == "text":

            self._draw_text(
                pdf,
                page_width,
                page_height,
                config,
            )

        else:

            self._draw_image(
                pdf,
                page_width,
                page_height,
                config,
            )

        pdf.save()

        buffer.seek(0)

        overlay_reader = PdfReader(
            buffer
        )

        return overlay_reader.pages[0]

    # ==========================================================
    # TEXT WATERMARK
    # ==========================================================

    def _draw_text(
        self,
        pdf,
        page_width,
        page_height,
        config,
    ):

        text = config.text.strip()

        if not text:
            return

        font_size = (
            config.font_size
            * config.scale
        )

        font_size = max(
            6,
            min(
                font_size,
                300,
            ),
        )

        pdf.saveState()

        pdf.setFillAlpha(
            config.opacity
        )

        pdf.setFillColorRGB(
            *config.text_color
        )

        pdf.setFont(
            config.font_name,
            font_size,
        )

        text_width = pdf.stringWidth(
            text,
            config.font_name,
            font_size,
        )

        text_height = font_size

        x, y = self._calculate_position(
            page_width,
            page_height,
            text_width,
            text_height,
            config.position,
        )

        pdf.translate(
            x,
            y,
        )

        pdf.rotate(
            config.rotation
        )

        pdf.drawString(
            -text_width / 2,
            0,
            text,
        )

        pdf.restoreState()

    # ==========================================================
    # IMAGE WATERMARK
    # ==========================================================

    def _draw_image(
        self,
        pdf,
        page_width,
        page_height,
        config,
    ):

        if not config.image_path:
            return

        image_path = Path(
            config.image_path
        )

        if not image_path.exists():
            raise ValueError(
                "Watermark image does not exist."
            )

        image = Image.open(
            image_path
        )

        image_width, image_height = (
            image.size
        )

        if image_width <= 0 or image_height <= 0:
            raise ValueError(
                "Invalid watermark image dimensions."
            )

        # Base image width = 30% of PDF width.
        target_width = (
            page_width
            * 0.30
            * config.scale
        )

        target_width = max(
            20,
            min(
                target_width,
                page_width * 0.75,
            ),
        )

        ratio = (
            target_width
            / image_width
        )

        target_height = (
            image_height
            * ratio
        )

        # Prepare transparent PNG.
        rgba = image.convert(
            "RGBA"
        )

        alpha = rgba.getchannel(
            "A"
        )

        alpha = alpha.point(
            lambda value:
            int(
                value
                * config.opacity
            )
        )

        rgba.putalpha(
            alpha
        )

        image_buffer = io.BytesIO()

        rgba.save(
            image_buffer,
            format="PNG",
        )

        image_buffer.seek(0)

        image_reader = ImageReader(
            image_buffer
        )

        x, y = self._calculate_position(
            page_width,
            page_height,
            target_width,
            target_height,
            config.position,
        )

        pdf.saveState()

        pdf.translate(
            x,
            y,
        )

        pdf.rotate(
            config.rotation
        )

        pdf.drawImage(
            image_reader,
            -target_width / 2,
            -target_height / 2,
            width=target_width,
            height=target_height,
            preserveAspectRatio=True,
            mask="auto",
        )

        pdf.restoreState()

    # ==========================================================
    # POSITION
    # ==========================================================

    def _calculate_position(
        self,
        page_width,
        page_height,
        object_width,
        object_height,
        position,
    ):

        positions = {

            "top-left": (
                page_width * 0.18,
                page_height * 0.85,
            ),

            "top-center": (
                page_width * 0.50,
                page_height * 0.85,
            ),

            "top-right": (
                page_width * 0.82,
                page_height * 0.85,
            ),

            "center-left": (
                page_width * 0.18,
                page_height * 0.50,
            ),

            "center": (
                page_width * 0.50,
                page_height * 0.50,
            ),

            "center-right": (
                page_width * 0.82,
                page_height * 0.50,
            ),

            "bottom-left": (
                page_width * 0.18,
                page_height * 0.15,
            ),

            "bottom-center": (
                page_width * 0.50,
                page_height * 0.15,
            ),

            "bottom-right": (
                page_width * 0.82,
                page_height * 0.15,
            ),
        }

        return positions.get(
            position,
            positions["center"],
        )