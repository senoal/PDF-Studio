#!/usr/bin/env python3
"""
PDF Decryptor - remove PDF encryption/security settings when the
document can be opened with an empty password or a password supplied
by the user.

Tested approach: pypdf.
The program does NOT crack or bypass an unknown password.

Usage:
    python pdf_decryptor.py

It opens a file picker, lets you select a PDF, and creates:
    original_name_decrypted.pdf

Dependency:
    pip install -U pypdf cryptography
"""

from pathlib import Path
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    print("Module pypdf belum terinstall.")
    print("Install dengan:")
    print("    python -m pip install -U pypdf cryptography")
    sys.exit(1)


def decrypt_pdf(input_path: Path, password: str = "") -> Path:
    """Decrypt a PDF and write a new PDF without encryption."""
    output_path = input_path.with_name(
        f"{input_path.stem}_decrypted{input_path.suffix}"
    )

    reader = PdfReader(str(input_path), strict=False)

    if reader.is_encrypted:
        result = reader.decrypt(password)

        if not result:
            raise ValueError(
                "Password salah atau PDF tidak dapat didekripsi dengan "
                "password yang diberikan."
            )

    writer = PdfWriter()

    # Copy every page into a new PDF. The new writer is not encrypted.
    for page in reader.pages:
        writer.add_page(page)

    # Preserve common document metadata where available.
    if reader.metadata:
        metadata = {}
        for key, value in reader.metadata.items():
            if key and value is not None:
                metadata[str(key)] = str(value)
        if metadata:
            writer.add_metadata(metadata)

    with output_path.open("wb") as output_file:
        writer.write(output_file)

    return output_path


def main():
    root = tk.Tk()
    root.withdraw()

    input_file = filedialog.askopenfilename(
        title="Pilih PDF yang akan didekripsi",
        filetypes=[
            ("PDF files", "*.pdf"),
            ("All files", "*.*"),
        ],
    )

    if not input_file:
        print("Tidak ada file yang dipilih.")
        return

    input_path = Path(input_file)

    try:
        # First try an empty password. This handles PDFs that open
        # normally but are still technically encrypted.
        reader = PdfReader(str(input_path), strict=False)

        if reader.is_encrypted:
            result = reader.decrypt("")

            if result:
                password = ""
                print("PDF terenkripsi, tetapi dapat dibuka dengan empty password.")
            else:
                # If empty password fails, ask the user for the legitimate
                # password. This does not attempt password cracking.
                password = simpledialog.askstring(
                    "Password PDF",
                    "PDF meminta password.\n"
                    "Masukkan password yang sah:",
                    show="*",
                    parent=root,
                )

                if password is None:
                    print("Proses dibatalkan.")
                    return
        else:
            password = ""
            print("PDF tidak terenkripsi. Membuat salinan tanpa security settings.")

        output_path = decrypt_pdf(input_path, password)

        message = (
            "Berhasil!\n\n"
            f"Input : {input_path}\n"
            f"Output: {output_path}\n\n"
            "File output dibuat sebagai PDF baru tanpa encryption "
            "dari PdfWriter."
        )

        print(message)
        messagebox.showinfo("Selesai", message, parent=root)

    except Exception as exc:
        error_message = (
            "Gagal memproses PDF.\n\n"
            f"{type(exc).__name__}: {exc}\n\n"
            "Jika PDF memiliki password yang tidak diketahui, "
            "program ini tidak melakukan password cracking."
        )
        print(error_message, file=sys.stderr)
        messagebox.showerror("Gagal", error_message, parent=root)

    finally:
        root.destroy()


if __name__ == "__main__":
    main()
