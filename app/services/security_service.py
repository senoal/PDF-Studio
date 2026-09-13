"""
PDF Security Service
--------------------
Application-level wrapper around the PDF security core.
"""

from pathlib import Path
from typing import Optional

from app.core.security import (
    PDFSecurity,
    PDFSecurityError,
)


class SecurityService:
    """
    Service layer for PDF encryption/decryption.
    """

    def __init__(self):
        self.security = PDFSecurity()

    def inspect_pdf(self, pdf_path: str) -> dict:
        """
        Inspect PDF without decrypting it.
        """
        return self.security.get_pdf_status(pdf_path)

    def is_encrypted(self, pdf_path: str) -> bool:
        """
        Return True when PDF is encrypted.
        """
        return self.security.is_encrypted(pdf_path)

    def encrypt(
        self,
        input_path: str,
        output_path: str,
        password: str,
        owner_password: Optional[str] = None,
    ):
        """
        Encrypt PDF.
        """
        return self.security.encrypt_pdf(
            input_path=input_path,
            output_path=output_path,
            user_password=password,
            owner_password=owner_password,
        )

    def decrypt(
        self,
        input_path: str,
        output_path: str,
        password: str,
    ):
        """
        Remove PDF encryption/password.
        """
        return self.security.decrypt_pdf(
            input_path=input_path,
            output_path=output_path,
            password=password,
        )

    def validate_password(
        self,
        pdf_path: str,
        password: str
    ) -> bool:
        """
        Validate PDF password.
        """
        return self.security.validate_password(
            pdf_path,
            password
        )


# Backward-compatible alias
PDFSecurityService = SecurityService