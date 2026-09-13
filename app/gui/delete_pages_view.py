from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

from app.services.pdf_service import PDFService
from app.services.preview_service import (
    PreviewService,
    PreviewServiceError,
)

from app.utils.dialogs import (
    ask_open_pdf,
    ask_save_pdf,
    show_error,
    show_info,
    show_warning,
)

from app.utils.image_utils import bytes_to_tk_image
from app.utils.background import run_in_background
from app.gui.theme import APP_BG, BORDER, INK, SURFACE, SURFACE_MUTED


class DeletePagesView(ttk.Frame):
    """Professional PDF page deletion workspace."""

    THUMBNAIL_WIDTH = 170
    THUMBNAIL_HEIGHT = 220
    CARD_WIDTH = 220

    def __init__(
        self,
        parent,
        status_callback=None,
    ) -> None:

        super().__init__(
            parent,
            style="Content.TFrame",
        )

        self.status_callback = status_callback

        self.pdf_service = PDFService()

        self.preview_service = PreviewService(
            dpi=90
        )

        self.pdf_path: str | None = None

        self.total_pages = 0

        self.selected_pages: set[int] = set()

        # IMPORTANT:
        # Keep Tkinter image references alive.
        self.thumbnail_images: list = []

        # Page widget references.
        self.page_widgets: list[tuple] = []

        # Empty-state widget.
        self.empty_label: ttk.Label | None = None

        # Rendering large documents one page at a time keeps the event loop
        # available for repainting, scrolling, and cancellation.
        self._thumbnail_render_token = 0
        self._thumbnail_render_index = 0
        self._thumbnail_columns = 1

        self._build_ui()

        self._show_empty_state()

        self._update_state()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self) -> None:

        self.columnconfigure(
            0,
            weight=1,
        )

        self.rowconfigure(
            1,
            weight=1,
        )

        # ----------------------------------------------------
        # Toolbar
        # ----------------------------------------------------

        toolbar = ttk.Frame(
            self,
            style="Content.TFrame",
        )

        toolbar.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=30,
            pady=(25, 12),
        )

        self.open_button = ttk.Button(
            toolbar,
            text="+  Open PDF",
            style="Primary.TButton",
            command=self.open_pdf,
        )

        self.open_button.pack(
            side="left",
            padx=(0, 8),
        )

        self.select_all_button = ttk.Button(
            toolbar,
            text="Select All",
            style="Secondary.TButton",
            command=self.select_all,
        )

        self.select_all_button.pack(
            side="left",
            padx=4,
        )

        self.clear_selection_button = ttk.Button(
            toolbar,
            text="Clear Selection",
            style="Secondary.TButton",
            command=self.clear_selection,
        )

        self.clear_selection_button.pack(
            side="left",
            padx=4,
        )

        self.close_button = ttk.Button(
            toolbar,
            text="Close PDF",
            style="Secondary.TButton",
            command=self.close_pdf,
        )

        self.close_button.pack(
            side="right",
        )

        # ----------------------------------------------------
        # Preview Container
        # ----------------------------------------------------

        preview_container = ttk.Frame(
            self,
            style="Content.TFrame",
        )

        preview_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=30,
            pady=(0, 10),
        )

        preview_container.columnconfigure(
            0,
            weight=1,
        )

        preview_container.rowconfigure(
            0,
            weight=1,
        )

        # ----------------------------------------------------
        # Canvas
        # ----------------------------------------------------

        self.canvas = tk.Canvas(
            preview_container,
            background=APP_BG,
            highlightthickness=0,
            bd=0,
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar = ttk.Scrollbar(
            preview_container,
            orient="vertical",
            command=self.canvas.yview,
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        # ----------------------------------------------------
        # Thumbnail Frame
        # ----------------------------------------------------

        self.thumbnail_frame = ttk.Frame(
            self.canvas,
            style="Content.TFrame",
        )

        self.canvas_window = (
            self.canvas.create_window(
                (0, 0),
                window=self.thumbnail_frame,
                anchor="nw",
            )
        )

        self.thumbnail_frame.bind(
            "<Configure>",
            self._update_scroll_region,
        )

        self.canvas.bind(
            "<Configure>",
            self._on_canvas_resize,
        )

        self.canvas.bind(
            "<MouseWheel>",
            self._on_mousewheel,
        )

        self.canvas.bind(
            "<Button-4>",
            self._on_mousewheel,
        )

        self.canvas.bind(
            "<Button-5>",
            self._on_mousewheel,
        )

        # ----------------------------------------------------
        # Bottom Bar
        # ----------------------------------------------------

        bottom = ttk.Frame(
            self,
            style="Content.TFrame",
        )

        bottom.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=30,
            pady=(0, 25),
        )

        bottom.columnconfigure(
            0,
            weight=1,
        )

        self.summary_label = ttk.Label(
            bottom,
            text="No PDF loaded",
            style="CardText.TLabel",
        )

        self.summary_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.delete_button = ttk.Button(
            bottom,
            text="Delete Selected & Save  →",
            style="Primary.TButton",
            command=self.delete_selected,
        )

        self.delete_button.grid(
            row=0,
            column=1,
            sticky="e",
        )

    # ========================================================
    # OPEN PDF
    # ========================================================

    def open_pdf(self) -> None:

        selected = ask_open_pdf(
            self,
            multiple=False,
        )

        if not selected:
            return

        self._load_pdf(
            str(selected)
        )

    # ========================================================
    # LOAD PDF
    # ========================================================

    def _load_pdf(
        self,
        pdf_path: str,
    ) -> None:

        self._set_status(
            "Loading PDF preview..."
        )

        self.update_idletasks()

        try:
            valid, result = (
                self.pdf_service.get_page_count(
                    pdf_path
                )
            )

            if not valid:

                show_error(
                    self,
                    "Unable to Open PDF",
                    str(result),
                )

                self._set_status(
                    "Unable to open PDF."
                )

                return

            page_count = int(result)

            if page_count <= 0:

                show_error(
                    self,
                    "Invalid PDF",
                    "The PDF does not contain any pages.",
                )

                return

            # ------------------------------------------------
            # Clean previous document first.
            # ------------------------------------------------

            self._clear_thumbnail_widgets()

            self.pdf_path = pdf_path
            self.total_pages = page_count
            self.selected_pages.clear()

            # ------------------------------------------------
            # Render thumbnails.
            # ------------------------------------------------

            self._render_thumbnails()

            self._update_state()

            self._set_status(
                f"Loaded {self.total_pages} page(s)."
            )

        except Exception as exc:

            show_error(
                self,
                "Preview Error",
                f"Unable to load PDF:\n\n{exc}",
            )

            self._set_status(
                "PDF preview failed."
            )

    # ========================================================
    # RENDER THUMBNAILS
    # ========================================================

    def _render_thumbnails(self) -> None:

        if not self.pdf_path:
            return

        self._hide_empty_state()

        self.thumbnail_images.clear()
        self.page_widgets.clear()

        self._thumbnail_render_token += 1
        self._thumbnail_render_index = 0
        self._thumbnail_columns = self._calculate_columns()
        self._render_next_thumbnail(self._thumbnail_render_token)

    def _render_next_thumbnail(self, token: int) -> None:
        """Render one thumbnail per UI turn instead of blocking on all pages."""
        if (
            token != self._thumbnail_render_token
            or not self.pdf_path
            or self._thumbnail_render_index >= self.total_pages
        ):
            return

        page_index = self._thumbnail_render_index
        columns = self._thumbnail_columns
        row = page_index // columns
        column = page_index % columns

        try:

            preview = (
                self.preview_service.render_page(
                    self.pdf_path,
                    page_index,
                )
            )

            image = bytes_to_tk_image(
                preview.image_data,
                max_width=self.THUMBNAIL_WIDTH,
                max_height=self.THUMBNAIL_HEIGHT,
            )

                # IMPORTANT:
                # Keep reference alive.
            self.thumbnail_images.append(image)

            page_frame = tk.Frame(
                    self.thumbnail_frame,
                    background=SURFACE,
                    highlightthickness=1,
                    highlightbackground=BORDER,
                    highlightcolor=INK,
                    bd=0,
                    cursor="hand2",
                )

            page_frame.grid(
                    row=row,
                    column=column,
                    padx=12,
                    pady=12,
                    sticky="n",
                )

            image_label = tk.Label(
                    page_frame,
                    image=image,
                    background=SURFACE,
                    bd=0,
                    cursor="hand2",
                )

            image_label.pack(
                    padx=10,
                    pady=(10, 6),
                )

            number_label = tk.Label(
                    page_frame,
                    text=f"Page {page_index + 1}",
                    background=SURFACE,
                    foreground="#65707B",
                    font=(
                        "Segoe UI",
                        9,
                        "bold",
                    ),
                    cursor="hand2",
                )

            number_label.pack(
                    pady=(0, 10),
                )

            widgets = (page_frame, image_label, number_label)

            self.page_widgets.append(widgets)

                # ------------------------------------------------
                # Bind click events.
                # ------------------------------------------------

            for widget in widgets:

                widget.bind(
                        "<Button-1>",
                        lambda event,
                        index=page_index:
                        self.toggle_page(index),
                    )

        except PreviewServiceError as exc:

            self._create_preview_error(
                    page_index,
                    row,
                    column,
                    str(exc),
                )

        except Exception:

            self._create_preview_error(
                    page_index,
                    row,
                    column,
                    "Unable to render preview.",
                )

        self._thumbnail_render_index += 1
        self._update_page_visuals()
        self.after(1, self._update_scroll_region)

        if self._thumbnail_render_index < self.total_pages:
            self.after(1, self._render_next_thumbnail, token)
        else:
            self._set_status(f"Loaded {self.total_pages} page(s).")

    # ========================================================
    # PREVIEW ERROR CARD
    # ========================================================

    def _create_preview_error(
        self,
        page_index: int,
        row: int,
        column: int,
        message: str,
    ) -> None:

        page_frame = tk.Frame(
            self.thumbnail_frame,
            background=SURFACE,
            highlightthickness=1,
            highlightbackground=BORDER,
        )

        page_frame.grid(
            row=row,
            column=column,
            padx=12,
            pady=12,
            sticky="n",
        )

        ttk.Label(
            page_frame,
            text=f"Page {page_index + 1}",
            style="CardTitle.TLabel",
        ).pack(
            padx=35,
            pady=(35, 8),
        )

        ttk.Label(
            page_frame,
            text="Preview unavailable",
            style="CardText.TLabel",
        ).pack(
            padx=20,
            pady=(0, 35),
        )

        # Keep page indexes aligned with their widget slots even when one
        # thumbnail cannot be rendered.
        self.page_widgets.append(())

    # ========================================================
    # PAGE SELECTION
    # ========================================================

    def toggle_page(
        self,
        page_index: int,
    ) -> None:

        if page_index < 0:
            return

        if page_index >= self.total_pages:
            return

        if page_index in self.selected_pages:

            self.selected_pages.remove(
                page_index
            )

        else:

            self.selected_pages.add(
                page_index
            )

        self._update_page_visuals()

        self._update_state()

        self._set_status(
            self._selection_status()
        )

    # ========================================================
    # SELECT ALL
    # ========================================================

    def select_all(self) -> None:

        if not self.pdf_path:
            return

        self.selected_pages = set(
            range(self.total_pages)
        )

        self._update_page_visuals()

        self._update_state()

        self._set_status(
            f"Selected all {self.total_pages} pages."
        )

    # ========================================================
    # CLEAR SELECTION
    # ========================================================

    def clear_selection(self) -> None:

        self.selected_pages.clear()

        self._update_page_visuals()

        self._update_state()

        self._set_status(
            "Page selection cleared."
        )

    # ========================================================
    # DELETE SELECTED
    # ========================================================

    def delete_selected(self) -> None:

        if not self.pdf_path:

            show_warning(
                self,
                "No PDF Loaded",
                "Please open a PDF first.",
            )

            return

        if not self.selected_pages:

            show_warning(
                self,
                "No Pages Selected",
                "Please select at least one page to delete.",
            )

            return

        if len(self.selected_pages) >= self.total_pages:

            show_warning(
                self,
                "Invalid Selection",
                (
                    "You cannot delete all pages.\n\n"
                    "At least one page must remain."
                ),
            )

            return

        selected_numbers = [
            index + 1
            for index in sorted(
                self.selected_pages
            )
        ]

        preview = ", ".join(
            str(number)
            for number in selected_numbers[:20]
        )

        if len(selected_numbers) > 20:

            preview += (
                f", ... "
                f"(+{len(selected_numbers) - 20})"
            )

        confirmed = messagebox.askyesno(
            "Delete Pages",
            (
                f"Delete {len(selected_numbers)} page(s)?\n\n"
                f"Pages: {preview}"
            ),
            parent=self,
        )

        if not confirmed:
            return

        output_file = ask_save_pdf(
            self,
            initial_name="edited_document.pdf",
        )

        if not output_file:
            return

        if not output_file.lower().endswith(
            ".pdf"
        ):

            output_file += ".pdf"

        if self._same_as_source(
            output_file
        ):

            show_error(
                self,
                "Invalid Output",
                (
                    "The output file cannot be "
                    "the source PDF."
                ),
            )

            return

        self.delete_button.config(state="disabled")
        self._set_status("Deleting selected pages in the background...")

        def completed(result) -> None:
            success, message = result
            if not success:
                show_error(self, "Delete Pages Failed", message)
                self._set_status("Delete operation failed.")
                return
            show_info(self, "Operation Complete", "Selected pages were removed successfully.\n\n" f"Saved to:\n{output_file}")
            self._set_status("Pages deleted successfully.")
            self._load_pdf(output_file)

        def failed(exc: Exception) -> None:
            show_error(self, "Delete Pages Failed", str(exc))
            self._set_status("Delete operation failed.")

        run_in_background(
            self,
            lambda: self.pdf_service.delete_pages(self.pdf_path, list(self.selected_pages), output_file),
            completed,
            failed,
            lambda: self.delete_button.config(state="normal"),
        )

    # ========================================================
    # CLOSE PDF
    # ========================================================

    def close_pdf(self) -> None:

        self._thumbnail_render_token += 1
        self.preview_service.close()

        self._clear_thumbnail_widgets()

        self.pdf_path = None

        self.total_pages = 0

        self.selected_pages.clear()

        self._show_empty_state()

        self._update_state()

        self._set_status(
            "PDF closed."
        )

    # ========================================================
    # PAGE VISUALS
    # ========================================================

    def _update_page_visuals(self) -> None:

        for page_index, widgets in enumerate(
            self.page_widgets
        ):

            if not widgets:
                continue

            frame = widgets[0]

            # Make sure widget still exists.
            try:
                if not frame.winfo_exists():
                    continue
            except tk.TclError:
                continue

            if page_index in self.selected_pages:

                frame.configure(
                    background="#e9edf3",
                    highlightbackground="#17191f",
                    highlightthickness=2,
                )

                for widget in widgets[1:]:

                    try:

                        widget.configure(
                            background="#e9edf3"
                        )

                    except tk.TclError:
                        pass

            else:

                frame.configure(
                    background="#ffffff",
                    highlightbackground="#dfe2e7",
                    highlightthickness=1,
                )

                for widget in widgets[1:]:

                    try:

                        widget.configure(
                            background="#ffffff"
                        )

                    except tk.TclError:
                        pass

    # ========================================================
    # EMPTY STATE
    # ========================================================

    def _show_empty_state(self) -> None:

        # Avoid duplicate empty-state labels.
        self._hide_empty_state()

        self.empty_label = ttk.Label(
            self.thumbnail_frame,
            text=(
                "No PDF loaded\n\n"
                "Open a PDF to preview and select pages."
            ),
            style="CardText.TLabel",
            justify="center",
        )

        self.empty_label.grid(
            row=0,
            column=0,
            padx=100,
            pady=120,
        )

    def _hide_empty_state(self) -> None:

        if self.empty_label is None:
            return

        try:

            if self.empty_label.winfo_exists():

                self.empty_label.grid_forget()

                self.empty_label.destroy()

        except tk.TclError:
            pass

        finally:

            self.empty_label = None

    # ========================================================
    # CLEAR THUMBNAILS
    # ========================================================

    def _clear_thumbnail_widgets(self) -> None:

        # ----------------------------------------------------
        # IMPORTANT:
        # Remove empty state first.
        # ----------------------------------------------------

        self._hide_empty_state()

        # ----------------------------------------------------
        # Destroy page widgets.
        # ----------------------------------------------------

        for widget in (
            self.thumbnail_frame.winfo_children()
        ):

            try:
                widget.destroy()

            except tk.TclError:
                pass

        # ----------------------------------------------------
        # Clear Python references.
        # ----------------------------------------------------

        self.page_widgets.clear()

        self.thumbnail_images.clear()

        # ----------------------------------------------------
        # Reset scroll position.
        # ----------------------------------------------------

        try:

            self.canvas.yview_moveto(
                0
            )

        except tk.TclError:
            pass

    # ========================================================
    # LAYOUT
    # ========================================================

    def _calculate_columns(self) -> int:

        width = self.canvas.winfo_width()

        if width <= 1:
            return 3

        columns = max(
            1,
            width // self.CARD_WIDTH,
        )

        return min(
            columns,
            6,
        )

    def _on_canvas_resize(
        self,
        event=None,
    ) -> None:

        if not self.page_widgets:
            return

        columns = self._calculate_columns()

        self._reposition_existing_pages(
            columns
        )

    def _reposition_existing_pages(
        self,
        columns: int,
    ) -> None:

        for index, widgets in enumerate(
            self.page_widgets
        ):

            if not widgets:
                continue

            frame = widgets[0]

            try:

                if not frame.winfo_exists():
                    continue

                row = index // columns
                column = index % columns

                frame.grid_configure(
                    row=row,
                    column=column,
                )

            except tk.TclError:
                continue

    # ========================================================
    # SCROLL
    # ========================================================

    def _update_scroll_region(
        self,
        event=None,
    ) -> None:

        try:

            self.canvas.configure(
                scrollregion=self.canvas.bbox(
                    "all"
                )
            )

        except tk.TclError:
            pass

    def _on_mousewheel(
        self,
        event,
    ) -> None:

        try:

            if event.num == 4:

                self.canvas.yview_scroll(
                    -3,
                    "units",
                )

            elif event.num == 5:

                self.canvas.yview_scroll(
                    3,
                    "units",
                )

            else:

                delta = int(
                    -1 * (event.delta / 120)
                )

                self.canvas.yview_scroll(
                    delta,
                    "units",
                )

        except tk.TclError:
            pass

    # ========================================================
    # STATE
    # ========================================================

    def _update_state(self) -> None:

        has_pdf = (
            self.pdf_path is not None
            and self.total_pages > 0
        )

        has_selection = bool(
            self.selected_pages
        )

        self.select_all_button.config(
            state=(
                "normal"
                if has_pdf
                else "disabled"
            )
        )

        self.clear_selection_button.config(
            state=(
                "normal"
                if has_selection
                else "disabled"
            )
        )

        self.close_button.config(
            state=(
                "normal"
                if has_pdf
                else "disabled"
            )
        )

        self.delete_button.config(
            state=(
                "normal"
                if (
                    has_pdf
                    and has_selection
                    and len(self.selected_pages)
                    < self.total_pages
                )
                else "disabled"
            )
        )

        if not has_pdf:

            self.summary_label.config(
                text="No PDF loaded"
            )

            return

        selected = len(
            self.selected_pages
        )

        remaining = (
            self.total_pages - selected
        )

        self.summary_label.config(
            text=(
                f"{self.total_pages} pages  •  "
                f"{selected} selected  •  "
                f"{remaining} remaining"
            )
        )

    # ========================================================
    # HELPERS
    # ========================================================

    def _selection_status(self) -> str:

        count = len(
            self.selected_pages
        )

        if count == 0:
            return "No pages selected."

        return f"{count} page(s) selected."

    def _same_as_source(
        self,
        output_file: str,
    ) -> bool:

        if not self.pdf_path:
            return False

        return (
            Path(output_file).resolve()
            == Path(self.pdf_path).resolve()
        )

    def _set_status(
        self,
        message: str,
    ) -> None:

        if self.status_callback:

            self.status_callback(
                message
            )
