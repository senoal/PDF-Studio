from __future__ import annotations

import io
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageFont, ImageTk

from app.core.watermark import WatermarkConfig
from app.services.preview_service import PreviewService
from app.services.watermark_service import WatermarkService
from app.utils.background import run_in_background
from app.gui.theme import ACCENT, APP_BG, BORDER, INK, MUTED, NAVY, NAVY_HOVER, SURFACE


class WatermarkView(ttk.Frame):
    """
    Premium Watermark workspace.

    Layout:
        -------------------------------------------------
        | LEFT: Scrollable Controls | RIGHT: Preview    |
        -------------------------------------------------
        | Status / Actions                           |
        -------------------------------------------------
    """

    # =========================================================
    # DESIGN TOKENS
    # =========================================================

    BG = APP_BG
    CARD = SURFACE
    PREVIEW_BG = "#EEF1F0"

    TEXT = INK
    MUTED = MUTED

    PRIMARY = NAVY
    PRIMARY_HOVER = NAVY_HOVER

    BORDER = BORDER
    ACCENT = ACCENT

    SCROLLBAR = "#C8CDD5"

    def __init__(
        self,
        parent,
        status_callback=None,
    ):
        super().__init__(
            parent,
            style="WatermarkRoot.TFrame",
        )

        self.status_callback = status_callback

        self.pdf_path = None
        self.total_pages = 0

        self.watermark_image_path = None

        self.preview_photo = None
        self.preview_job = None

        self.watermark_service = WatermarkService()

        self.preview_service = PreviewService(
            dpi=90
        )

        self._configure_styles()
        self._build_ui()

        self._update_state()

    # =========================================================
    # STYLE
    # =========================================================

    def _configure_styles(self):

        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # -----------------------------------------------------
        # ROOT
        # -----------------------------------------------------

        style.configure(
            "WatermarkRoot.TFrame",
            background=self.BG,
        )

        # -----------------------------------------------------
        # CARD
        # -----------------------------------------------------

        style.configure(
            "WatermarkCard.TFrame",
            background=self.CARD,
        )

        # -----------------------------------------------------
        # LABELS
        # -----------------------------------------------------

        style.configure(
            "WatermarkSection.TLabel",
            background=self.CARD,
            foreground=self.TEXT,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        )

        style.configure(
            "WatermarkLabel.TLabel",
            background=self.CARD,
            foreground=self.TEXT,
            font=(
                "Segoe UI",
                9,
            ),
        )

        style.configure(
            "WatermarkMuted.TLabel",
            background=self.CARD,
            foreground=self.MUTED,
            font=(
                "Segoe UI",
                8,
            ),
        )

        style.configure(
            "WatermarkValue.TLabel",
            background=self.CARD,
            foreground=self.ACCENT,
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        )

        style.configure(
            "WatermarkSummary.TLabel",
            background=self.BG,
            foreground=self.MUTED,
            font=(
                "Segoe UI",
                9,
            ),
        )

        # -----------------------------------------------------
        # BUTTONS
        # -----------------------------------------------------

        style.configure(
            "WatermarkPrimary.TButton",
            background=self.PRIMARY,
            foreground="white",
            borderwidth=0,
            padding=(
                18,
                10,
            ),
            font=(
                "Segoe UI",
                9,
                "bold",
            ),
        )

        style.map(
            "WatermarkPrimary.TButton",
            background=[
                (
                    "active",
                    self.PRIMARY_HOVER,
                ),
                (
                    "pressed",
                    self.PRIMARY_HOVER,
                ),
                (
                    "disabled",
                    "#CBD0D8",
                ),
            ],
        )

        style.configure(
            "WatermarkSecondary.TButton",
            background="#EEF1F5",
            foreground=self.TEXT,
            borderwidth=0,
            padding=(
                14,
                9,
            ),
            font=(
                "Segoe UI",
                9,
            ),
        )

        style.map(
            "WatermarkSecondary.TButton",
            background=[
                (
                    "active",
                    "#E3E7ED",
                ),
            ],
        )

        # -----------------------------------------------------
        # RADIO
        # -----------------------------------------------------

        style.configure(
            "WatermarkRadio.TRadiobutton",
            background=self.CARD,
            foreground=self.TEXT,
            font=(
                "Segoe UI",
                9,
            ),
        )

        # -----------------------------------------------------
        # ENTRY
        # -----------------------------------------------------

        style.configure(
            "Watermark.TEntry",
            padding=8,
            font=(
                "Segoe UI",
                9,
            ),
        )

        # -----------------------------------------------------
        # COMBOBOX
        # -----------------------------------------------------

        style.configure(
            "Watermark.TCombobox",
            padding=7,
            font=(
                "Segoe UI",
                9,
            ),
        )

        # -----------------------------------------------------
        # SCROLLBAR
        # -----------------------------------------------------

        style.configure(
            "Watermark.Vertical.TScrollbar",
            troughcolor="#F0F2F5",
            background=self.SCROLLBAR,
            bordercolor="#F0F2F5",
            arrowcolor=self.MUTED,
        )

    # =========================================================
    # MAIN UI
    # =========================================================

    def _build_ui(self):

        self.columnconfigure(
            0,
            weight=1,
        )

        self.rowconfigure(
            0,
            weight=1,
        )

        self.rowconfigure(
            1,
            weight=0,
        )

        # =====================================================
        # WORKSPACE
        # =====================================================

        workspace = ttk.Frame(
            self,
            style="WatermarkRoot.TFrame",
        )

        workspace.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=32,
            pady=24,
        )

        workspace.columnconfigure(
            0,
            weight=0,
        )

        workspace.columnconfigure(
            1,
            weight=1,
        )

        workspace.rowconfigure(
            0,
            weight=1,
        )

        # =====================================================
        # LEFT SCROLLABLE PANEL
        # =====================================================

        self._build_scrollable_controls(
            workspace
        )

        # =====================================================
        # RIGHT PREVIEW
        # =====================================================

        self._build_preview_panel(
            workspace
        )

        # =====================================================
        # BOTTOM ACTION BAR
        # =====================================================

        self._build_action_bar()

    # =========================================================
    # LEFT SCROLLABLE CONTROLS
    # =========================================================

    def _build_scrollable_controls(
        self,
        parent,
    ):

        container = ttk.Frame(
            parent,
            style="WatermarkRoot.TFrame",
        )

        container.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 16),
        )

        container.rowconfigure(
            0,
            weight=1,
        )

        container.columnconfigure(
            0,
            weight=1,
        )

        # -----------------------------------------------------
        # Canvas
        # -----------------------------------------------------

        self.controls_canvas = tk.Canvas(
            container,
            background=self.CARD,
            highlightthickness=0,
            bd=0,
        )

        self.controls_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        # -----------------------------------------------------
        # Scrollbar
        # -----------------------------------------------------

        self.controls_scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self.controls_canvas.yview,
            style="Watermark.Vertical.TScrollbar",
        )

        self.controls_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.controls_canvas.configure(
            yscrollcommand=(
                self.controls_scrollbar.set
            )
        )

        # -----------------------------------------------------
        # Inner Card
        # -----------------------------------------------------

        self.left_card = ttk.Frame(
            self.controls_canvas,
            style="WatermarkCard.TFrame",
            padding=22,
        )

        self.left_card.columnconfigure(
            0,
            weight=1,
        )

        self.controls_window = (
            self.controls_canvas.create_window(
                0,
                0,
                window=self.left_card,
                anchor="nw",
            )
        )

        # -----------------------------------------------------
        # Events
        # -----------------------------------------------------

        self.left_card.bind(
            "<Configure>",
            self._on_controls_configure,
        )

        self.controls_canvas.bind(
            "<Configure>",
            self._on_canvas_configure,
        )

        self.controls_canvas.bind(
            "<Enter>",
            self._bind_mousewheel,
        )

        self.controls_canvas.bind(
            "<Leave>",
            self._unbind_mousewheel,
        )

        self.left_card.bind(
            "<Enter>",
            self._bind_mousewheel,
        )

        self.left_card.bind(
            "<Leave>",
            self._unbind_mousewheel,
        )

        # -----------------------------------------------------
        # Controls
        # -----------------------------------------------------

        self._build_source()
        self._build_watermark()
        self._build_appearance()
        self._build_target()

    # =========================================================
    # SCROLL EVENTS
    # =========================================================

    def _on_controls_configure(
        self,
        event=None,
    ):

        self.controls_canvas.configure(
            scrollregion=(
                self.controls_canvas.bbox(
                    "all"
                )
            )
        )

    def _on_canvas_configure(
        self,
        event,
    ):

        self.controls_canvas.itemconfigure(
            self.controls_window,
            width=event.width,
        )

        self.controls_canvas.configure(
            scrollregion=(
                self.controls_canvas.bbox(
                    "all"
                )
            )
        )

    def _bind_mousewheel(
        self,
        event=None,
    ):

        self.controls_canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel,
        )

    def _unbind_mousewheel(
        self,
        event=None,
    ):

        self.controls_canvas.unbind_all(
            "<MouseWheel>"
        )

    def _on_mousewheel(
        self,
        event,
    ):

        self.controls_canvas.yview_scroll(
            int(
                -1
                * (event.delta / 120)
            ),
            "units",
        )

    # =========================================================
    # SOURCE
    # =========================================================

    def _build_source(self):

        ttk.Label(
            self.left_card,
            text="SOURCE PDF",
            style="WatermarkSection.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            self.left_card,
            text="+  Open PDF",
            style="WatermarkPrimary.TButton",
            command=self.open_pdf,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(10, 6),
        )

        self.source_label = ttk.Label(
            self.left_card,
            text="No PDF selected",
            style="WatermarkMuted.TLabel",
            wraplength=260,
        )

        self.source_label.grid(
            row=2,
            column=0,
            sticky="w",
        )

        ttk.Separator(
            self.left_card,
        ).grid(
            row=3,
            column=0,
            sticky="ew",
            pady=(18, 20),
        )

    # =========================================================
    # WATERMARK
    # =========================================================

    def _build_watermark(self):

        ttk.Label(
            self.left_card,
            text="WATERMARK",
            style="WatermarkSection.TLabel",
        ).grid(
            row=4,
            column=0,
            sticky="w",
        )

        type_frame = ttk.Frame(
            self.left_card,
            style="WatermarkCard.TFrame",
        )

        type_frame.grid(
            row=5,
            column=0,
            sticky="w",
            pady=(10, 14),
        )

        self.watermark_type = tk.StringVar(
            value="text"
        )

        ttk.Radiobutton(
            type_frame,
            text="Text",
            variable=self.watermark_type,
            value="text",
            style="WatermarkRadio.TRadiobutton",
            command=self._on_type_changed,
        ).pack(
            side="left"
        )

        ttk.Radiobutton(
            type_frame,
            text="Image",
            variable=self.watermark_type,
            value="image",
            style="WatermarkRadio.TRadiobutton",
            command=self._on_type_changed,
        ).pack(
            side="left",
            padx=(28, 0),
        )

        # -----------------------------------------------------
        # Text Panel
        # -----------------------------------------------------

        self.text_panel = ttk.Frame(
            self.left_card,
            style="WatermarkCard.TFrame",
        )

        self.text_panel.grid(
            row=6,
            column=0,
            sticky="ew",
        )

        self.text_panel.columnconfigure(
            0,
            weight=1,
        )

        ttk.Label(
            self.text_panel,
            text="Watermark Text",
            style="WatermarkLabel.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.watermark_text = tk.StringVar(
            value="CONFIDENTIAL"
        )

        self.text_entry = ttk.Entry(
            self.text_panel,
            textvariable=self.watermark_text,
            style="Watermark.TEntry",
        )

        self.text_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(5, 0),
        )

        self.text_entry.bind(
            "<KeyRelease>",
            lambda event:
            self._schedule_preview(),
        )

        # -----------------------------------------------------
        # Image Panel
        # -----------------------------------------------------

        self.image_panel = ttk.Frame(
            self.left_card,
            style="WatermarkCard.TFrame",
        )

        self.image_panel.columnconfigure(
            0,
            weight=1,
        )

        ttk.Label(
            self.image_panel,
            text="Watermark Image",
            style="WatermarkLabel.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            self.image_panel,
            text="Upload Image",
            style="WatermarkSecondary.TButton",
            command=self.choose_image,
        ).grid(
            row=1,
            column=0,
            sticky="w",
            pady=(6, 5),
        )

        self.image_label = ttk.Label(
            self.image_panel,
            text="PNG, JPG, JPEG or WEBP",
            style="WatermarkMuted.TLabel",
            wraplength=260,
        )

        self.image_label.grid(
            row=2,
            column=0,
            sticky="w",
        )

        ttk.Separator(
            self.left_card,
        ).grid(
            row=7,
            column=0,
            sticky="ew",
            pady=(20, 18),
        )

    # =========================================================
    # APPEARANCE
    # =========================================================

    def _build_appearance(self):

        ttk.Label(
            self.left_card,
            text="APPEARANCE",
            style="WatermarkSection.TLabel",
        ).grid(
            row=8,
            column=0,
            sticky="w",
        )

        self.opacity = tk.DoubleVar(
            value=30
        )

        self._add_slider(
            row=9,
            label="Opacity",
            variable=self.opacity,
            minimum=5,
            maximum=100,
            formatter=lambda value:
            f"{int(float(value))}%",
        )

        self.rotation = tk.DoubleVar(
            value=-45
        )

        self._add_slider(
            row=11,
            label="Rotation",
            variable=self.rotation,
            minimum=-180,
            maximum=180,
            formatter=lambda value:
            f"{int(float(value))}°",
        )

        self.scale = tk.DoubleVar(
            value=1.0
        )

        self._add_slider(
            row=13,
            label="Scale",
            variable=self.scale,
            minimum=0.25,
            maximum=3.0,
            formatter=lambda value:
            f"{float(value):.2f}×",
        )

        # -----------------------------------------------------
        # Position
        # -----------------------------------------------------

        ttk.Label(
            self.left_card,
            text="Position",
            style="WatermarkLabel.TLabel",
        ).grid(
            row=15,
            column=0,
            sticky="w",
            pady=(12, 5),
        )

        self.position = tk.StringVar(
            value="center"
        )

        self.position_combo = ttk.Combobox(
            self.left_card,
            textvariable=self.position,
            state="readonly",
            values=[
                "Top Left",
                "Top Center",
                "Top Right",
                "Center Left",
                "Center",
                "Center Right",
                "Bottom Left",
                "Bottom Center",
                "Bottom Right",
            ],
            style="Watermark.TCombobox",
        )

        self.position_combo.grid(
            row=16,
            column=0,
            sticky="ew",
        )

        self.position_combo.set(
            "Center"
        )

        self.position_combo.bind(
            "<<ComboboxSelected>>",
            lambda event:
            self._schedule_preview(),
        )

    def _add_slider(
        self,
        row,
        label,
        variable,
        minimum,
        maximum,
        formatter,
    ):

        ttk.Label(
            self.left_card,
            text=label,
            style="WatermarkLabel.TLabel",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(8, 4),
        )

        frame = ttk.Frame(
            self.left_card,
            style="WatermarkCard.TFrame",
        )

        frame.grid(
            row=row + 1,
            column=0,
            sticky="ew",
        )

        frame.columnconfigure(
            0,
            weight=1,
        )

        value_label = ttk.Label(
            frame,
            text=formatter(
                variable.get()
            ),
            style="WatermarkValue.TLabel",
            width=8,
            anchor="e",
        )

        value_label.grid(
            row=0,
            column=1,
            padx=(10, 0),
        )

        def changed(value):

            value_label.config(
                text=formatter(value)
            )

            self._schedule_preview()

        ttk.Scale(
            frame,
            from_=minimum,
            to=maximum,
            variable=variable,
            command=changed,
        ).grid(
            row=0,
            column=0,
            sticky="ew",
        )

    # =========================================================
    # APPLY TO
    # =========================================================

    def _build_target(self):

        ttk.Separator(
            self.left_card,
        ).grid(
            row=17,
            column=0,
            sticky="ew",
            pady=(20, 18),
        )

        ttk.Label(
            self.left_card,
            text="APPLY TO",
            style="WatermarkSection.TLabel",
        ).grid(
            row=18,
            column=0,
            sticky="w",
        )

        self.apply_mode = tk.StringVar(
            value="all"
        )

        ttk.Radiobutton(
            self.left_card,
            text="All pages",
            variable=self.apply_mode,
            value="all",
            style="WatermarkRadio.TRadiobutton",
            command=self._on_apply_mode_changed,
        ).grid(
            row=19,
            column=0,
            sticky="w",
            pady=(9, 4),
        )

        ttk.Radiobutton(
            self.left_card,
            text="Selected pages",
            variable=self.apply_mode,
            value="selected",
            style="WatermarkRadio.TRadiobutton",
            command=self._on_apply_mode_changed,
        ).grid(
            row=20,
            column=0,
            sticky="w",
        )

        # -----------------------------------------------------
        # Selected Pages
        # -----------------------------------------------------

        self.page_range_frame = ttk.Frame(
            self.left_card,
            style="WatermarkCard.TFrame",
        )

        self.page_range_frame.grid(
            row=21,
            column=0,
            sticky="ew",
            pady=(8, 0),
        )

        self.page_range_frame.columnconfigure(
            0,
            weight=1,
        )

        ttk.Label(
            self.page_range_frame,
            text="Page numbers",
            style="WatermarkMuted.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.page_range = tk.StringVar()

        self.page_range_entry = ttk.Entry(
            self.page_range_frame,
            textvariable=self.page_range,
            style="Watermark.TEntry",
        )

        self.page_range_entry.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(4, 3),
        )

        ttk.Label(
            self.page_range_frame,
            text="Example: 1, 3, 5-8",
            style="WatermarkMuted.TLabel",
        ).grid(
            row=2,
            column=0,
            sticky="w",
        )

        self.page_range_frame.grid_remove()

        # -----------------------------------------------------
        # Bottom information
        # -----------------------------------------------------

        self.target_info = ttk.Label(
            self.left_card,
            text="All pages will be watermarked.",
            style="WatermarkMuted.TLabel",
            wraplength=260,
        )

        self.target_info.grid(
            row=22,
            column=0,
            sticky="w",
            pady=(12, 0),
        )

        # Extra breathing room
        ttk.Frame(
            self.left_card,
            height=18,
            style="WatermarkCard.TFrame",
        ).grid(
            row=23,
            column=0,
            sticky="ew",
        )

    # =========================================================
    # RIGHT PREVIEW
    # =========================================================

    def _build_preview_panel(
        self,
        parent,
    ):

        right = ttk.Frame(
            parent,
            style="WatermarkCard.TFrame",
            padding=20,
        )

        right.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        right.columnconfigure(
            0,
            weight=1,
        )

        right.rowconfigure(
            1,
            weight=1,
        )

        ttk.Label(
            right,
            text="LIVE PREVIEW",
            style="WatermarkSection.TLabel",
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 12),
        )

        preview_frame = tk.Frame(
            right,
            bg=self.PREVIEW_BG,
        )

        preview_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        preview_frame.bind(
            "<Configure>",
            lambda event:
            self._schedule_preview(),
        )

        self.preview_canvas = tk.Canvas(
            preview_frame,
            bg=self.PREVIEW_BG,
            highlightthickness=0,
            bd=0,
        )

        self.preview_canvas.pack(
            fill="both",
            expand=True,
        )

        self.preview_placeholder = tk.Label(
            preview_frame,
            text=(
                "No PDF loaded\n\n"
                "Open a PDF to preview\n"
                "your watermark."
            ),
            bg=self.PREVIEW_BG,
            fg=self.MUTED,
            font=(
                "Segoe UI",
                10,
            ),
            justify="center",
        )

        self.preview_placeholder.place(
            relx=0.5,
            rely=0.5,
            anchor="center",
        )

    # =========================================================
    # ACTION BAR
    # =========================================================

    def _build_action_bar(self):

        bottom = ttk.Frame(
            self,
            style="WatermarkRoot.TFrame",
        )

        bottom.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=32,
            pady=(
                0,
                22,
            ),
        )

        bottom.columnconfigure(
            0,
            weight=1,
        )

        self.summary_label = ttk.Label(
            bottom,
            text="No PDF loaded",
            style="WatermarkSummary.TLabel",
        )

        self.summary_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Button(
            bottom,
            text="Reset",
            style="WatermarkSecondary.TButton",
            command=self.reset,
        ).grid(
            row=0,
            column=1,
            padx=(10, 8),
        )

        self.save_button = ttk.Button(
            bottom,
            text="Apply & Save  →",
            style="WatermarkPrimary.TButton",
            command=self.apply_watermark,
        )

        self.save_button.grid(
            row=0,
            column=2,
        )

    # =========================================================
    # OPEN PDF
    # =========================================================

    def open_pdf(self):

        path = filedialog.askopenfilename(
            parent=self,
            title="Open PDF",
            filetypes=[
                (
                    "PDF Files",
                    "*.pdf",
                )
            ],
        )

        if not path:
            return

        self._load_pdf(
            path
        )

    def _load_pdf(
        self,
        path,
    ):

        try:

            self._set_status(
                "Loading PDF..."
            )

            self.total_pages = (
                self.preview_service.get_page_count(
                    path
                )
            )

            if self.total_pages <= 0:

                raise ValueError(
                    "The PDF contains no pages."
                )

            self.pdf_path = path

            self.source_label.config(
                text=Path(
                    path
                ).name,
                foreground=self.TEXT,
            )

            # StringVar -> set()
            self.page_range.set("")

            self._update_target_info()
            self._update_state()

            self._render_preview()

            self._set_status(
                (
                    f"Loaded PDF successfully "
                    f"({self.total_pages} pages)."
                )
            )

        except Exception as exc:

            messagebox.showerror(
                "Unable to Open PDF",
                str(exc),
                parent=self,
            )

            self._set_status(
                "Unable to open PDF."
            )

    # =========================================================
    # IMAGE
    # =========================================================

    def choose_image(self):

        path = filedialog.askopenfilename(
            parent=self,
            title="Select Watermark Image",
            filetypes=[
                (
                    "Image Files",
                    "*.png *.jpg *.jpeg *.webp",
                ),
                (
                    "PNG",
                    "*.png",
                ),
                (
                    "JPEG",
                    "*.jpg *.jpeg",
                ),
                (
                    "WEBP",
                    "*.webp",
                ),
            ],
        )

        if not path:
            return

        try:

            with Image.open(path) as image:

                image.verify()

        except Exception:

            messagebox.showerror(
                "Invalid Image",
                (
                    "The selected file is not "
                    "a valid image."
                ),
                parent=self,
            )

            return

        self.watermark_image_path = path

        self.image_label.config(
            text=Path(
                path
            ).name,
            foreground=self.TEXT,
        )

        self._render_preview()

        self._set_status(
            "Watermark image selected."
        )

    # =========================================================
    # WATERMARK TYPE
    # =========================================================

    def _on_type_changed(self):

        if (
            self.watermark_type.get()
            == "text"
        ):

            self.image_panel.grid_remove()

            self.text_panel.grid(
                row=6,
                column=0,
                sticky="ew",
            )

        else:

            self.text_panel.grid_remove()

            self.image_panel.grid(
                row=6,
                column=0,
                sticky="ew",
            )

        self._schedule_preview()

        self._on_controls_configure()

    # =========================================================
    # APPLY MODE
    # =========================================================

    def _on_apply_mode_changed(self):

        if (
            self.apply_mode.get()
            == "selected"
        ):

            self.page_range_frame.grid()

        else:

            self.page_range_frame.grid_remove()

        self._update_target_info()

        self._update_state()

        self._on_controls_configure()

    # =========================================================
    # TARGET INFORMATION
    # =========================================================

    def _update_target_info(self):

        if (
            self.apply_mode.get()
            == "all"
        ):

            if self.total_pages:

                self.target_info.config(
                    text=(
                        f"Watermark will be applied "
                        f"to all {self.total_pages} pages."
                    )
                )

            else:

                self.target_info.config(
                    text=(
                        "Watermark will be applied "
                        "to all pages."
                    )
                )

        else:

            self.target_info.config(
                text=(
                    "Enter the page numbers to "
                    "receive the watermark."
                )
            )

    # =========================================================
    # CONFIG
    # =========================================================

    def _get_config(self):

        return WatermarkConfig(

            watermark_type=(
                self.watermark_type.get()
            ),

            text=(
                self.watermark_text.get()
            ),

            image_path=(
                self.watermark_image_path
            ),

            font_size=48,

            opacity=(
                float(
                    self.opacity.get()
                )
                / 100.0
            ),

            rotation=(
                float(
                    self.rotation.get()
                )
            ),

            scale=(
                float(
                    self.scale.get()
                )
            ),

            position=(
                self._normalize_position(
                    self.position.get()
                )
            ),
        )

    # =========================================================
    # PAGE RANGE
    # =========================================================

    def _parse_page_range(self):

        value = (
            self.page_range
            .get()
            .strip()
        )

        if not value:

            raise ValueError(
                "Please enter page numbers."
            )

        pages = set()

        for part in value.split(","):

            part = part.strip()

            if not part:
                continue

            if "-" in part:

                pieces = part.split("-")

                if len(pieces) != 2:

                    raise ValueError(
                        f"Invalid page range: {part}"
                    )

                start = int(
                    pieces[0].strip()
                )

                end = int(
                    pieces[1].strip()
                )

                if start > end:

                    raise ValueError(
                        f"Invalid page range: {part}"
                    )

                for page in range(
                    start,
                    end + 1,
                ):

                    pages.add(page)

            else:

                pages.add(
                    int(part)
                )

        if not pages:

            raise ValueError(
                "No pages selected."
            )

        for page in pages:

            if (
                page < 1
                or page > self.total_pages
            ):

                raise ValueError(
                    (
                        f"Page {page} does not exist. "
                        f"PDF has {self.total_pages} pages."
                    )
                )

        return sorted(
            page - 1
            for page in pages
        )

    # =========================================================
    # APPLY WATERMARK
    # =========================================================

    def apply_watermark(self):

        if not self.pdf_path:

            messagebox.showwarning(
                "No PDF Loaded",
                "Please open a PDF first.",
                parent=self,
            )

            return

        try:

            config = self._get_config()

            config.validate()

        except Exception as exc:

            messagebox.showerror(
                "Invalid Watermark",
                str(exc),
                parent=self,
            )

            return

        page_indexes = None

        if (
            self.apply_mode.get()
            == "selected"
        ):

            try:

                page_indexes = (
                    self._parse_page_range()
                )

            except Exception as exc:

                messagebox.showerror(
                    "Invalid Page Selection",
                    str(exc),
                    parent=self,
                )

                return

        output_file = (
            filedialog.asksaveasfilename(
                parent=self,
                title="Save Watermarked PDF",
                defaultextension=".pdf",
                filetypes=[
                    (
                        "PDF Files",
                        "*.pdf",
                    )
                ],
                initialfile=(
                    "watermarked_document.pdf"
                ),
            )
        )

        if not output_file:
            return

        if not output_file.lower().endswith(
            ".pdf"
        ):

            output_file += ".pdf"

        try:

            source = Path(
                self.pdf_path
            ).resolve()

            destination = Path(
                output_file
            ).resolve()

            if source == destination:

                messagebox.showerror(
                    "Invalid Output",
                    (
                        "The output file cannot "
                        "be the same as the source PDF."
                    ),
                    parent=self,
                )

                return

        except Exception:
            pass

        self.save_button.config(
            state="disabled"
        )

        self._set_status(
            "Applying watermark..."
        )

        input_file = self.pdf_path

        def completed(result) -> None:
            success, message = result
            if not success:
                messagebox.showerror("Watermark Failed", message, parent=self)
                self._set_status("Watermark operation failed.")
                return
            messagebox.showinfo(
                "Watermark Complete",
                "Watermark applied successfully.\n\n" f"Saved to:\n{output_file}",
                parent=self,
            )
            self._set_status("Watermark applied successfully.")
            self._load_pdf(output_file)

        def failed(exc: Exception) -> None:
            messagebox.showerror("Watermark Failed", str(exc), parent=self)
            self._set_status("Watermark operation failed.")

        run_in_background(
            self,
            lambda: self.watermark_service.apply_watermark(
                input_file=input_file,
                output_file=output_file,
                config=config,
                page_indexes=page_indexes,
            ),
            completed,
            failed,
            lambda: self.save_button.config(state="normal"),
        )

    # =========================================================
    # PREVIEW SCHEDULER
    # =========================================================

    def _schedule_preview(self):

        if self.preview_job:

            try:

                self.after_cancel(
                    self.preview_job
                )

            except tk.TclError:
                pass

        self.preview_job = self.after(
            150,
            self._render_preview,
        )

    # =========================================================
    # PREVIEW
    # =========================================================

    def _render_preview(self):

        self.preview_job = None

        if not self.pdf_path:
            return

        try:

            preview = (
                self.preview_service.render_page(
                    self.pdf_path,
                    0,
                )
            )

            image = Image.open(
                io.BytesIO(
                    preview.image_data
                )
            ).convert(
                "RGBA"
            )

            image = (
                self._apply_preview_watermark(
                    image
                )
            )

            width = (
                self.preview_canvas.winfo_width()
            )

            height = (
                self.preview_canvas.winfo_height()
            )

            if width <= 10 or height <= 10:
                return

            image.thumbnail(
                (
                    max(
                        300,
                        width - 60,
                    ),
                    max(
                        400,
                        height - 60,
                    ),
                ),
                Image.Resampling.LANCZOS,
            )

            self.preview_photo = (
                ImageTk.PhotoImage(
                    image
                )
            )

            self.preview_canvas.delete(
                "all"
            )

            self.preview_canvas.create_image(
                width / 2,
                height / 2,
                image=self.preview_photo,
                anchor="center",
            )

            self.preview_placeholder.place_forget()

        except Exception as exc:

            self.preview_canvas.delete(
                "all"
            )

            self.preview_placeholder.config(
                text=(
                    "Preview unavailable\n\n"
                    f"{exc}"
                )
            )

            self.preview_placeholder.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
            )

    # =========================================================
    # PREVIEW WATERMARK
    # =========================================================

    def _apply_preview_watermark(
        self,
        image,
    ):

        config = self._get_config()

        overlay = Image.new(
            "RGBA",
            image.size,
            (0, 0, 0, 0),
        )

        if (
            config.watermark_type
            == "text"
        ):

            self._preview_text(
                overlay,
                config,
            )

        elif (
            config.watermark_type
            == "image"
            and config.image_path
        ):

            self._preview_image(
                overlay,
                config,
            )

        return Image.alpha_composite(
            image,
            overlay,
        )

    # =========================================================
    # TEXT PREVIEW
    # =========================================================

    def _preview_text(
        self,
        overlay,
        config,
    ):

        text = config.text.strip()

        if not text:
            return

        draw = ImageDraw.Draw(
            overlay
        )

        font = self._load_font(
            max(
                18,
                int(
                    46
                    * config.scale
                ),
            )
        )

        bbox = draw.textbbox(
            (0, 0),
            text,
            font=font,
        )

        width = (
            bbox[2]
            - bbox[0]
        )

        height = (
            bbox[3]
            - bbox[1]
        )

        layer = Image.new(
            "RGBA",
            (
                width + 50,
                height + 50,
            ),
            (0, 0, 0, 0),
        )

        layer_draw = ImageDraw.Draw(
            layer
        )

        layer_draw.text(
            (
                25,
                25,
            ),
            text,
            font=font,
            fill=(
                80,
                80,
                80,
                int(
                    255
                    * config.opacity
                ),
            ),
        )

        layer = layer.rotate(
            config.rotation,
            expand=True,
            resample=Image.Resampling.BICUBIC,
        )

        x, y = self._preview_position(
            overlay.size,
            layer.size,
            config.position,
        )

        overlay.alpha_composite(
            layer,
            (
                x,
                y,
            ),
        )

    # =========================================================
    # IMAGE PREVIEW
    # =========================================================

    def _preview_image(
        self,
        overlay,
        config,
    ):

        try:

            image = Image.open(
                config.image_path
            ).convert(
                "RGBA"
            )

            alpha = image.getchannel(
                "A"
            )

            alpha = alpha.point(
                lambda value:
                int(
                    value
                    * config.opacity
                )
            )

            image.putalpha(
                alpha
            )

            target_width = int(
                overlay.width
                * 0.30
                * config.scale
            )

            target_width = max(
                40,
                min(
                    target_width,
                    int(
                        overlay.width
                        * 0.70
                    ),
                ),
            )

            ratio = (
                target_width
                / image.width
            )

            target_height = int(
                image.height
                * ratio
            )

            image = image.resize(
                (
                    target_width,
                    target_height,
                ),
                Image.Resampling.LANCZOS,
            )

            image = image.rotate(
                config.rotation,
                expand=True,
                resample=Image.Resampling.BICUBIC,
            )

            x, y = self._preview_position(
                overlay.size,
                image.size,
                config.position,
            )

            overlay.alpha_composite(
                image,
                (
                    x,
                    y,
                ),
            )

        except Exception:
            pass

    # =========================================================
    # PREVIEW POSITION
    # =========================================================

    def _preview_position(
        self,
        canvas_size,
        object_size,
        position,
    ):

        width, height = canvas_size

        object_width, object_height = (
            object_size
        )

        positions = {

            "top-left": (
                0.18,
                0.15,
            ),

            "top-center": (
                0.50,
                0.15,
            ),

            "top-right": (
                0.82,
                0.15,
            ),

            "center-left": (
                0.18,
                0.50,
            ),

            "center": (
                0.50,
                0.50,
            ),

            "center-right": (
                0.82,
                0.50,
            ),

            "bottom-left": (
                0.18,
                0.85,
            ),

            "bottom-center": (
                0.50,
                0.85,
            ),

            "bottom-right": (
                0.82,
                0.85,
            ),
        }

        px, py = positions.get(
            position,
            positions["center"],
        )

        return (
            int(
                width * px
                - object_width / 2
            ),
            int(
                height * py
                - object_height / 2
            ),
        )

    # =========================================================
    # FONT
    # =========================================================

    def _load_font(
        self,
        size,
    ):

        fonts = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/calibrib.ttf",
        ]

        for path in fonts:

            try:

                return ImageFont.truetype(
                    path,
                    size,
                )

            except Exception:
                continue

        return ImageFont.load_default()

    # =========================================================
    # RESET
    # =========================================================

    def reset(self):

        self.watermark_type.set(
            "text"
        )

        self.watermark_text.set(
            "CONFIDENTIAL"
        )

        self.watermark_image_path = None

        self.image_label.config(
            text="PNG, JPG, JPEG or WEBP",
            foreground=self.MUTED,
        )

        self.opacity.set(
            30
        )

        self.rotation.set(
            -45
        )

        self.scale.set(
            1.0
        )

        self.position.set(
            "center"
        )

        self.position_combo.set(
            "Center"
        )

        self.apply_mode.set(
            "all"
        )

        self.page_range.set(
            ""
        )

        self.text_panel.grid(
            row=6,
            column=0,
            sticky="ew",
        )

        self.image_panel.grid_remove()

        self.page_range_frame.grid_remove()

        self._update_target_info()
        self._update_state()

        self._schedule_preview()

        self._on_controls_configure()

        self._set_status(
            "Watermark settings reset."
        )

    # =========================================================
    # STATE
    # =========================================================

    def _update_state(self):

        if (
            self.pdf_path
            and self.total_pages > 0
        ):

            self.save_button.config(
                state="normal"
            )

            if (
                self.apply_mode.get()
                == "all"
            ):

                target = (
                    f"All {self.total_pages} pages"
                )

            else:

                target = "Selected pages"

            self.summary_label.config(
                text=(
                    f"{self.total_pages} pages"
                    f"  •  Target: {target}"
                )
            )

        else:

            self.save_button.config(
                state="disabled"
            )

            self.summary_label.config(
                text="No PDF loaded"
            )

    # =========================================================
    # STATUS
    # =========================================================

    def _set_status(
        self,
        message,
    ):

        if self.status_callback:

            try:

                self.status_callback(
                    message
                )

            except Exception:
                pass

    # =========================================================
    # POSITION NORMALIZATION
    # =========================================================

    def _normalize_position(
        self,
        value,
    ):

        return (
            value
            .strip()
            .lower()
            .replace(
                " ",
                "-",
            )
        )
