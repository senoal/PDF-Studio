from __future__ import annotations

from app.core.page_manager import (
    PageManager,
    PageManagerError,
)

from app.core.pdf_merger import (
    PDFMerger,
    PDFMergerError,
)


class PDFService:
    """High-level PDF application service."""

    def __init__(self) -> None:
        self.merger = PDFMerger()
        self.page_manager = PageManager()

    # ========================================================
    # MERGE
    # ========================================================

    def validate_pdf(
        self,
        file_path: str,
    ) -> tuple[bool, str]:

        try:
            self.merger.validate_pdf(
                file_path
            )

            return True, "PDF is valid."

        except PDFMergerError as exc:
            return False, str(exc)

        except Exception:
            return (
                False,
                "Unable to validate PDF.",
            )

    def merge_pdfs(
        self,
        input_files: list[str],
        output_file: str,
    ) -> tuple[bool, str]:

        try:
            self.merger.merge(
                input_files=input_files,
                output_file=output_file,
            )

            return (
                True,
                "PDF files merged successfully.",
            )

        except PDFMergerError as exc:
            return False, str(exc)

        except Exception:
            return (
                False,
                "An unexpected error occurred.",
            )

    # ========================================================
    # PAGE MANAGEMENT
    # ========================================================

    def get_page_count(
        self,
        file_path: str,
    ) -> tuple[bool, int | str]:

        try:
            count = (
                self.page_manager.get_page_count(
                    file_path
                )
            )

            return True, count

        except PageManagerError as exc:
            return False, str(exc)

        except Exception:
            return (
                False,
                "Unable to read PDF page count.",
            )

    def delete_pages(
        self,
        input_file: str,
        pages_to_delete: list[int],
        output_file: str,
    ) -> tuple[bool, str]:

        try:
            self.page_manager.delete_pages(
                input_file=input_file,
                pages_to_delete=pages_to_delete,
                output_file=output_file,
            )

            return (
                True,
                "Pages deleted successfully.",
            )

        except PageManagerError as exc:
            return False, str(exc)

        except Exception:
            return (
                False,
                "An unexpected error occurred.",
            )