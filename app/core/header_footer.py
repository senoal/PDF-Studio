from __future__ import annotations

from pathlib import Path
from typing import Optional

import fitz


class HeaderFooterProcessor:
    """
    Core processor for adding text/image headers and footers to PDF files.

    Coordinates use PDF points.
    """

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def apply(
        self,
        input_path: str,
        output_path: str,
        header: Optional[dict] = None,
        footer: Optional[dict] = None,
    ) -> str:
        """
        Apply header/footer configuration to a PDF.

        Example:

        header = {
            "enabled": True,
            "type": "image",
            "image_path": "...",
            "margin": 24,
            "height": 80,
            "alignment": "center",
        }

        footer = {
            "enabled": True,
            "type": "text",
            "text": "Page {page} of {pages}",
            "margin": 24,
            "height": 40,
            "alignment": "center",
        }
        """

        input_path = str(input_path)
        output_path = str(output_path)

        document = fitz.open(input_path)

        try:
            total_pages = len(document)

            for page_number, page in enumerate(document, start=1):
                if header and header.get("enabled"):
                    self._apply_element(
                        page=page,
                        config=header,
                        page_number=page_number,
                        total_pages=total_pages,
                        is_header=True,
                    )

                if footer and footer.get("enabled"):
                    self._apply_element(
                        page=page,
                        config=footer,
                        page_number=page_number,
                        total_pages=total_pages,
                        is_header=False,
                    )

            output_file = Path(output_path)

            if output_file.exists():
                output_file.unlink()

            document.save(
                str(output_file),
                garbage=4,
                deflate=True,
                clean=True,
            )

        finally:
            document.close()

        return output_path

    # ------------------------------------------------------------------
    # ELEMENT
    # ------------------------------------------------------------------

    def _apply_element(
        self,
        page,
        config: dict,
        page_number: int,
        total_pages: int,
        is_header: bool,
    ):
        page_rect = page.rect

        margin = float(config.get("margin", 24))
        height = float(config.get("height", 72))

        margin = max(0, margin)
        height = max(10, height)

        available_width = page_rect.width - (margin * 2)

        if available_width <= 0:
            return

        if is_header:
            rect = fitz.Rect(
                margin,
                margin,
                page_rect.width - margin,
                margin + height,
            )
        else:
            rect = fitz.Rect(
                margin,
                page_rect.height - margin - height,
                page_rect.width - margin,
                page_rect.height - margin,
            )

        element_type = str(
            config.get("type", "text")
        ).lower().strip()

        if element_type == "image":
            self._insert_image(
                page,
                rect,
                config.get("image_path"),
            )
        else:
            self._insert_text(
                page,
                rect,
                config,
                page_number,
                total_pages,
            )

    # ------------------------------------------------------------------
    # IMAGE
    # ------------------------------------------------------------------

    def _insert_image(
        self,
        page,
        rect: fitz.Rect,
        image_path: Optional[str],
    ):
        if not image_path:
            return

        image_file = Path(image_path)

        if not image_file.exists():
            return

        try:
            # Fill the complete header/footer area.
            #
            # This intentionally uses the complete rectangle so a
            # letterhead/header image can occupy the full configured
            # header/footer dimensions.
            page.insert_image(
                rect,
                filename=str(image_file),
                keep_proportion=False,
                overlay=True,
            )

        except Exception:
            # Fallback for unusual image formats.
            try:
                pix = fitz.Pixmap(str(image_file))

                if pix.alpha:
                    pix = fitz.Pixmap(
                        fitz.csRGB,
                        pix,
                    )

                page.insert_image(
                    rect,
                    pixmap=pix,
                    keep_proportion=False,
                    overlay=True,
                )

            except Exception:
                pass

    # ------------------------------------------------------------------
    # TEXT
    # ------------------------------------------------------------------

    def _insert_text(
        self,
        page,
        rect: fitz.Rect,
        config: dict,
        page_number: int,
        total_pages: int,
    ):
        text = str(config.get("text", "")).strip()

        if not text:
            return

        text = text.replace(
            "{page}",
            str(page_number),
        )

        text = text.replace(
            "{pages}",
            str(total_pages),
        )

        text = text.replace(
            "{total_pages}",
            str(total_pages),
        )

        alignment_name = str(
            config.get("alignment", "center")
        ).lower()

        alignment_map = {
            "left": 0,
            "center": 1,
            "right": 2,
        }

        align = alignment_map.get(
            alignment_name,
            1,
        )

        font_size = float(
            config.get("font_size", 9)
        )

        font_size = max(
            5,
            min(font_size, 72),
        )

        color = config.get(
            "color",
            (0.15, 0.15, 0.18),
        )

        try:
            page.insert_textbox(
                rect,
                text,
                fontsize=font_size,
                fontname="helv",
                color=color,
                align=align,
                overlay=True,
            )
        except Exception:
            pass