from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pypdf import PdfReader, PdfWriter
from pypdf.errors import PdfReadError


class PDFMergerError(Exception):
    """Base exception for PDF merge operations."""


class PDFMerger:
    """Handle PDF merging operations."""

    def validate_pdf(self, file_path: str) -> None:
        """
        Validate that a file exists and can be read as a PDF.

        Raises:
            PDFMergerError: If the file is invalid or unreadable.
        """
        path = Path(file_path)

        if not path.exists():
            raise PDFMergerError(
                f"File not found: {path.name}"
            )

        if not path.is_file():
            raise PDFMergerError(
                f"Not a file: {path.name}"
            )

        if path.suffix.lower() != ".pdf":
            raise PDFMergerError(
                f"Unsupported file type: {path.name}"
            )

        try:
            reader = PdfReader(str(path))

            if reader.is_encrypted:
                raise PDFMergerError(
                    f"Encrypted PDF cannot be merged without "
                    f"unlocking it first: {path.name}"
                )

            # Force page access to detect malformed PDFs.
            _ = len(reader.pages)

        except PdfReadError as exc:
            raise PDFMergerError(
                f"Invalid or corrupted PDF: {path.name}"
            ) from exc

        except PDFMergerError:
            raise

        except Exception as exc:
            raise PDFMergerError(
                f"Unable to read PDF: {path.name}"
            ) from exc

    def merge(
        self,
        input_files: Iterable[str],
        output_file: str,
    ) -> None:
        """
        Merge multiple PDF files into one PDF.

        Args:
            input_files: PDF files in desired merge order.
            output_file: Destination PDF path.

        Raises:
            PDFMergerError: If merging fails.
        """
        files = [str(Path(file)) for file in input_files]

        if len(files) < 2:
            raise PDFMergerError(
                "At least two PDF files are required."
            )

        output_path = Path(output_file).resolve()

        # Validate all input files before creating output.
        for file_path in files:
            self.validate_pdf(file_path)

        # Prevent output from being one of the input files.
        input_paths = {
            Path(file).resolve()
            for file in files
        }

        if output_path in input_paths:
            raise PDFMergerError(
                "The output file cannot be one of the input files."
            )

        writer = PdfWriter()
        readers: list[PdfReader] = []

        try:
            for file_path in files:
                reader = PdfReader(file_path)
                readers.append(reader)

                for page in reader.pages:
                    writer.add_page(page)

            if len(writer.pages) == 0:
                raise PDFMergerError(
                    "The selected PDFs contain no pages."
                )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )

            with output_path.open("wb") as output_stream:
                writer.write(output_stream)

        except PDFMergerError:
            raise

        except PermissionError as exc:
            raise PDFMergerError(
                "Permission denied while creating the output PDF."
            ) from exc

        except OSError as exc:
            raise PDFMergerError(
                f"Unable to write output file: "
                f"{output_path.name}"
            ) from exc

        except Exception as exc:
            raise PDFMergerError(
                "An unexpected error occurred while merging PDFs."
            ) from exc

        finally:
            writer.close()

            # Explicitly close readers where supported.
            for reader in readers:
                stream = getattr(reader, "stream", None)

                if stream is not None:
                    try:
                        stream.close()
                    except Exception:
                        pass