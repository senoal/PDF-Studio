import tkinter as tk
from tkinter import ttk

from app.gui.theme import SIDEBAR


class Sidebar(ttk.Frame):
    """Premium application sidebar."""

    FEATURES = [
        ("Merge PDF", "merge", "Ctrl+M"),
        ("Delete Pages", "delete_pages", "Ctrl+D"),
        ("Watermark", "watermark", ""),
        ("Header & Footer", "header_footer", ""),
        ("Encrypt / Decrypt", "security", ""),
        ("Edit PDF", "editor", "Ctrl+E"),
    ]

    def __init__(self, parent, on_select) -> None:
        super().__init__(
            parent,
            style="Sidebar.TFrame",
            width=235,
        )

        self.on_select = on_select
        self.buttons = {}
        self.active_feature = None

        self.pack_propagate(False)

        self._build()

    def _build(self) -> None:
        # ----------------------------------------------------
        # Brand
        # ----------------------------------------------------

        brand_frame = ttk.Frame(
            self,
            style="Sidebar.TFrame",
        )

        brand_frame.pack(
            fill="x",
            padx=20,
            pady=(24, 30),
        )

        logo = tk.Canvas(
            brand_frame,
            width=38,
            height=38,
            bg=SIDEBAR,
            highlightthickness=0,
        )

        logo.create_rectangle(
            5,
            5,
            33,
            33,
            outline="#ffffff",
            width=2,
        )

        logo.create_line(
            12,
            14,
            26,
            14,
            fill="#ffffff",
            width=2,
        )

        logo.create_line(
            12,
            20,
            26,
            20,
            fill="#ffffff",
            width=2,
        )

        logo.create_line(
            12,
            26,
            22,
            26,
            fill="#ffffff",
            width=2,
        )

        logo.pack(side="left")

        brand_text = ttk.Frame(
            brand_frame,
            style="Sidebar.TFrame",
        )

        brand_text.pack(
            side="left",
            padx=(12, 0),
        )

        ttk.Label(
            brand_text,
            text="PDF Studio",
            style="Brand.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            brand_text,
            text="Professional PDF Utility",
            style="BrandSub.TLabel",
        ).pack(anchor="w")

        # ----------------------------------------------------
        # Navigation Label
        # ----------------------------------------------------

        ttk.Label(
            self,
            text="TOOLS",
            style="Section.TLabel",
        ).pack(
            anchor="w",
            padx=22,
            pady=(0, 8),
        )

        # ----------------------------------------------------
        # Navigation Buttons
        # ----------------------------------------------------

        for label, feature, shortcut in self.FEATURES:
            self._create_navigation_button(
                label,
                feature,
                shortcut,
            )

        # ----------------------------------------------------
        # Bottom Information
        # ----------------------------------------------------

        bottom = ttk.Frame(
            self,
            style="Sidebar.TFrame",
        )

        bottom.pack(
            side="bottom",
            fill="x",
            padx=20,
            pady=20,
        )

        separator = ttk.Separator(
            bottom,
            orient="horizontal",
        )

        separator.pack(
            fill="x",
            pady=(0, 14),
        )

        ttk.Label(
            bottom,
            text="Offline & Private",
            style="Privacy.TLabel",
        ).pack(anchor="w")

        ttk.Label(
            bottom,
            text="Your PDF files stay on this device.",
            style="PrivacySub.TLabel",
            wraplength=190,
        ).pack(
            anchor="w",
            pady=(3, 0),
        )

    def _create_navigation_button(
        self,
        label: str,
        feature: str,
        shortcut: str,
    ) -> None:

        button = ttk.Button(
            self,
            text=label,
            style="Navigation.TButton",
            command=lambda: self._select(feature),
        )

        button.pack(
            fill="x",
            padx=12,
            pady=2,
            ipady=7,
        )

        self.buttons[feature] = button

    def _select(self, feature: str) -> None:
        self.set_active(feature)
        self.on_select(feature)

    def set_active(self, feature: str) -> None:
        """Set active navigation item."""
        self.active_feature = feature

        for name, button in self.buttons.items():
            if name == feature:
                button.configure(
                    style="NavigationActive.TButton"
                )
            else:
                button.configure(
                    style="Navigation.TButton"
                )
