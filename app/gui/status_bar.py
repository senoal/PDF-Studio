import tkinter as tk
from tkinter import ttk


class StatusBar(ttk.Frame):
    """Application status bar."""

    def __init__(self, parent) -> None:
        super().__init__(parent, style="Status.TFrame")

        self.columnconfigure(0, weight=1)

        self.status_label = ttk.Label(
            self,
            text="Ready",
            style="Status.TLabel",
            anchor="w",
        )

        self.status_label.grid(
            row=0,
            column=0,
            sticky="w",
            padx=18,
            pady=8,
        )

        self.version_label = ttk.Label(
            self,
            text="PDF Studio v1.0.0",
            style="Status.TLabel",
            anchor="e",
        )

        self.version_label.grid(
            row=0,
            column=1,
            sticky="e",
            padx=18,
            pady=8,
        )

    def set_message(self, message: str) -> None:
        """Update status message."""
        self.status_label.config(text=message)
