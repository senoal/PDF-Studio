"""
PDF Security Core
-----------------
Low-level PDF encryption/decryption operations.

Supported:
- Encrypt PDF with password
- Decrypt password-protected PDF
- Detect encrypted PDF
- Validate decrypt password
- Remove encryption from PDF
"""

from pathlib import Path
from typing import Optional, Tuple

from pypdf import PdfReader, PdfWriter


class PDFSecurityError(Exception):
    """Raised when a PDF security operation fails."""


class PDFSecurity:
    """
    Core security manager for PDF encryption/decryption.
    """

    @staticmethod
    def is_encrypted(pdf_path: str) -> bool:
        """
        Check whether a PDF is encrypted.

        Important:
        This method does NOT attempt to read/decrypt the pages.
        It only checks the PDF encryption flag.
        """
        try:
            path = Path(pdf_path)

            if not path.exists():
                raise PDFSecurityError(
                    f"PDF file does not exist:\n{path}"
                )

            if path.suffix.lower() != ".pdf":
                raise PDFSecurityError(
                    "Selected file is not a PDF."
                )

            reader = PdfReader(
                str(path),
                strict=False
            )

            return bool(reader.is_encrypted)

        except PDFSecurityError:
            raise

        except Exception as exc:
            raise PDFSecurityError(
                f"Unable to inspect PDF encryption status.\n\n{exc}"
            ) from exc

    @staticmethod
    def get_pdf_status(pdf_path: str) -> dict:
        """
        Return basic PDF status without requiring decryption.
        """

        try:
            path = Path(pdf_path)

            if not path.exists():
                raise PDFSecurityError(
                    f"PDF file does not exist:\n{path}"
                )

            reader = PdfReader(
                str(path),
                strict=False
            )

            encrypted = bool(reader.is_encrypted)

            page_count: Optional[int] = None

            # Do not access pages of encrypted documents
            # before password authentication.
            if not encrypted:
                page_count = len(reader.pages)

            return {
                "path": str(path),
                "filename": path.name,
                "encrypted": encrypted,
                "page_count": page_count,
            }

        except PDFSecurityError:
            raise

        except Exception as exc:
            raise PDFSecurityError(
                f"Unable to inspect PDF.\n\n{exc}"
            ) from exc

    @staticmethod
    def encrypt_pdf(
        input_path: str,
        output_path: str,
        user_password: str,
        owner_password: Optional[str] = None,
    ) -> Tuple[bool, str]:
        """
        Encrypt a PDF.

        user_password:
            Password required to open the PDF.

        owner_password:
            Optional owner password.
            If omitted, user password is used.
        """

        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            raise PDFSecurityError(
                "Source PDF does not exist."
            )

        if not user_password:
            raise PDFSecurityError(
                "Password cannot be empty."
            )

        if owner_password is None or not owner_password:
            owner_password = user_password

        try:
            reader = PdfReader(
                str(input_file),
                strict=False
            )

            if reader.is_encrypted:
                raise PDFSecurityError(
                    "The selected PDF is already encrypted.\n"
                    "Decrypt it first before encrypting it again."
                )

            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # Preserve metadata when possible.
            if reader.metadata:
                try:
                    writer.add_metadata(
                        dict(reader.metadata)
                    )
                except Exception:
                    pass

            # Use AES-256 when supported by the installed pypdf.
            encryption_done = False

            try:
                writer.encrypt(
                    user_password=user_password,
                    owner_password=owner_password,
                    algorithm="AES-256",
                )
                encryption_done = True
            except (TypeError, ValueError):
                pass

            # Compatibility fallback for older pypdf versions.
            if not encryption_done:
                try:
                    writer.encrypt(
                        user_password=user_password,
                        owner_password=owner_password,
                    )
                    encryption_done = True
                except TypeError:
                    writer.encrypt(
                        user_password,
                        owner_password,
                    )
                    encryption_done = True

            output_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            with open(output_file, "wb") as output_stream:
                writer.write(output_stream)

            return (
                True,
                f"PDF encrypted successfully:\n{output_file}"
            )

        except PDFSecurityError:
            raise

        except Exception as exc:
            raise PDFSecurityError(
                f"Failed to encrypt PDF.\n\n{exc}"
            ) from exc

    @staticmethod
    def decrypt_pdf(
        input_path: str,
        output_path: str,
        password: str,
    ) -> Tuple[bool, str]:
        """
        Decrypt a password-protected PDF.

        The resulting PDF is written without encryption.
        """

        input_file = Path(input_path)
        output_file = Path(output_path)

        if not input_file.exists():
            raise PDFSecurityError(
                "Source PDF does not exist."
            )

        if not password:
            raise PDFSecurityError(
                "Enter the PDF password."
            )

        try:
            # IMPORTANT:
            # Construct reader first.
            # This is allowed even if the PDF is encrypted.
            reader = PdfReader(
                str(input_file),
                strict=False
            )

            if not reader.is_encrypted:
                raise PDFSecurityError(
                    "This PDF is not encrypted.\n"
                    "There is no password to remove."
                )

            # Authenticate the encrypted PDF.
            decrypt_result = reader.decrypt(password)

            if decrypt_result == 0:
                raise PDFSecurityError(
                    "Incorrect PDF password.\n"
                    "The document could not be decrypted."
                )

            # Only access pages AFTER successful authentication.
            writer = PdfWriter()

            for page in reader.pages:
                writer.add_page(page)

            # Preserve metadata where possible.
            if reader.metadata:
                try:
                    writer.add_metadata(
                        dict(reader.metadata)
                    )
                except Exception:
                    pass

            output_file.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            # Important:
            # We intentionally DO NOT call writer.encrypt().
            # Therefore the generated PDF has no password.
            with open(output_file, "wb") as output_stream:
                writer.write(output_stream)

            return (
                True,
                f"PDF decrypted successfully:\n{output_file}"
            )

        except PDFSecurityError:
            raise

        except Exception as exc:
            raise PDFSecurityError(
                f"Failed to decrypt PDF.\n\n{exc}"
            ) from exc

    @staticmethod
    def validate_password(
        pdf_path: str,
        password: str
    ) -> bool:
        """
        Validate whether a password can unlock an encrypted PDF.
        """

        if not password:
            return False

        try:
            reader = PdfReader(
                str(pdf_path),
                strict=False
            )

            if not reader.is_encrypted:
                return False

            result = reader.decrypt(password)

            return result != 0

        except Exception:
            return False


# Backward-compatible aliases
SecurityManager = PDFSecurity
PDFSecurityManager = PDFSecurity