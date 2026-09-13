from __future__ import annotations

from dataclasses import dataclass

import fitz


class PreviewServiceError(Exception):
    """Base exception for preview operations."""


@dataclass
class PagePreview:
    """Rendered PDF page preview."""

    page_index: int
    width: int
    height: int
    image_data: bytes


class PreviewService:
    """Render PDF pages into preview images."""

    def __init__(
        self,
        dpi: int = 100,
    ) -> None:

        self.dpi = max(
            50,
            min(dpi, 200),
        )
        self._document: fitz.Document | None = None
        self._document_path: str | None = None

    def close(self) -> None:
        """Release the cached preview document and its file handle."""
        if self._document is not None:
            self._document.close()
        self._document = None
        self._document_path = None

    def _get_document(self, pdf_path: str) -> fitz.Document:
        """Reuse one open document while rendering a page sequence."""
        normalized_path = str(pdf_path)
        if self._document is None or self._document_path != normalized_path:
            self.close()
            self._document = fitz.open(normalized_path)
            self._document_path = normalized_path

        if self._document.needs_pass:
            raise PreviewServiceError("Encrypted PDFs are not supported.")

        return self._document

    def get_page_count(
        self,
        pdf_path: str,
    ) -> int:

        try:
            document = self._get_document(pdf_path)
            return document.page_count

        except PreviewServiceError:
            raise

        except Exception as exc:
            raise PreviewServiceError(
                "Unable to open PDF for preview."
            ) from exc

    def render_page(
        self,
        pdf_path: str,
        page_index: int,
    ) -> PagePreview:

        try:
            document = self._get_document(pdf_path)
            if (
                page_index < 0
                or page_index >= document.page_count
            ):
                raise PreviewServiceError(
                    f"Invalid page index: {page_index + 1}"
                )

            page = document.load_page(page_index)

            scale = self.dpi / 72.0

            matrix = fitz.Matrix(
                scale,
                scale,
            )

            pixmap = page.get_pixmap(
                matrix=matrix,
                alpha=False,
            )

            image_data = pixmap.tobytes(
                "ppm"
            )

            return PagePreview(
                page_index=page_index,
                width=pixmap.width,
                height=pixmap.height,
                image_data=image_data,
            )

        except PreviewServiceError:
            raise

        except Exception as exc:
            raise PreviewServiceError(
                f"Unable to render page "
                f"{page_index + 1}."
            ) from exc

    def render_all_pages(
        self,
        pdf_path: str,
    ) -> list[PagePreview]:

        previews = []

        page_count = self.get_page_count(
            pdf_path
        )

        for page_index in range(page_count):
            previews.append(
                self.render_page(
                    pdf_path,
                    page_index,
                )
            )

        return previews
