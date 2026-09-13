from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from app.services.pdf_service import PDFService
from app.utils.dialogs import (
    ask_open_pdf,
    ask_save_pdf,
    ask_confirmation,
    show_error,
    show_info,
    show_warning,
)
from app.utils.file_utils import (
    get_file_size,
    format_file_size,
    get_filename,
)
from app.utils.validation import validate_merge_list
from app.utils.background import run_in_background


class MergeView(ttk.Frame):
    """Professional PDF merge workspace."""

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

        self.pdf_files: list[str] = []

        self._build_ui()
        self._update_ui_state()

    # ========================================================
    # UI
    # ========================================================

    def _build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        description = ttk.Label(
            self,
            text=(
                "Add PDF documents, arrange them in the desired order, "
                "then merge them into one PDF file."
            ),
            style="CardText.TLabel",
            wraplength=800,
        )

        description.grid(
            row=0,
            column=0,
            sticky="w",
            padx=30,
            pady=(26, 18),
        )

        # ----------------------------------------------------
        # Main workspace
        # ----------------------------------------------------

        workspace = ttk.Frame(
            self,
            style="Content.TFrame",
        )

        workspace.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=30,
            pady=(0, 20),
        )

        workspace.columnconfigure(0, weight=1)
        workspace.rowconfigure(1, weight=1)

        # ----------------------------------------------------
        # Toolbar
        # ----------------------------------------------------

        toolbar = ttk.Frame(
            workspace,
            style="Content.TFrame",
        )

        toolbar.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(0, 10),
        )

        self.add_button = ttk.Button(
            toolbar,
            text="+  Add PDF",
            style="Primary.TButton",
            command=self.add_pdfs,
        )

        self.add_button.pack(
            side="left",
            padx=(0, 8),
        )

        self.remove_button = ttk.Button(
            toolbar,
            text="Remove",
            style="Secondary.TButton",
            command=self.remove_selected,
        )

        self.remove_button.pack(
            side="left",
            padx=4,
        )

        self.move_up_button = ttk.Button(
            toolbar,
            text="↑  Move Up",
            style="Secondary.TButton",
            command=self.move_up,
        )

        self.move_up_button.pack(
            side="left",
            padx=4,
        )

        self.move_down_button = ttk.Button(
            toolbar,
            text="↓  Move Down",
            style="Secondary.TButton",
            command=self.move_down,
        )

        self.move_down_button.pack(
            side="left",
            padx=4,
        )

        self.clear_button = ttk.Button(
            toolbar,
            text="Clear All",
            style="Secondary.TButton",
            command=self.clear_all,
        )

        self.clear_button.pack(
            side="right",
        )

        # ----------------------------------------------------
        # File list
        # ----------------------------------------------------

        list_container = ttk.Frame(
            workspace,
            style="Content.TFrame",
        )

        list_container.grid(
            row=1,
            column=0,
            sticky="nsew",
        )

        list_container.columnconfigure(0, weight=1)
        list_container.rowconfigure(0, weight=1)

        columns = (
            "number",
            "filename",
            "size",
        )

        self.tree = ttk.Treeview(
            list_container,
            columns=columns,
            show="headings",
            selectmode="extended",
        )

        self.tree.heading(
            "number",
            text="#",
        )

        self.tree.heading(
            "filename",
            text="PDF Document",
        )

        self.tree.heading(
            "size",
            text="Size",
        )

        self.tree.column(
            "number",
            width=55,
            anchor="center",
            stretch=False,
        )

        self.tree.column(
            "filename",
            width=500,
            anchor="w",
        )

        self.tree.column(
            "size",
            width=120,
            anchor="e",
            stretch=False,
        )

        scrollbar = ttk.Scrollbar(
            list_container,
            orient="vertical",
            command=self.tree.yview,
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.tree.bind(
            "<<TreeviewSelect>>",
            self._on_selection_changed,
        )

        # ----------------------------------------------------
        # Empty state
        # ----------------------------------------------------

        self.empty_label = ttk.Label(
            list_container,
            text=(
                "No PDF files added yet.\n\n"
                "Click  + Add PDF  to select documents."
            ),
            style="CardText.TLabel",
            justify="center",
        )

        # ----------------------------------------------------
        # Bottom bar
        # ----------------------------------------------------

        bottom = ttk.Frame(
            workspace,
            style="Content.TFrame",
        )

        bottom.grid(
            row=2,
            column=0,
            sticky="ew",
            pady=(16, 0),
        )

        bottom.columnconfigure(
            0,
            weight=1,
        )

        self.summary_label = ttk.Label(
            bottom,
            text="0 PDF files",
            style="CardText.TLabel",
        )

        self.summary_label.grid(
            row=0,
            column=0,
            sticky="w",
        )

        self.merge_button = ttk.Button(
            bottom,
            text="Merge & Save  →",
            style="Primary.TButton",
            command=self.merge_pdfs,
        )

        self.merge_button.grid(
            row=0,
            column=1,
            sticky="e",
            padx=(10, 0),
        )

    # ========================================================
    # ADD
    # ========================================================

    def add_pdfs(self) -> None:
        """Add PDF files to the merge queue."""

        selected = ask_open_pdf(
            self,
            multiple=True,
        )

        if not selected:
            return

        added = 0
        skipped = []

        for file_path in selected:

            if file_path in self.pdf_files:
                skipped.append(
                    f"{get_filename(file_path)} (duplicate)"
                )
                continue

            valid, message = (
                self.pdf_service.validate_pdf(
                    file_path
                )
            )

            if not valid:
                skipped.append(
                    f"{get_filename(file_path)} "
                    f"({message})"
                )
                continue

            self.pdf_files.append(file_path)
            added += 1

        self._refresh_list()
        self._update_ui_state()

        if added:
            self._set_status(
                f"{added} PDF file(s) added."
            )

        if skipped:
            message = (
                f"{len(skipped)} file(s) were not added:\n\n"
                + "\n".join(skipped[:8])
            )

            if len(skipped) > 8:
                message += (
                    f"\n\n...and "
                    f"{len(skipped) - 8} more."
                )

            show_warning(
                self,
                "Some Files Were Skipped",
                message,
            )

    # ========================================================
    # REMOVE
    # ========================================================

    def remove_selected(self) -> None:
        """Remove selected files."""

        selected = self.tree.selection()

        if not selected:
            return

        indexes = sorted(
            (
                self.tree.index(item)
                for item in selected
            ),
            reverse=True,
        )

        for index in indexes:
            del self.pdf_files[index]

        self._refresh_list()
        self._update_ui_state()

        self._set_status(
            "Selected PDF file(s) removed."
        )

    # ========================================================
    # MOVE UP
    # ========================================================

    def move_up(self) -> None:
        """Move selected file up."""

        selected = self.tree.selection()

        if len(selected) != 1:
            return

        item = selected[0]
        index = self.tree.index(item)

        if index <= 0:
            return

        self.pdf_files[index - 1], self.pdf_files[index] = (
            self.pdf_files[index],
            self.pdf_files[index - 1],
        )

        self._refresh_list()

        self.tree.selection_set(
            self.tree.get_children()[index - 1]
        )

        self._set_status(
            "PDF order updated."
        )

    # ========================================================
    # MOVE DOWN
    # ========================================================

    def move_down(self) -> None:
        """Move selected file down."""

        selected = self.tree.selection()

        if len(selected) != 1:
            return

        item = selected[0]
        index = self.tree.index(item)

        if index >= len(self.pdf_files) - 1:
            return

        self.pdf_files[index + 1], self.pdf_files[index] = (
            self.pdf_files[index],
            self.pdf_files[index + 1],
        )

        self._refresh_list()

        self.tree.selection_set(
            self.tree.get_children()[index + 1]
        )

        self._set_status(
            "PDF order updated."
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_all(self) -> None:
        """Clear all PDF files."""

        if not self.pdf_files:
            return

        confirmed = ask_confirmation(
            self,
            "Clear PDF List",
            "Remove all PDF files from the merge list?",
        )

        if not confirmed:
            return

        self.pdf_files.clear()

        self._refresh_list()
        self._update_ui_state()

        self._set_status(
            "PDF list cleared."
        )

    # ========================================================
    # MERGE
    # ========================================================

    def merge_pdfs(self) -> None:
        """Merge selected PDF files."""

        valid, message = validate_merge_list(
            self.pdf_files
        )

        if not valid:
            show_warning(
                self,
                "Cannot Merge PDFs",
                message,
            )
            return

        output_file = ask_save_pdf(
            self,
            initial_name="merged_document.pdf",
        )

        if not output_file:
            return

        # Ensure .pdf extension.
        if not output_file.lower().endswith(".pdf"):
            output_file += ".pdf"

        # Prevent accidental overwrite confirmation.
        if self._same_as_input(output_file):
            show_error(
                self,
                "Invalid Output",
                (
                    "The output file cannot be "
                    "one of the source PDF files."
                ),
            )
            return

        self.merge_button.config(state="disabled")
        self._set_status("Merging PDF files in the background...")

        def completed(result) -> None:
            success, message = result
            if not success:
                show_error(self, "Merge Failed", message)
                self._set_status("Merge failed.")
                return
            self._set_status("PDF files merged successfully.")
            show_info(self, "Merge Complete", "Your PDF files have been merged successfully.\n\n" f"Saved to:\n{output_file}")

        def failed(exc: Exception) -> None:
            show_error(self, "Merge Failed", str(exc))
            self._set_status("Merge failed.")

        run_in_background(
            self,
            lambda: self.pdf_service.merge_pdfs(list(self.pdf_files), output_file),
            completed,
            failed,
            lambda: self.merge_button.config(state="normal"),
        )

    # ========================================================
    # LIST
    # ========================================================

    def _refresh_list(self) -> None:
        """Refresh treeview."""

        for item in self.tree.get_children():
            self.tree.delete(item)

        for index, file_path in enumerate(
            self.pdf_files,
            start=1,
        ):
            try:
                size = format_file_size(
                    get_file_size(file_path)
                )
            except OSError:
                size = "Unknown"

            self.tree.insert(
                "",
                "end",
                values=(
                    index,
                    get_filename(file_path),
                    size,
                ),
            )

        if self.pdf_files:
            self.empty_label.place_forget()

        else:
            self.empty_label.place(
                relx=0.5,
                rely=0.5,
                anchor="center",
            )

        self.summary_label.config(
            text=self._summary_text()
        )

    def _summary_text(self) -> str:
        count = len(self.pdf_files)

        if count == 0:
            return "0 PDF files"

        if count == 1:
            return "1 PDF file"

        return f"{count} PDF files"

    # ========================================================
    # UI STATE
    # ========================================================

    def _update_ui_state(self) -> None:
        count = len(self.pdf_files)

        selected = self.tree.selection()

        # Remove
        self.remove_button.config(
            state=(
                "normal"
                if selected
                else "disabled"
            )
        )

        # Move
        can_move = len(selected) == 1

        self.move_up_button.config(
            state=(
                "normal"
                if can_move
                else "disabled"
            )
        )

        self.move_down_button.config(
            state=(
                "normal"
                if can_move
                else "disabled"
            )
        )

        # Clear
        self.clear_button.config(
            state=(
                "normal"
                if count
                else "disabled"
            )
        )

        # Merge
        self.merge_button.config(
            state=(
                "normal"
                if count >= 2
                else "disabled"
            )
        )

    def _on_selection_changed(
        self,
        event=None,
    ) -> None:
        self._update_ui_state()

    # ========================================================
    # HELPERS
    # ========================================================

    def _same_as_input(
        self,
        output_file: str,
    ) -> bool:

        from pathlib import Path

        output_path = Path(
            output_file
        ).resolve()

        return any(
            Path(file_path).resolve()
            == output_path
            for file_path in self.pdf_files
        )

    def _set_status(
        self,
        message: str,
    ) -> None:

        if self.status_callback:
            self.status_callback(message)
