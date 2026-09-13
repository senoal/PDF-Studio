from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class PageManagerError(Exception):
    """Base exception for page management operations."""


class PageManager:
    """Handle PDF page manipulation."""

    def validate_pdf(self, file_path: str) -> int:
        """
        Validate a PDF and return its page count.

        Raises:
            PageManagerError: If the PDF cannot be read.
        """
        path = Path(file_path)

        if not path.exists():
            raise PageManagerError(
                f"File not found: {path.name}"
            )

        if not path.is_file():
            raise PageManagerError(
                f"Selected path is not a file: {path.name}"
            )

        if path.suffix.lower() != ".pdf":
            raise PageManagerError(
                f"Only PDF files are supported: {path.name}"
            )

        try:
            reader = PdfReader(str(path))

            if reader.is_encrypted:
                raise PageManagerError(
                    f"Encrypted PDF cannot be processed: "
                    f"{path.name}"
                )

            page_count = len(reader.pages)

            if page_count == 0:
                raise PageManagerError(
                    f"PDF contains no pages: {path.name}"
                )

            return page_count

        except PageManagerError:
            raise

        except PdfReadError as exc:
            raise PageManagerError(
                f"Invalid or corrupted PDF: {path.name}"
            ) from exc

        except Exception as exc:
            raise PageManagerError(
                f"Unable to read PDF: {path.name}"
            ) from exc

    def delete_pages(
        self,
        input_file: str,
        pages_to_delete: Iterable[int],
        output_file: str,
    ) -> None:
        """
        Delete selected pages from a PDF.

        Page indexes are zero-based.

        Args:
            input_file: Source PDF.
            pages_to_delete: Zero-based page indexes.
            output_file: Destination PDF.
        """
        input_path = Path(input_file).resolve()
        output_path = Path(output_file).resolve()

        if input_path == output_path:
            raise PageManagerError(
                "The output file cannot be the source PDF."
            )

        delete_indexes = sorted(
            set(int(index) for index in pages_to_delete)
        )

        try:
            reader = PdfReader(str(input_path))

            if reader.is_encrypted:
                raise PageManagerError(
                    "Encrypted PDFs are not supported."
                )

            total_pages = len(reader.pages)

            if total_pages == 0:
                raise PageManagerError(
                    "The PDF contains no pages."
                )

            for index in delete_indexes:
                if index < 0 or index >= total_pages:
                    raise PageManagerError(
                        f"Invalid page index: {index + 1}"
                    )

            remaining_pages = (
                total_pages - len(delete_indexes)
            )

            if remaining_pages <= 0:
                raise PageManagerError(
                    "You cannot delete all pages from a PDF."
                )

            delete_set = set(delete_indexes)

            writer = PdfWriter()

            for index, page in enumerate(reader.pages):
                if index not in delete_set:
                    writer.add_page(page)

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with output_path.open("wb") as output_stream:
                writer.write(output_stream)

            writer.close()

        except PageManagerError:
            raise

        except PdfReadError as exc:
            raise PageManagerError(
                "The source PDF is invalid or corrupted."
            ) from exc

        except PermissionError as exc:
            raise PageManagerError(
                "Permission denied while writing the output PDF."
            ) from exc

        except OSError as exc:
            raise PageManagerError(
                f"Unable to write output file: "
                f"{output_path.name}"
            ) from exc

        except Exception as exc:
            raise PageManagerError(
                "An unexpected error occurred while deleting pages."
            ) from exc

    def get_page_count(self, file_path: str) -> int:
        """Return the number of pages in a PDF."""
        return self.validate_pdf(file_path)