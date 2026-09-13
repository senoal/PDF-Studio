from __future__ import annotations

import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox


def ask_open_pdf(
    parent: tk.Misc,
    multiple: bool = True,
) -> tuple[str, ...] | str | None:
    """Open PDF file selection dialog."""

    filetypes = [
        ("PDF files", "*.pdf"),
        ("All files", "*.*"),
    ]

    if multiple:
        return filedialog.askopenfilenames(
            parent=parent,
            title="Select PDF files",
            filetypes=filetypes,
        )

    return filedialog.askopenfilename(
        parent=parent,
        title="Select PDF file",
        filetypes=filetypes,
    )


def ask_save_pdf(
    parent: tk.Misc,
    initial_name: str = "merged_document.pdf",
) -> str | None:
    """Open PDF save dialog."""

    return filedialog.asksaveasfilename(
        parent=parent,
        title="Save merged PDF",
        defaultextension=".pdf",
        initialfile=initial_name,
        filetypes=[
            ("PDF files", "*.pdf"),
            ("All files", "*.*"),
        ],
    )


def show_info(
    parent: tk.Misc,
    title: str,
    message: str,
) -> None:
    """Show information dialog."""
    messagebox.showinfo(
        title,
        message,
        parent=parent,
    )


def show_warning(
    parent: tk.Misc,
    title: str,
    message: str,
) -> None:
    """Show warning dialog."""
    messagebox.showwarning(
        title,
        message,
        parent=parent,
    )


def show_error(
    parent: tk.Misc,
    title: str,
    message: str,
) -> None:
    """Show error dialog."""
    messagebox.showerror(
        title,
        message,
        parent=parent,
    )


def ask_confirmation(
    parent: tk.Misc,
    title: str,
    message: str,
) -> bool:
    """Ask user for confirmation."""
    return messagebox.askyesno(
        title,
        message,
        parent=parent,
    )