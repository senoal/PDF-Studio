from __future__ import annotations

from pathlib import Path


def is_pdf_file(file_path: str) -> bool:
    """Return True if the file has a PDF extension."""
    return Path(file_path).suffix.lower() == ".pdf"


def validate_pdf_file(file_path: str) -> tuple[bool, str]:
    """
    Basic PDF file validation.

    Returns:
        Tuple containing success state and message.
    """
    path = Path(file_path)

    if not path.exists():
        return False, "File does not exist."

    if not path.is_file():
        return False, "Selected path is not a file."

    if not is_pdf_file(file_path):
        return False, "Only PDF files are supported."

    return True, "Valid PDF file."


def validate_merge_list(
    files: list[str],
) -> tuple[bool, str]:
    """Validate a list of PDF files for merging."""

    if not files:
        return False, "Please add PDF files first."

    if len(files) < 2:
        return (
            False,
            "Please add at least two PDF files to merge.",
        )

    for file_path in files:
        valid, message = validate_pdf_file(file_path)

        if not valid:
            return False, message

    return True, "Ready to merge."