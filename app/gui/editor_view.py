import os
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser

from PIL import Image, ImageTk

from app.core.pdf_editor import PDFEditor
from app.models.text_object import TextObject
from app.models.signature_object import SignatureObject
from app.gui.theme import ACCENT, APP_BG, BORDER, INK, MUTED, NAVY, NAVY_HOVER, SURFACE


class EditorView(tk.Frame):

    BG = APP_BG
    CARD = SURFACE
    TEXT = INK
    MUTED = MUTED
    BORDER = BORDER
    DARK = NAVY
    BLUE = ACCENT
    BLUE_HOVER = NAVY_HOVER
    LIGHT_BLUE = "#EFF4FF"
    DANGER = "#D92D20"

    def __init__(self, parent, status_callback=None):
        super().__init__(parent, bg=self.BG)

        self.status_callback = status_callback

        self.editor = PDFEditor()

        self.current_page = 0
        self.preview_scale = 1.0

        self.preview_photo = None

        self.selected_object = None
        self.selected_type = None

        self.drag_start = None
        self.object_start = None
        self.drag_mode = None
        self._interaction_snapshot = None

        self.history = []
        self.redo_stack = []

        self.text_color = "#101828"
        self.text_background_color = (1.0, 0.95, 0.70)

        self.signature_path = None

        self._build_ui()

    # =========================================================
    # UI
    # =========================================================

    def _build_ui(self):

        # The application shell already supplies the page title and purpose.
        # Keep this view focused on the editing task so the heading is not
        # repeated and the document workspace receives more room.
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        body = tk.Frame(
            self,
            bg=self.BG
        )

        body.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=20,
            pady=20
        )

        body.grid_columnconfigure(0, weight=0)
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        self._build_toolbar(body)
        self._build_workspace(body)

    # =========================================================
    # TOOLBAR
    # =========================================================

    def _build_toolbar(self, parent):

        panel = tk.Frame(
            parent,
            bg=self.CARD,
            width=258,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        panel.grid(
            row=0,
            column=0,
            sticky="ns",
            padx=(0, 18)
        )

        panel.grid_propagate(False)

        self.toolbar_canvas = tk.Canvas(
            panel,
            bg=self.CARD,
            highlightthickness=0,
            width=237
        )

        scrollbar = tk.Scrollbar(
            panel,
            orient="vertical",
            command=self.toolbar_canvas.yview
        )

        self.toolbar_canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.toolbar_canvas.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        inner = tk.Frame(
            self.toolbar_canvas,
            bg=self.CARD
        )

        self.toolbar_window = self.toolbar_canvas.create_window(
            (0, 0),
            window=inner,
            anchor="nw",
        )
        self.toolbar_inner = inner

        inner.bind(
            "<Configure>",
            lambda e: self.toolbar_canvas.configure(
                scrollregion=self.toolbar_canvas.bbox("all")
            )
        )

        self.toolbar_canvas.bind(
            "<Configure>",
            self._resize_toolbar_inner,
        )

        # The side panel contains many controls. Bind scrolling to every
        # control inside it, so the wheel works while hovering an entry,
        # button, or label—not only empty canvas space.
        self.toolbar_canvas.bind(
            "<MouseWheel>",
            self._on_toolbar_mousewheel,
        )

        self._build_toolbar_content(inner)
        self._bind_toolbar_scrolling(inner)

    def _resize_toolbar_inner(self, event):
        """Keep the scrollable toolbar content aligned with its viewport."""
        self.toolbar_canvas.itemconfigure(
            self.toolbar_window,
            width=event.width,
        )

    def _on_toolbar_mousewheel(self, event):
        """Scroll the edit-control panel from any of its child widgets."""
        if event.delta:
            direction = -1 if event.delta > 0 else 1
            steps = max(1, abs(event.delta) // 120)
            self.toolbar_canvas.yview_scroll(direction * steps, "units")
            return "break"

        return None

    def _on_toolbar_button_scroll(self, event):
        self.toolbar_canvas.yview_scroll(
            -1 if event.num == 4 else 1,
            "units",
        )
        return "break"

    def _bind_toolbar_scrolling(self, widget):
        """Attach local wheel handling recursively without affecting preview."""
        widget.bind("<MouseWheel>", self._on_toolbar_mousewheel, add="+")
        widget.bind("<Button-4>", self._on_toolbar_button_scroll, add="+")
        widget.bind("<Button-5>", self._on_toolbar_button_scroll, add="+")

        for child in widget.winfo_children():
            self._bind_toolbar_scrolling(child)

    def _section(self, parent, title):

        tk.Label(
            parent,
            text=title.upper(),
            font=("Segoe UI", 8, "bold"),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(
            anchor="w",
            padx=16,
            pady=(17, 7)
        )

    def _build_toolbar_content(self, parent):

        tk.Label(
            parent,
            text="EDIT CONTROLS",
            font=("Segoe UI", 11, "bold"),
            fg=self.TEXT,
            bg=self.CARD
        ).pack(anchor="w", padx=16, pady=(18, 2))

        tk.Label(
            parent,
            text="Open a file, add content, then export when ready.",
            font=("Segoe UI", 8),
            fg=self.MUTED,
            bg=self.CARD,
            wraplength=210,
            justify="left"
        ).pack(anchor="w", padx=16)

        # -----------------------------------------------------
        # DOCUMENT
        # -----------------------------------------------------

        self._section(parent, "Document")

        self._button(
            parent,
            "+  Open PDF",
            self.open_pdf,
            primary=True
        )

        self.file_label = tk.Label(
            parent,
            text="No PDF selected",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD,
            wraplength=185,
            justify="left"
        )

        self.file_label.pack(
            anchor="w",
            padx=16,
            pady=(8, 0)
        )

        self._separator(parent)

        # -----------------------------------------------------
        # TOOLS
        # -----------------------------------------------------

        self._section(parent, "Add content")

        self._button(
            parent,
            "+  Add Text",
            self.activate_add_text
        )

        self._button(
            parent,
            "+  Add Signature",
            self.activate_signature
        )

        self._button(
            parent,
            "Remove Selected Item",
            self.delete_selected,
            danger=True
        )

        self._separator(parent)

        # -----------------------------------------------------
        # TEXT
        # -----------------------------------------------------

        self._section(parent, "Text Properties")

        tk.Label(
            parent,
            text="Text content",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(
            anchor="w",
            padx=16
        )

        self.text_entry = tk.Text(
            parent,
            height=4,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            highlightthickness=0
        )

        self.text_entry.pack(
            fill="x",
            padx=16,
            pady=(4, 10)
        )

        self.text_entry.bind(
            "<KeyRelease>",
            lambda e: self.update_selected_text()
        )

        tk.Label(
            parent,
            text="Font Size",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(
            anchor="w",
            padx=16
        )

        self.font_size_var = tk.DoubleVar(value=16)

        font_size_controls = tk.Frame(
            parent,
            bg=self.CARD
        )

        font_size_controls.pack(
            anchor="w",
            padx=16,
            pady=(4, 10)
        )

        self._small_button(
            font_size_controls,
            "−",
            self.decrease_selected_text_size
        ).pack(side="left")

        self.font_size_spinbox = tk.Spinbox(
            font_size_controls,
            from_=6,
            to=120,
            textvariable=self.font_size_var,
            width=6,
            command=self.update_selected_text_style
        )

        self.font_size_spinbox.pack(
            side="left",
            padx=5
        )

        self.font_size_spinbox.bind(
            "<Return>",
            lambda _: self.update_selected_text_style()
        )

        self.font_size_spinbox.bind(
            "<FocusOut>",
            lambda _: self.update_selected_text_style()
        )

        self._small_button(
            font_size_controls,
            "+",
            self.increase_selected_text_size
        ).pack(side="left")

        self.bold_var = tk.BooleanVar(value=False)
        self.italic_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            parent,
            text="Bold",
            variable=self.bold_var,
            command=self.update_selected_text_style,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD
        ).pack(
            anchor="w",
            padx=12
        )

        tk.Checkbutton(
            parent,
            text="Italic",
            variable=self.italic_var,
            command=self.update_selected_text_style,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD
        ).pack(
            anchor="w",
            padx=12
        )

        self._button(
            parent,
            "Text Color",
            self.choose_text_color
        )

        tk.Label(
            parent,
            text="Text Background",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(
            anchor="w",
            padx=16,
            pady=(10, 0)
        )

        self.background_transparent_var = tk.BooleanVar(value=True)

        tk.Checkbutton(
            parent,
            text="Transparent",
            variable=self.background_transparent_var,
            command=self.toggle_text_background,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD
        ).pack(
            anchor="w",
            padx=12
        )

        self._button(
            parent,
            "Choose Background Color",
            self.choose_text_background_color
        )

        # -----------------------------------------------------
        # ALIGNMENT
        # -----------------------------------------------------

        tk.Label(
            parent,
            text="Alignment",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(
            anchor="w",
            padx=16,
            pady=(10, 3)
        )

        self.align_var = tk.StringVar(value="Left")

        alignment_menu = tk.OptionMenu(
            parent,
            self.align_var,
            "Left",
            "Center",
            "Right",
            command=lambda _: self.update_selected_text_style()
        )

        alignment_menu.config(
            width=15,
            bg="#FFFFFF",
            fg=self.TEXT,
            relief="solid",
            bd=1
        )

        alignment_menu.pack(
            padx=16,
            anchor="w"
        )

        self._separator(parent)

        # -----------------------------------------------------
        # SIGNATURE
        # -----------------------------------------------------

        self._section(parent, "Signature file")

        self.signature_label = tk.Label(
            parent,
            text="No signature uploaded",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD,
            wraplength=185,
            justify="left"
        )

        self.signature_label.pack(
            anchor="w",
            padx=16
        )

        self._button(
            parent,
            "Choose Signature Image",
            self.upload_signature
        )

        tk.Label(
            parent,
            text="Signature Size",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(
            anchor="w",
            padx=16,
            pady=(10, 3)
        )

        self.signature_scale_var = tk.DoubleVar(value=1.0)

        signature_scale = tk.Scale(
            parent,
            from_=0.25,
            to=3.0,
            resolution=0.05,
            orient="horizontal",
            variable=self.signature_scale_var,
            command=self.resize_selected_signature,
            bg=self.CARD,
            highlightthickness=0
        )

        signature_scale.pack(
            fill="x",
            padx=12
        )

        self._separator(parent)

        # -----------------------------------------------------
        # HISTORY
        # -----------------------------------------------------

        self._section(parent, "History")

        history_frame = tk.Frame(
            parent,
            bg=self.CARD
        )

        history_frame.pack(
            fill="x",
            padx=12
        )

        self._small_button(
            history_frame,
            "Undo",
            self.undo
        ).pack(
            side="left",
            padx=(0, 5)
        )

        self._small_button(
            history_frame,
            "Redo",
            self.redo
        ).pack(
            side="left"
        )

        self._separator(parent)

        # -----------------------------------------------------
        # EXPORT
        # -----------------------------------------------------

        self._section(parent, "Export")

        self._button(
            parent,
            "Export Edited PDF",
            self.export_pdf,
            primary=True
        )

        tk.Label(
            parent,
            text="Tip: drag an item to move it, or drag its blue corner to resize it.",
            font=("Segoe UI", 8),
            fg=self.MUTED,
            bg=self.CARD,
            wraplength=210,
            justify="left"
        ).pack(
            anchor="w",
            padx=16,
            pady=(12, 20)
        )

    # =========================================================
    # WORKSPACE
    # =========================================================

    def _build_workspace(self, parent):

        workspace = tk.Frame(
            parent,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1
        )

        workspace.grid(
            row=0,
            column=1,
            sticky="nsew"
        )

        workspace.grid_rowconfigure(1, weight=1)
        workspace.grid_columnconfigure(0, weight=1)

        top = tk.Frame(
            workspace,
            bg=self.CARD,
            height=48
        )

        top.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        top.grid_propagate(False)

        tk.Label(
            top,
            text="DOCUMENT PREVIEW",
            font=("Segoe UI", 9, "bold"),
            fg=self.TEXT,
            bg=self.CARD
        ).pack(
            side="left",
            padx=16
        )

        self.page_label = tk.Label(
            top,
            text="Page 0 / 0",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD
        )

        self.page_label.pack(
            side="right",
            padx=16
        )

        tk.Label(
            top,
            text="Use the controls below to browse and zoom",
            font=("Segoe UI", 8),
            fg=self.MUTED,
            bg=self.CARD
        ).pack(side="left", padx=(10, 0))

        preview_area = tk.Frame(
            workspace,
            bg="#EEF2F6"
        )

        preview_area.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=12,
            pady=(0, 12)
        )

        preview_area.grid_rowconfigure(0, weight=1)
        preview_area.grid_columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            preview_area,
            bg="#EEF2F6",
            highlightthickness=0
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        vscroll = tk.Scrollbar(
            preview_area,
            orient="vertical",
            command=self.canvas.yview
        )

        hscroll = tk.Scrollbar(
            preview_area,
            orient="horizontal",
            command=self.canvas.xview
        )

        vscroll.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        hscroll.grid(
            row=1,
            column=0,
            sticky="ew"
        )

        self.canvas.configure(
            yscrollcommand=vscroll.set,
            xscrollcommand=hscroll.set
        )

        self.canvas.bind(
            "<ButtonPress-1>",
            self.on_canvas_press
        )

        self.canvas.bind(
            "<B1-Motion>",
            self.on_canvas_drag
        )

        self.canvas.bind(
            "<ButtonRelease-1>",
            self.on_canvas_release
        )

        self.canvas.bind(
            "<Double-Button-1>",
            self.on_canvas_double_click
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self._fit_preview()
        )

        self._build_page_controls(workspace)

    # =========================================================
    # PAGE CONTROLS
    # =========================================================

    def _build_page_controls(self, parent):

        controls = tk.Frame(
            parent,
            bg=self.CARD,
            height=54
        )

        controls.grid(
            row=2,
            column=0,
            sticky="ew"
        )

        controls.grid_propagate(False)

        self._small_button(
            controls,
            "Previous",
            self.previous_page
        ).pack(
            side="left",
            padx=(12, 4),
            pady=10
        )

        self._small_button(
            controls,
            "Next",
            self.next_page
        ).pack(
            side="left",
            pady=10
        )

        self.zoom_label = tk.Label(
            controls,
            text="100% zoom",
            font=("Segoe UI", 9),
            fg=self.MUTED,
            bg=self.CARD
        )

        self.zoom_label.pack(
            side="right",
            padx=16
        )

        self._small_button(
            controls,
            "Zoom +",
            self.zoom_in
        ).pack(
            side="right",
            padx=2,
            pady=10
        )

        self._small_button(
            controls,
            "Zoom −",
            self.zoom_out
        ).pack(
            side="right",
            padx=2,
            pady=10
        )

    # =========================================================
    # BUTTONS
    # =========================================================

    def _button(self, parent, text, command, primary=False, danger=False):

        if primary:
            bg = self.DARK
            fg = "#FFFFFF"
        elif danger:
            bg = "#FEF3F2"
            fg = self.DANGER
        else:
            bg = "#FFFFFF"
            fg = self.TEXT

        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            bg=bg,
            fg=fg,
            activebackground=self.BLUE_HOVER if primary else "#F2F4F7",
            activeforeground="#FFFFFF" if primary else self.TEXT,
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=10,
            pady=10
        )

        button.pack(
            fill="x",
            padx=12,
            pady=3
        )

        return button

    def _small_button(self, parent, text, command):

        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 9, "bold"),
            bg="#FFFFFF",
            fg=self.TEXT,
            activebackground="#F2F4F7",
            relief="solid",
            bd=1,
            cursor="hand2",
            width=max(5, len(text) + 1)
        )

    def _separator(self, parent):

        tk.Frame(
            parent,
            height=1,
            bg=self.BORDER
        ).pack(
            fill="x",
            padx=12,
            pady=10
        )

    # =========================================================
    # OPEN PDF
    # =========================================================

    def open_pdf(self):

        path = filedialog.askopenfilename(
            title="Open PDF",
            filetypes=[
                ("PDF files", "*.pdf"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:

            count = self.editor.load(path)

            self.current_page = 0
            self.selected_object = None
            self.selected_type = None

            self.history.clear()
            self.redo_stack.clear()

            self.file_label.config(
                text=os.path.basename(path)
            )

            self._render_page()

            self._status(
                f"Loaded {count} page(s): {os.path.basename(path)}"
            )

        except Exception as exc:

            messagebox.showerror(
                "Unable to Open PDF",
                str(exc)
            )

    # =========================================================
    # RENDER
    # =========================================================

    def _render_page(self):

        if self.editor.page_count == 0:
            self.canvas.delete("all")
            self.page_label.config(
                text="Page 0 / 0"
            )
            return

        try:

            pix = self.editor.render_page(
                self.current_page,
                self.preview_scale
            )

            image = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples
            )

            self.preview_photo = ImageTk.PhotoImage(image)

            self.canvas.delete("all")

            canvas_width = max(
                self.canvas.winfo_width(),
                600
            )

            canvas_height = max(
                self.canvas.winfo_height(),
                600
            )

            x = max(
                (canvas_width - image.width) // 2,
                20
            )

            y = max(
                (canvas_height - image.height) // 2,
                20
            )

            self.page_origin = (x, y)

            self.canvas.create_image(
                x,
                y,
                anchor="nw",
                image=self.preview_photo,
                tags="page"
            )

            self._draw_objects()

            self.canvas.configure(
                scrollregion=(
                    0,
                    0,
                    max(canvas_width, x + image.width + 40),
                    max(canvas_height, y + image.height + 40)
                )
            )

            self.page_label.config(
                text=f"Page {self.current_page + 1} / {self.editor.page_count}"
            )

            self.zoom_label.config(
                text=f"{int(self.preview_scale * 100)}% zoom"
            )

        except Exception as exc:

            messagebox.showerror(
                "Preview Error",
                str(exc)
            )

    def _fit_preview(self):

        if self.editor.page_count == 0:
            return

        # Do not continuously change zoom after user zooms.
        if getattr(self, "_fit_done", False):
            return

        try:

            page = self.editor.get_page(
                self.current_page
            )

            canvas_width = max(
                self.canvas.winfo_width() - 40,
                300
            )

            canvas_height = max(
                self.canvas.winfo_height() - 40,
                300
            )

            sx = canvas_width / page.rect.width
            sy = canvas_height / page.rect.height

            self.preview_scale = min(
                sx,
                sy,
                1.5
            )

            self._fit_done = True

            self._render_page()

        except Exception:
            pass

    # =========================================================
    # OBJECT RENDERING
    # =========================================================

    def _draw_objects(self):

        page = self.editor.get_page(
            self.current_page
        )

        origin_x, origin_y = self.page_origin

        scale = self.preview_scale

        for obj in self.editor.text_objects:

            if obj.page_index != self.current_page:
                continue

            x1 = origin_x + obj.x * scale
            y1 = origin_y + obj.y * scale

            x2 = origin_x + (obj.x + obj.width) * scale
            y2 = origin_y + (obj.y + obj.height) * scale

            selected = obj is self.selected_object

            fill = (
                ""
                if obj.background_color is None
                else self._rgb_to_hex(obj.background_color)
            )
            outline = self.BLUE if selected else "#98A2B3"

            self.canvas.create_rectangle(
                x1,
                y1,
                x2,
                y2,
                fill=fill,
                outline=outline,
                width=2 if selected else 1,
                tags=("object", f"text:{id(obj)}")
            )

            font_size = max(
                6,
                int(obj.font_size * scale)
            )

            font_weight = "bold" if obj.bold else "normal"
            font_slant = "italic" if obj.italic else "roman"

            self.canvas.create_text(
                x1 + 6,
                y1 + 5,
                anchor="nw",
                text=obj.text,
                fill=self._rgb_to_hex(obj.color),
                font=("Segoe UI", font_size, font_weight, font_slant),
                width=max(
                    20,
                    x2 - x1 - 12
                ),
                tags=("object", f"text:{id(obj)}")
            )

            if selected:
                self._draw_resize_handle(
                    x2,
                    y2
                )

        for obj in self.editor.signature_objects:

            if obj.page_index != self.current_page:
                continue

            if not os.path.isfile(obj.image_path):
                continue

            try:

                image = Image.open(
                    obj.image_path
                ).convert("RGBA")

                width = max(
                    10,
                    int(obj.width * scale)
                )

                height = max(
                    10,
                    int(obj.height * scale)
                )

                image.thumbnail(
                    (width, height),
                    Image.LANCZOS
                )

                photo = ImageTk.PhotoImage(image)

                # Keep references alive.
                if not hasattr(self, "_signature_photos"):
                    self._signature_photos = []

                self._signature_photos.append(photo)

                x1 = origin_x + obj.x * scale
                y1 = origin_y + obj.y * scale

                self.canvas.create_image(
                    x1,
                    y1,
                    anchor="nw",
                    image=photo,
                    tags=("object", f"signature:{id(obj)}")
                )

                x2 = x1 + width
                y2 = y1 + height

                if obj is self.selected_object:

                    self.canvas.create_rectangle(
                        x1,
                        y1,
                        x2,
                        y2,
                        outline=self.BLUE,
                        width=2,
                        tags=("object", f"signature:{id(obj)}")
                    )

                    self._draw_resize_handle(
                        x2,
                        y2
                    )

            except Exception:
                continue

    def _draw_resize_handle(self, x, y):

        size = 8

        self.canvas.create_rectangle(
            x - size,
            y - size,
            x + size,
            y + size,
            fill=self.BLUE,
            outline=self.BLUE,
            tags="resize_handle"
        )

    @staticmethod
    def _rgb_to_hex(color):
        """Convert the PDF color tuple used by TextObject to a Tk color."""
        channels = [
            min(255, max(0, round(channel * 255)))
            for channel in color
        ]
        return "#{:02x}{:02x}{:02x}".format(*channels)

    def _is_on_resize_handle(self, x, y, obj):
        """Return whether a canvas position is on an object's resize handle."""
        if obj is None or obj.page_index != self.current_page:
            return False

        origin_x, origin_y = self.page_origin
        handle_x = origin_x + (obj.x + obj.width) * self.preview_scale
        handle_y = origin_y + (obj.y + obj.height) * self.preview_scale
        hit_radius = 12

        return (
            abs(x - handle_x) <= hit_radius
            and abs(y - handle_y) <= hit_radius
        )

    # =========================================================
    # CANVAS INTERACTION
    # =========================================================

    def _canvas_to_pdf(self, x, y):

        origin_x, origin_y = self.page_origin

        pdf_x = (x - origin_x) / self.preview_scale
        pdf_y = (y - origin_y) / self.preview_scale

        return pdf_x, pdf_y

    def _find_object_at(self, x, y):

        pdf_x, pdf_y = self._canvas_to_pdf(
            x,
            y
        )

        # Reverse order means top-most object wins.
        objects = list(
            reversed(
                self.editor.get_objects_for_page(
                    self.current_page
                )
            )
        )

        for obj in objects:

            if (
                obj.x <= pdf_x <= obj.x + obj.width
                and
                obj.y <= pdf_y <= obj.y + obj.height
            ):
                return obj

        return None

    def on_canvas_press(self, event):

        if self.editor.page_count == 0:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        # Check the selected object's corner first. The handle overlaps the
        # object's bounding box, so regular hit testing would otherwise turn
        # every attempted resize into a move.
        if self._is_on_resize_handle(x, y, self.selected_object):
            obj = self.selected_object
            self.drag_mode = "resize"
        else:
            obj = self._find_object_at(
                x,
                y
            )
            self.drag_mode = "move" if obj else None

        if obj:

            self.selected_object = obj

            if isinstance(
                obj,
                TextObject
            ):
                self.selected_type = "text"
                self._load_text_properties(obj)

            elif isinstance(
                obj,
                SignatureObject
            ):
                self.selected_type = "signature"

            self.drag_start = (x, y)

            self.object_start = (
                obj.x,
                obj.y,
                obj.width,
                obj.height,
                getattr(obj, "font_size", None)
            )

            self._interaction_snapshot = self._snapshot()

            self._render_page()

        else:

            self.selected_object = None
            self.selected_type = None
            self.drag_mode = None
            self._interaction_snapshot = None
            self._render_page()

    def on_canvas_drag(self, event):

        if not self.selected_object:
            return

        if not self.drag_start:
            return

        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)

        dx = (
            x - self.drag_start[0]
        ) / self.preview_scale

        dy = (
            y - self.drag_start[1]
        ) / self.preview_scale

        if self.drag_mode == "resize":
            self._resize_selected_object(dx, dy)
        else:
            obj = self.selected_object
            page = self.editor.get_page(self.current_page)

            obj.x = min(
                max(0, self.object_start[0] + dx),
                max(0, page.rect.width - obj.width)
            )

            obj.y = min(
                max(0, self.object_start[1] + dy),
                max(0, page.rect.height - obj.height)
            )

        self._render_page()

    def _resize_selected_object(self, dx, dy):
        """Resize from the bottom-right corner while preserving proportions."""
        obj = self.selected_object
        if obj is None or not self.object_start:
            return

        start_x, start_y, start_width, start_height, start_font_size = (
            self.object_start
        )

        # Project the pointer movement onto the object's diagonal. This makes
        # horizontal, vertical, and diagonal drags all feel predictable while
        # retaining the object's aspect ratio.
        diagonal_squared = start_width ** 2 + start_height ** 2
        if diagonal_squared <= 0:
            return

        scale = 1 + (
            dx * start_width + dy * start_height
        ) / diagonal_squared

        min_scale = max(
            24 / start_width,
            18 / start_height
        )

        if isinstance(obj, TextObject) and start_font_size:
            min_scale = max(min_scale, 6 / start_font_size)

        page = self.editor.get_page(self.current_page)
        max_scale = min(
            (page.rect.width - start_x) / start_width,
            (page.rect.height - start_y) / start_height
        )

        scale = min(max(scale, min_scale), max_scale)

        obj.width = start_width * scale
        obj.height = start_height * scale

        if isinstance(obj, TextObject) and start_font_size:
            obj.font_size = min(120, max(6, start_font_size * scale))
            self.font_size_var.set(round(obj.font_size, 1))

    def on_canvas_release(self, event):

        if self.selected_object and self.drag_start:

            old = self.object_start

            new = (
                self.selected_object.x,
                self.selected_object.y,
                self.selected_object.width,
                self.selected_object.height
            )

            if old[:4] != new and self._interaction_snapshot is not None:
                self.history.append(self._interaction_snapshot)
                if len(self.history) > 50:
                    self.history.pop(0)
                self.redo_stack.clear()

        self.drag_start = None
        self.object_start = None
        self.drag_mode = None
        self._interaction_snapshot = None

    def on_canvas_double_click(self, event):

        obj = self._find_object_at(
            self.canvas.canvasx(event.x),
            self.canvas.canvasy(event.y)
        )

        if isinstance(
            obj,
            TextObject
        ):

            self.selected_object = obj

            self._load_text_properties(
                obj
            )

            self.text_entry.focus_set()

    # =========================================================
    # ADD TEXT
    # =========================================================

    def activate_add_text(self):

        if self.editor.page_count == 0:

            messagebox.showwarning(
                "No PDF",
                "Open a PDF document first."
            )

            return

        self._push_history()

        page = self.editor.get_page(
            self.current_page
        )

        obj = TextObject(
            text="Your text",
            x=50,
            y=50,
            width=min(
                250,
                page.rect.width - 100
            ),
            height=70,
            font_name="helv",
            font_size=16,
            color=(0.05, 0.05, 0.05),
            align=0,
            page_index=self.current_page
        )

        self.editor.add_text(
            obj
        )

        self.selected_object = obj
        self.selected_type = "text"

        self._load_text_properties(
            obj
        )

        self._render_page()

        self._status(
            "Text object added."
        )

    # =========================================================
    # TEXT PROPERTIES
    # =========================================================

    def _load_text_properties(self, obj):

        self.text_entry.delete(
            "1.0",
            "end"
        )

        self.text_entry.insert(
            "1.0",
            obj.text
        )

        self.font_size_var.set(
            int(obj.font_size)
        )

        self.bold_var.set(
            obj.bold
        )

        self.italic_var.set(
            obj.italic
        )

        self.background_transparent_var.set(
            obj.background_color is None
        )

        if obj.background_color is not None:
            self.text_background_color = obj.background_color

        if obj.align == 0:
            self.align_var.set("Left")
        elif obj.align == 1:
            self.align_var.set("Center")
        else:
            self.align_var.set("Right")

    def update_selected_text(self):

        if not isinstance(
            self.selected_object,
            TextObject
        ):
            return

        self.selected_object.text = (
            self.text_entry.get(
                "1.0",
                "end-1c"
            )
        )

        self._render_page()

    def update_selected_text_style(self):

        if not isinstance(
            self.selected_object,
            TextObject
        ):
            return

        obj = self.selected_object

        try:
            font_size = float(self.font_size_var.get())
        except (ValueError, tk.TclError):
            self.font_size_var.set(round(obj.font_size, 1))
            return

        obj.font_size = min(120, max(6, font_size))
        self.font_size_var.set(round(obj.font_size, 1))

        obj.bold = self.bold_var.get()
        obj.italic = self.italic_var.get()

        alignment = self.align_var.get()

        if alignment == "Left":
            obj.align = 0
        elif alignment == "Center":
            obj.align = 1
        else:
            obj.align = 2

        self._render_page()

    def decrease_selected_text_size(self):
        self._adjust_selected_text_size(-1)

    def increase_selected_text_size(self):
        self._adjust_selected_text_size(1)

    def _adjust_selected_text_size(self, amount):
        if not isinstance(self.selected_object, TextObject):
            return

        self.font_size_var.set(
            min(120, max(6, self.selected_object.font_size + amount))
        )
        self.update_selected_text_style()

    def choose_text_color(self):

        result = colorchooser.askcolor(
            title="Choose Text Color"
        )

        if not result or not result[1]:
            return

        self.text_color = result[1]

        rgb = result[0]

        if isinstance(
            self.selected_object,
            TextObject
        ):
            self.selected_object.color = (
                rgb[0] / 255,
                rgb[1] / 255,
                rgb[2] / 255,
            )

        self._render_page()

    def toggle_text_background(self):
        if not isinstance(self.selected_object, TextObject):
            return

        if self.background_transparent_var.get():
            self.selected_object.background_color = None
        else:
            self.selected_object.background_color = self.text_background_color

        self._render_page()

    def choose_text_background_color(self):
        if not isinstance(self.selected_object, TextObject):
            messagebox.showinfo(
                "Text Background",
                "Select a text object first."
            )
            return

        result = colorchooser.askcolor(
            color=self._rgb_to_hex(self.text_background_color),
            title="Choose Text Background Color"
        )

        if not result or not result[1]:
            return

        rgb = result[0]
        self.text_background_color = (
            rgb[0] / 255,
            rgb[1] / 255,
            rgb[2] / 255,
        )
        self.selected_object.background_color = self.text_background_color
        self.background_transparent_var.set(False)
        self._render_page()

    # =========================================================
    # SIGNATURE
    # =========================================================

    def activate_signature(self):

        self.upload_signature()

    def upload_signature(self):

        if self.editor.page_count == 0:

            messagebox.showwarning(
                "No PDF",
                "Open a PDF document first."
            )

            return

        path = filedialog.askopenfilename(
            title="Select Signature Image",
            filetypes=[
                (
                    "Image files",
                    "*.png *.jpg *.jpeg *.webp"
                ),
                (
                    "PNG files",
                    "*.png"
                ),
                (
                    "JPEG files",
                    "*.jpg *.jpeg"
                )
            ]
        )

        if not path:
            return

        try:

            image = Image.open(
                path
            )

            width_px, height_px = image.size

            page = self.editor.get_page(
                self.current_page
            )

            # Initial signature size.
            target_width = min(
                180,
                page.rect.width - 60
            )

            ratio = (
                height_px / width_px
                if width_px
                else 0.35
            )

            target_height = (
                target_width * ratio
            )

            obj = SignatureObject(
                image_path=path,
                x=50,
                y=50,
                width=target_width,
                height=target_height,
                page_index=self.current_page
            )

            self._push_history()

            self.editor.add_signature(
                obj
            )

            self.signature_path = path

            self.signature_label.config(
                text=os.path.basename(path)
            )

            self.selected_object = obj
            self.selected_type = "signature"

            self.signature_scale_var.set(
                1.0
            )

            self._render_page()

            self._status(
                "Signature added. Drag it to position."
            )

        except Exception as exc:

            messagebox.showerror(
                "Signature Error",
                str(exc)
            )

    def resize_selected_signature(self, value):

        if not isinstance(
            self.selected_object,
            SignatureObject
        ):
            return

        obj = self.selected_object

        try:
            scale = float(value)
        except ValueError:
            return

        if not hasattr(
            self,
            "_signature_base_size"
        ):
            self._signature_base_size = (
                obj.width,
                obj.height
            )

        base_width, base_height = (
            self._signature_base_size
        )

        obj.width = (
            base_width * scale
        )

        obj.height = (
            base_height * scale
        )

        self._render_page()

    # =========================================================
    # DELETE
    # =========================================================

    def delete_selected(self):

        if not self.selected_object:

            messagebox.showinfo(
                "Delete Object",
                "Select a text or signature object first."
            )

            return

        self._push_history()

        if isinstance(
            self.selected_object,
            TextObject
        ):
            self.editor.remove_text(
                self.selected_object
            )

        elif isinstance(
            self.selected_object,
            SignatureObject
        ):
            self.editor.remove_signature(
                self.selected_object
            )

        self.selected_object = None
        self.selected_type = None

        self._render_page()

        self._status(
            "Selected object deleted."
        )

    # =========================================================
    # PAGE NAVIGATION
    # =========================================================

    def previous_page(self):

        if self.current_page <= 0:
            return

        self.current_page -= 1

        self.selected_object = None
        self.selected_type = None

        self._render_page()

    def next_page(self):

        if self.current_page >= self.editor.page_count - 1:
            return

        self.current_page += 1

        self.selected_object = None
        self.selected_type = None

        self._render_page()

    # =========================================================
    # ZOOM
    # =========================================================

    def zoom_in(self):

        if self.editor.page_count == 0:
            return

        self.preview_scale = min(
            3.0,
            self.preview_scale + 0.15
        )

        self._render_page()

    def zoom_out(self):

        if self.editor.page_count == 0:
            return

        self.preview_scale = max(
            0.35,
            self.preview_scale - 0.15
        )

        self._render_page()

    # =========================================================
    # HISTORY
    # =========================================================

    def _snapshot(self):

        return {
            "texts": [
                obj.clone()
                for obj in self.editor.text_objects
            ],
            "signatures": [
                obj.clone()
                for obj in self.editor.signature_objects
            ]
        }

    def _restore(self, snapshot):

        self.editor.text_objects = [
            obj.clone()
            for obj in snapshot["texts"]
        ]

        self.editor.signature_objects = [
            obj.clone()
            for obj in snapshot["signatures"]
        ]

        self.selected_object = None
        self.selected_type = None

        self._render_page()

    def _push_history(self):

        self.history.append(
            self._snapshot()
        )

        if len(self.history) > 50:
            self.history.pop(0)

        self.redo_stack.clear()

    def undo(self):

        if not self.history:
            return

        self.redo_stack.append(
            self._snapshot()
        )

        snapshot = self.history.pop()

        self._restore(
            snapshot
        )

        self._status(
            "Undo completed."
        )

    def redo(self):

        if not self.redo_stack:
            return

        self.history.append(
            self._snapshot()
        )

        snapshot = self.redo_stack.pop()

        self._restore(
            snapshot
        )

        self._status(
            "Redo completed."
        )

    # =========================================================
    # EXPORT
    # =========================================================

    def export_pdf(self):

        if self.editor.page_count == 0:

            messagebox.showwarning(
                "No PDF",
                "Open a PDF document first."
            )

            return

        base_name = "edited_document.pdf"

        if self.editor.source_path:

            original = os.path.basename(
                self.editor.source_path
            )

            stem = os.path.splitext(
                original
            )[0]

            base_name = (
                f"{stem}_edited.pdf"
            )

        output_path = filedialog.asksaveasfilename(
            title="Export Edited PDF",
            defaultextension=".pdf",
            initialfile=base_name,
            filetypes=[
                (
                    "PDF files",
                    "*.pdf"
                )
            ]
        )

        if not output_path:
            return

        try:

            self.editor.export(
                output_path
            )

            self._status(
                f"Exported: {os.path.basename(output_path)}"
            )

            messagebox.showinfo(
                "Export Complete",
                "The edited PDF has been exported successfully."
            )

        except Exception as exc:

            messagebox.showerror(
                "Export Error",
                str(exc)
            )

    # =========================================================
    # STATUS
    # =========================================================

    def _status(self, message):

        if callable(
            self.status_callback
        ):
            self.status_callback(
                message
            )
