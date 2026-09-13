from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import fitz
from PIL import Image, ImageTk

from app.core.header_footer import HeaderFooterProcessor
from app.gui.theme import ACCENT, APP_BG, BORDER, INK, MUTED, NAVY, SURFACE


class HeaderFooterView(tk.Frame):
    """
    Header & Footer editor.

    The page title is intentionally NOT rendered here because
    MainWindow already provides the application/page title.

    Compatible with:
        HeaderFooterView(parent)
        HeaderFooterView(parent, status_callback=...)
    """

    BG = APP_BG
    CARD = SURFACE
    NAVY = NAVY
    TEXT = INK
    MUTED = MUTED
    BORDER = BORDER
    PREVIEW_BG = "#EEF1F0"
    BLUE = ACCENT

    def __init__(
        self,
        parent,
        status_callback=None,
        **kwargs,
    ):
        super().__init__(
            parent,
            bg=self.BG,
            **kwargs,
        )

        self.status_callback = status_callback

        self.pdf_path = None
        self.pdf_document = None

        self.header_image_path = None
        self.footer_image_path = None

        self.preview_photo = None
        self._preview_images = []

        self.header_enabled = tk.BooleanVar(
            value=False
        )

        self.footer_enabled = tk.BooleanVar(
            value=False
        )

        self.header_type = tk.StringVar(
            value="text"
        )

        self.footer_type = tk.StringVar(
            value="text"
        )

        self.header_alignment = tk.StringVar(
            value="center"
        )

        self.footer_alignment = tk.StringVar(
            value="center"
        )

        self.header_margin = tk.DoubleVar(
            value=24
        )

        self.header_height = tk.DoubleVar(
            value=72
        )

        self.footer_margin = tk.DoubleVar(
            value=24
        )

        self.footer_height = tk.DoubleVar(
            value=48
        )

        self.header_text = tk.StringVar(
            value="CONFIDENTIAL"
        )

        self.footer_text = tk.StringVar(
            value="Page {page} of {pages}"
        )

        self.page_number_enabled = tk.BooleanVar(
            value=False
        )

        self._build_ui()

    # ==================================================================
    # UI
    # ==================================================================

    def _build_ui(self):
        """
        Build the feature UI.

        NOTE:
        No internal page title is created here.
        MainWindow owns the page title.
        """

        self.grid_rowconfigure(
            0,
            weight=1,
        )

        self.grid_columnconfigure(
            0,
            weight=1,
        )

        body = tk.Frame(
            self,
            bg=self.BG,
        )

        body.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=28,
            pady=(0, 20),
        )

        body.grid_columnconfigure(
            0,
            weight=0,
        )

        body.grid_columnconfigure(
            1,
            weight=1,
        )

        body.grid_rowconfigure(
            0,
            weight=1,
        )

        self._build_settings_panel(body)
        self._build_preview_panel(body)

        self._refresh_controls()
        self._update_preview()

    # ==================================================================
    # SETTINGS PANEL
    # ==================================================================

    def _build_settings_panel(self, parent):
        outer = tk.Frame(
            parent,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )

        outer.grid(
            row=0,
            column=0,
            sticky="ns",
            padx=(0, 14),
        )

        outer.grid_rowconfigure(
            0,
            weight=1,
        )

        outer.grid_columnconfigure(
            0,
            weight=1,
        )

        canvas = tk.Canvas(
            outer,
            bg=self.CARD,
            highlightthickness=0,
            width=395,
        )

        scrollbar = ttk.Scrollbar(
            outer,
            orient="vertical",
            command=canvas.yview,
        )

        canvas.configure(
            yscrollcommand=scrollbar.set
        )

        canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.settings_canvas = canvas

        self.settings_frame = tk.Frame(
            canvas,
            bg=self.CARD,
        )

        self.settings_window = canvas.create_window(
            (0, 0),
            window=self.settings_frame,
            anchor="nw",
        )

        self.settings_frame.bind(
            "<Configure>",
            self._update_scroll_region,
        )

        canvas.bind(
            "<Configure>",
            self._resize_settings_window,
        )

        self._build_settings_content()

        canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel,
        )

    def _update_scroll_region(
        self,
        event=None,
    ):
        bbox = self.settings_canvas.bbox("all")

        if bbox:
            self.settings_canvas.configure(
                scrollregion=bbox
            )

    def _resize_settings_window(
        self,
        event,
    ):
        self.settings_canvas.itemconfigure(
            self.settings_window,
            width=event.width,
        )

    def _on_mousewheel(
        self,
        event,
    ):
        try:
            if self.winfo_containing(
                event.x_root,
                event.y_root,
            ):
                self.settings_canvas.yview_scroll(
                    int(-1 * (event.delta / 120)),
                    "units",
                )
        except Exception:
            pass

    # ==================================================================
    # SETTINGS CONTENT
    # ==================================================================

    def _build_settings_content(self):
        container = self.settings_frame

        # --------------------------------------------------------------
        # SOURCE PDF
        # --------------------------------------------------------------

        self._section_title(
            container,
            "SOURCE PDF",
        )

        self._button(
            container,
            "+  Open PDF",
            self.open_pdf,
        ).pack(
            fill="x",
            padx=20,
            pady=(6, 8),
        )

        self.file_label = tk.Label(
            container,
            text="No PDF selected",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            justify="left",
            wraplength=340,
            font=("Segoe UI", 9),
        )

        self.file_label.pack(
            fill="x",
            padx=20,
        )

        self._separator(container)

        # --------------------------------------------------------------
        # HEADER
        # --------------------------------------------------------------

        self._section_title(
            container,
            "HEADER",
        )

        tk.Checkbutton(
            container,
            text="Enable Header",
            variable=self.header_enabled,
            command=self._on_header_toggle,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            selectcolor=self.CARD,
            font=("Segoe UI", 9),
        ).pack(
            anchor="w",
            padx=20,
            pady=(4, 8),
        )

        self.header_type_frame = tk.Frame(
            container,
            bg=self.CARD,
        )

        self.header_type_frame.pack(
            fill="x",
            padx=20,
        )

        self._label(
            self.header_type_frame,
            "Header Type",
        ).pack(
            anchor="w",
        )

        radio_row = tk.Frame(
            self.header_type_frame,
            bg=self.CARD,
        )

        radio_row.pack(
            fill="x",
            pady=(4, 8),
        )

        tk.Radiobutton(
            radio_row,
            text="Text",
            variable=self.header_type,
            value="text",
            command=self._refresh_controls,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            selectcolor=self.CARD,
            font=("Segoe UI", 9),
        ).pack(
            side="left",
            padx=(0, 15),
        )

        tk.Radiobutton(
            radio_row,
            text="Image / Letterhead",
            variable=self.header_type,
            value="image",
            command=self._refresh_controls,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            selectcolor=self.CARD,
            font=("Segoe UI", 9),
        ).pack(
            side="left",
        )

        self.header_dynamic = tk.Frame(
            container,
            bg=self.CARD,
        )

        self.header_dynamic.pack(
            fill="x",
            padx=20,
        )

        self._build_header_dynamic()

        self._separator(container)

        # --------------------------------------------------------------
        # HEADER POSITION
        # --------------------------------------------------------------

        self._section_title(
            container,
            "HEADER POSITION",
        )

        self._combo_field(
            container,
            "Alignment",
            self.header_alignment,
            [
                "left",
                "center",
                "right",
            ],
        )

        self._number_field(
            container,
            "Top Margin (pt)",
            self.header_margin,
        )

        self._number_field(
            container,
            "Header Height (pt)",
            self.header_height,
        )

        self._separator(container)

        # --------------------------------------------------------------
        # FOOTER
        # --------------------------------------------------------------

        self._section_title(
            container,
            "FOOTER",
        )

        tk.Checkbutton(
            container,
            text="Enable Footer",
            variable=self.footer_enabled,
            command=self._on_footer_toggle,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            selectcolor=self.CARD,
            font=("Segoe UI", 9),
        ).pack(
            anchor="w",
            padx=20,
            pady=(4, 8),
        )

        self.footer_type_frame = tk.Frame(
            container,
            bg=self.CARD,
        )

        self.footer_type_frame.pack(
            fill="x",
            padx=20,
        )

        self._label(
            self.footer_type_frame,
            "Footer Type",
        ).pack(
            anchor="w",
        )

        footer_radio = tk.Frame(
            self.footer_type_frame,
            bg=self.CARD,
        )

        footer_radio.pack(
            fill="x",
            pady=(4, 8),
        )

        tk.Radiobutton(
            footer_radio,
            text="Text",
            variable=self.footer_type,
            value="text",
            command=self._refresh_controls,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            selectcolor=self.CARD,
            font=("Segoe UI", 9),
        ).pack(
            side="left",
            padx=(0, 15),
        )

        tk.Radiobutton(
            footer_radio,
            text="Image / Letterhead",
            variable=self.footer_type,
            value="image",
            command=self._refresh_controls,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            selectcolor=self.CARD,
            font=("Segoe UI", 9),
        ).pack(
            side="left",
        )

        self.footer_dynamic = tk.Frame(
            container,
            bg=self.CARD,
        )

        self.footer_dynamic.pack(
            fill="x",
            padx=20,
        )

        self._build_footer_dynamic()

        self._separator(container)

        # --------------------------------------------------------------
        # FOOTER POSITION
        # --------------------------------------------------------------

        self._section_title(
            container,
            "FOOTER POSITION",
        )

        self._combo_field(
            container,
            "Alignment",
            self.footer_alignment,
            [
                "left",
                "center",
                "right",
            ],
        )

        self._number_field(
            container,
            "Bottom Margin (pt)",
            self.footer_margin,
        )

        self._number_field(
            container,
            "Footer Height (pt)",
            self.footer_height,
        )

        self._separator(container)

        # --------------------------------------------------------------
        # EXPORT
        # --------------------------------------------------------------

        self._section_title(
            container,
            "EXPORT",
        )

        self._button(
            container,
            "Apply Header & Footer",
            self.apply_header_footer,
        ).pack(
            fill="x",
            padx=20,
            pady=(5, 8),
        )

        tk.Button(
            container,
            text="Reset",
            command=self.reset,
            bg="#EEF2F7",
            fg=self.TEXT,
            activebackground="#E2E8F0",
            activeforeground=self.TEXT,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9),
            pady=8,
        ).pack(
            fill="x",
            padx=20,
            pady=(0, 20),
        )

    # ==================================================================
    # HEADER DYNAMIC CONTENT
    # ==================================================================

    def _build_header_dynamic(self):
        self.header_text_area = tk.Frame(
            self.header_dynamic,
            bg=self.CARD,
        )

        self._label(
            self.header_text_area,
            "Header Text",
        ).pack(
            anchor="w",
        )

        entry = tk.Entry(
            self.header_text_area,
            textvariable=self.header_text,
            relief="solid",
            bd=1,
            font=("Segoe UI", 9),
        )

        entry.pack(
            fill="x",
            pady=(5, 8),
            ipady=6,
        )

        entry.bind(
            "<KeyRelease>",
            lambda e: self._update_preview(),
        )

        self.header_image_area = tk.Frame(
            self.header_dynamic,
            bg=self.CARD,
        )

        self._label(
            self.header_image_area,
            "Header Image / Letterhead",
        ).pack(
            anchor="w",
        )

        self.header_upload_button = (
            self._outline_button(
                self.header_image_area,
                "Upload Header Image",
                self.upload_header_image,
            )
        )

        self.header_upload_button.pack(
            fill="x",
            pady=(5, 5),
        )

        self.header_image_label = tk.Label(
            self.header_image_area,
            text="No image selected",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            wraplength=340,
            font=("Segoe UI", 8),
        )

        self.header_image_label.pack(
            fill="x",
        )

    # ==================================================================
    # FOOTER DYNAMIC CONTENT
    # ==================================================================

    def _build_footer_dynamic(self):
        self.footer_text_area = tk.Frame(
            self.footer_dynamic,
            bg=self.CARD,
        )

        self._label(
            self.footer_text_area,
            "Footer Text",
        ).pack(
            anchor="w",
        )

        entry = tk.Entry(
            self.footer_text_area,
            textvariable=self.footer_text,
            relief="solid",
            bd=1,
            font=("Segoe UI", 9),
        )

        entry.pack(
            fill="x",
            pady=(5, 8),
            ipady=6,
        )

        entry.bind(
            "<KeyRelease>",
            lambda e: self._update_preview(),
        )

        self.footer_image_area = tk.Frame(
            self.footer_dynamic,
            bg=self.CARD,
        )

        self._label(
            self.footer_image_area,
            "Footer Image",
        ).pack(
            anchor="w",
        )

        self.footer_upload_button = (
            self._outline_button(
                self.footer_image_area,
                "Upload Footer Image",
                self.upload_footer_image,
            )
        )

        self.footer_upload_button.pack(
            fill="x",
            pady=(5, 5),
        )

        self.footer_image_label = tk.Label(
            self.footer_image_area,
            text="No image selected",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            wraplength=340,
            font=("Segoe UI", 8),
        )

        self.footer_image_label.pack(
            fill="x",
        )

    # ==================================================================
    # PREVIEW PANEL
    # ==================================================================

    def _build_preview_panel(self, parent):
        card = tk.Frame(
            parent,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
        )

        card.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        card.grid_rowconfigure(
            1,
            weight=1,
        )

        card.grid_columnconfigure(
            0,
            weight=1,
        )

        tk.Label(
            card,
            text="LIVE PREVIEW",
            bg=self.CARD,
            fg=self.NAVY,
            font=("Segoe UI", 10, "bold"),
        ).grid(
            row=0,
            column=0,
            sticky="w",
            padx=20,
            pady=(18, 10),
        )

        preview_container = tk.Frame(
            card,
            bg=self.PREVIEW_BG,
        )

        preview_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=12,
            pady=(0, 12),
        )

        preview_container.grid_rowconfigure(
            0,
            weight=1,
        )

        preview_container.grid_columnconfigure(
            0,
            weight=1,
        )

        self.preview_canvas = tk.Canvas(
            preview_container,
            bg=self.PREVIEW_BG,
            highlightthickness=0,
        )

        self.preview_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.preview_canvas.bind(
            "<Configure>",
            lambda e: self._update_preview(),
        )

    # ==================================================================
    # HELPERS
    # ==================================================================

    def _section_title(
        self,
        parent,
        text,
    ):
        tk.Label(
            parent,
            text=text,
            bg=self.CARD,
            fg=self.NAVY,
            font=("Segoe UI", 9, "bold"),
        ).pack(
            anchor="w",
            padx=20,
            pady=(16, 7),
        )

    def _label(
        self,
        parent,
        text,
    ):
        return tk.Label(
            parent,
            text=text,
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI", 9),
        )

    def _separator(
        self,
        parent,
    ):
        tk.Frame(
            parent,
            bg=self.BORDER,
            height=1,
        ).pack(
            fill="x",
            padx=20,
            pady=14,
        )

    def _button(
        self,
        parent,
        text,
        command,
    ):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=self.NAVY,
            fg="white",
            activebackground=self.NAVY,
            activeforeground="white",
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            pady=9,
        )

    def _outline_button(
        self,
        parent,
        text,
        command,
    ):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg="#F8FAFC",
            fg=self.TEXT,
            activebackground="#E2E8F0",
            activeforeground=self.TEXT,
            relief="solid",
            bd=1,
            cursor="hand2",
            font=("Segoe UI", 9),
            pady=7,
        )

    def _combo_field(
        self,
        parent,
        label,
        variable,
        values,
    ):
        frame = tk.Frame(
            parent,
            bg=self.CARD,
        )

        frame.pack(
            fill="x",
            padx=20,
            pady=(0, 9),
        )

        self._label(
            frame,
            label,
        ).pack(
            anchor="w",
            pady=(0, 4),
        )

        combo = ttk.Combobox(
            frame,
            textvariable=variable,
            values=values,
            state="readonly",
            font=("Segoe UI", 9),
        )

        combo.pack(
            fill="x",
            ipady=3,
        )

        combo.bind(
            "<<ComboboxSelected>>",
            lambda e: self._update_preview(),
        )

    def _number_field(
        self,
        parent,
        label,
        variable,
    ):
        frame = tk.Frame(
            parent,
            bg=self.CARD,
        )

        frame.pack(
            fill="x",
            padx=20,
            pady=(0, 9),
        )

        self._label(
            frame,
            label,
        ).pack(
            anchor="w",
            pady=(0, 4),
        )

        spin = tk.Spinbox(
            frame,
            from_=0,
            to=500,
            increment=1,
            textvariable=variable,
            font=("Segoe UI", 9),
        )

        spin.pack(
            fill="x",
            ipady=3,
        )

        spin.bind(
            "<KeyRelease>",
            lambda e: self._update_preview(),
        )

    # ==================================================================
    # DYNAMIC CONTROL
    # ==================================================================

    def _refresh_controls(self):
        self._clear_frame(
            self.header_dynamic
        )

        self._clear_frame(
            self.footer_dynamic
        )

        if self.header_type.get() == "text":
            self.header_text_area.pack(
                fill="x",
            )
        else:
            self.header_image_area.pack(
                fill="x",
            )

        if self.footer_type.get() == "text":
            self.footer_text_area.pack(
                fill="x",
            )
        else:
            self.footer_image_area.pack(
                fill="x",
            )

        self.settings_frame.update_idletasks()
        self._update_scroll_region()

        self._update_preview()

    def _clear_frame(
        self,
        frame,
    ):
        for widget in frame.winfo_children():
            widget.pack_forget()

    # ==================================================================
    # ENABLE / DISABLE
    # ==================================================================

    def _on_header_toggle(self):
        self._refresh_controls()

    def _on_footer_toggle(self):
        self._refresh_controls()

    # ==================================================================
    # OPEN PDF
    # ==================================================================

    def open_pdf(self):
        path = filedialog.askopenfilename(
            title="Open PDF",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*"),
            ],
        )

        if not path:
            return

        try:
            if self.pdf_document:
                self.pdf_document.close()
                self.pdf_document = None

            self.pdf_document = fitz.open(path)
            self.pdf_path = path

            pages = len(self.pdf_document)

            self.file_label.configure(
                text=(
                    f"{os.path.basename(path)}\n"
                    f"{pages} page(s) • Preview: Page 1"
                ),
                fg=self.TEXT,
            )

            self._set_status(
                f"Loaded {os.path.basename(path)}"
            )

            self._update_preview()

        except Exception as exc:
            messagebox.showerror(
                "Unable to Open PDF",
                f"Unable to open PDF:\n\n{exc}",
            )

    # ==================================================================
    # IMAGE UPLOAD
    # ==================================================================

    def upload_header_image(self):
        path = self._choose_image()

        if not path:
            return

        self.header_image_path = path

        self.header_image_label.configure(
            text=os.path.basename(path),
            fg=self.TEXT,
        )

        self.header_type.set("image")
        self.header_enabled.set(True)

        self._refresh_controls()
        self._update_preview()

    def upload_footer_image(self):
        path = self._choose_image()

        if not path:
            return

        self.footer_image_path = path

        self.footer_image_label.configure(
            text=os.path.basename(path),
            fg=self.TEXT,
        )

        self.footer_type.set("image")
        self.footer_enabled.set(True)

        self._refresh_controls()
        self._update_preview()

    def _choose_image(self):
        return filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                (
                    "Image files",
                    "*.png *.jpg *.jpeg *.webp *.bmp",
                ),
                ("PNG", "*.png"),
                ("JPEG", "*.jpg *.jpeg"),
                ("All files", "*.*"),
            ],
        )

    # ==================================================================
    # PREVIEW
    # ==================================================================

    def _update_preview(self):
        if not hasattr(
            self,
            "preview_canvas",
        ):
            return

        self.preview_canvas.delete("all")

        self._preview_images.clear()

        if not self.pdf_path:
            self._draw_empty_preview()
            return

        try:
            if not self.pdf_document:
                self._draw_empty_preview()
                return

            if len(self.pdf_document) == 0:
                self._draw_empty_preview()
                return

            page = self.pdf_document[0]

            pix = page.get_pixmap(
                matrix=fitz.Matrix(
                    1.2,
                    1.2,
                ),
                alpha=False,
            )

            image = Image.frombytes(
                "RGB",
                [
                    pix.width,
                    pix.height,
                ],
                pix.samples,
            )

            canvas_width = max(
                self.preview_canvas.winfo_width(),
                400,
            )

            canvas_height = max(
                self.preview_canvas.winfo_height(),
                400,
            )

            image.thumbnail(
                (
                    canvas_width - 80,
                    canvas_height - 80,
                ),
                Image.Resampling.LANCZOS,
            )

            self.preview_photo = ImageTk.PhotoImage(
                image
            )

            x = canvas_width // 2
            y = canvas_height // 2

            self.preview_canvas.create_image(
                x,
                y,
                image=self.preview_photo,
                anchor="center",
            )

            self._draw_preview_overlay(
                x,
                y,
                image.width,
                image.height,
            )

        except Exception as exc:
            self._draw_empty_preview(
                f"Preview unavailable\n{exc}"
            )

    def _draw_empty_preview(
        self,
        text=None,
    ):
        width = max(
            self.preview_canvas.winfo_width(),
            400,
        )

        height = max(
            self.preview_canvas.winfo_height(),
            400,
        )

        message = (
            text
            or
            "No PDF loaded\n\n"
            "Open a PDF to preview your "
            "header/footer."
        )

        self.preview_canvas.create_text(
            width // 2,
            height // 2,
            text=message,
            fill=self.MUTED,
            font=("Segoe UI", 11),
            justify="center",
        )

    def _draw_preview_overlay(
        self,
        center_x,
        center_y,
        image_width,
        image_height,
    ):
        left = (
            center_x
            - image_width / 2
        )

        top = (
            center_y
            - image_height / 2
        )

        right = (
            center_x
            + image_width / 2
        )

        bottom = (
            center_y
            + image_height / 2
        )

        scale = (
            image_width
            / max(
                self.pdf_document[0].rect.width,
                1,
            )
        )

        # --------------------------------------------------------------
        # HEADER
        # --------------------------------------------------------------

        if self.header_enabled.get():
            height = self._safe_number(
                self.header_height,
                72,
            )

            margin = self._safe_number(
                self.header_margin,
                24,
            )

            h = max(
                8,
                height * scale,
            )

            y1 = top + margin * scale

            y2 = min(
                y1 + h,
                bottom,
            )

            x1 = left + margin * scale
            x2 = right - margin * scale

            self.preview_canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline=self.BLUE,
                width=1,
                dash=(6, 4),
            )

            self.preview_canvas.create_text(
                x1 + 6,
                y1 + 10,
                text="HEADER",
                anchor="w",
                fill=self.BLUE,
                font=("Segoe UI", 8, "bold"),
            )

            self._draw_preview_content(
                x1,
                x2,
                y1,
                y2,
                is_header=True,
            )

        # --------------------------------------------------------------
        # FOOTER
        # --------------------------------------------------------------

        if self.footer_enabled.get():
            height = self._safe_number(
                self.footer_height,
                48,
            )

            margin = self._safe_number(
                self.footer_margin,
                24,
            )

            h = max(
                8,
                height * scale,
            )

            y2 = (
                bottom
                - margin * scale
            )

            y1 = max(
                y2 - h,
                top,
            )

            x1 = left + margin * scale
            x2 = right - margin * scale

            self.preview_canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                outline=self.BLUE,
                width=1,
                dash=(6, 4),
            )

            self.preview_canvas.create_text(
                x1 + 6,
                y1 + 10,
                text="FOOTER",
                anchor="w",
                fill=self.BLUE,
                font=("Segoe UI", 8, "bold"),
            )

            self._draw_preview_content(
                x1,
                x2,
                y1,
                y2,
                is_header=False,
            )

    def _draw_preview_content(
        self,
        left,
        right,
        top,
        bottom,
        is_header,
    ):
        if is_header:
            element_type = self.header_type.get()
            image_path = self.header_image_path
            text = self.header_text.get()
            alignment = self.header_alignment.get()
        else:
            element_type = self.footer_type.get()
            image_path = self.footer_image_path
            text = self.footer_text.get()
            alignment = self.footer_alignment.get()

        if (
            element_type == "image"
            and image_path
            and os.path.exists(image_path)
        ):
            self._draw_image_preview(
                image_path,
                left,
                right,
                top,
                bottom,
            )

            return

        if element_type == "text":
            if alignment == "left":
                anchor = "w"
                x = left + 10

            elif alignment == "right":
                anchor = "e"
                x = right - 10

            else:
                anchor = "center"
                x = (
                    left
                    + right
                ) / 2

            self.preview_canvas.create_text(
                x,
                (top + bottom) / 2,
                text=text,
                anchor=anchor,
                fill=self.NAVY,
                font=("Segoe UI", 9, "bold"),
            )

    def _draw_image_preview(
        self,
        image_path,
        left,
        right,
        top,
        bottom,
    ):
        try:
            image = Image.open(
                image_path
            ).convert("RGBA")

            width = max(
                int(right - left - 8),
                20,
            )

            height = max(
                int(bottom - top - 8),
                20,
            )

            image = image.resize(
                (
                    width,
                    height,
                ),
                Image.Resampling.LANCZOS,
            )

            photo = ImageTk.PhotoImage(
                image
            )

            self.preview_canvas.create_image(
                left + 4,
                top + 4,
                image=photo,
                anchor="nw",
            )

            self._preview_images.append(
                photo
            )

            if len(
                self._preview_images
            ) > 10:
                self._preview_images = (
                    self._preview_images[-5:]
                )

        except Exception:
            pass

    # ==================================================================
    # EXPORT
    # ==================================================================

    def apply_header_footer(self):
        if not self.pdf_path:
            messagebox.showwarning(
                "PDF Required",
                "Please open a PDF first.",
            )
            return

        if (
            not self.header_enabled.get()
            and not self.footer_enabled.get()
        ):
            messagebox.showwarning(
                "Nothing to Apply",
                "Enable Header or Footer first.",
            )
            return

        output_path = filedialog.asksaveasfilename(
            title="Save PDF",
            defaultextension=".pdf",
            filetypes=[
                ("PDF files", "*.pdf"),
            ],
            initialfile="header_footer_output.pdf",
        )

        if not output_path:
            return

        header = self._get_header_config()
        footer = self._get_footer_config()

        try:
            processor = HeaderFooterProcessor()

            processor.apply(
                input_path=self.pdf_path,
                output_path=output_path,
                header=header,
                footer=footer,
            )

            self._set_status(
                "Header & Footer applied successfully."
            )

            messagebox.showinfo(
                "Success",
                "Header & Footer have been "
                "applied successfully.",
            )

        except Exception as exc:
            messagebox.showerror(
                "Export Error",
                f"Unable to export PDF:\n\n{exc}",
            )

    # ==================================================================
    # CONFIG
    # ==================================================================

    def _get_header_config(self):
        if not self.header_enabled.get():
            return None

        return {
            "enabled": True,
            "type": self.header_type.get(),
            "text": self.header_text.get(),
            "image_path": self.header_image_path,
            "alignment": self.header_alignment.get(),
            "margin": self._safe_number(
                self.header_margin,
                24,
            ),
            "height": self._safe_number(
                self.header_height,
                72,
            ),
        }

    def _get_footer_config(self):
        if not self.footer_enabled.get():
            return None

        return {
            "enabled": True,
            "type": self.footer_type.get(),
            "text": self.footer_text.get(),
            "image_path": self.footer_image_path,
            "alignment": self.footer_alignment.get(),
            "margin": self._safe_number(
                self.footer_margin,
                24,
            ),
            "height": self._safe_number(
                self.footer_height,
                48,
            ),
        }

    def _safe_number(
        self,
        variable,
        default,
    ):
        try:
            value = float(
                variable.get()
            )

            if value < 0:
                return default

            return value

        except Exception:
            return default

    # ==================================================================
    # RESET
    # ==================================================================

    def reset(self):
        self.header_enabled.set(False)
        self.footer_enabled.set(False)

        self.header_type.set("text")
        self.footer_type.set("text")

        self.header_alignment.set("center")
        self.footer_alignment.set("center")

        self.header_margin.set(24)
        self.header_height.set(72)

        self.footer_margin.set(24)
        self.footer_height.set(48)

        self.header_text.set(
            "CONFIDENTIAL"
        )

        self.footer_text.set(
            "Page {page} of {pages}"
        )

        self.header_image_path = None
        self.footer_image_path = None

        self.header_image_label.configure(
            text="No image selected",
            fg=self.MUTED,
        )

        self.footer_image_label.configure(
            text="No image selected",
            fg=self.MUTED,
        )

        self._refresh_controls()
        self._update_preview()

        self._set_status(
            "Header & Footer settings reset."
        )

    # ==================================================================
    # STATUS
    # ==================================================================

    def _set_status(
        self,
        message,
    ):
        if callable(
            self.status_callback
        ):
            try:
                self.status_callback(
                    message
                )
            except Exception:
                pass

    # ==================================================================
    # CLEANUP
    # ==================================================================

    def destroy(self):
        try:
            if self.pdf_document:
                self.pdf_document.close()
                self.pdf_document = None
        except Exception:
            pass

        try:
            self.settings_canvas.unbind_all(
                "<MouseWheel>"
            )
        except Exception:
            pass

        super().destroy()
