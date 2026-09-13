"""
Encrypt / Decrypt View
----------------------

Premium Tkinter interface for:

- Encrypt PDF
- Decrypt PDF
- Remove PDF password
- Detect encrypted PDFs
- Output configuration
"""

import os
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from app.services.security_service import (
    SecurityService,
    PDFSecurityError,
)
from app.gui.theme import ACCENT, APP_BG, BORDER, INK, MUTED, NAVY, SURFACE


class SecurityView(tk.Frame):
    """
    Encrypt / Decrypt PDF interface.
    """

    BG = APP_BG
    CARD = SURFACE
    DARK = NAVY
    TEXT = INK
    MUTED = MUTED
    BORDER = BORDER
    ACCENT = NAVY
    BLUE = ACCENT
    SUCCESS = "#15803D"
    ERROR = "#DC2626"
    WARNING = "#B45309"

    def __init__(
        self,
        parent,
        content=None,
        status_callback=None,
        **kwargs
    ):
        super().__init__(
            parent,
            bg=self.BG,
            **kwargs
        )

        self.parent = parent
        self.status_callback = status_callback

        self.security_service = SecurityService()

        self.input_path = None
        self.output_path = None
        self.pdf_encrypted = False

        self.action_var = tk.StringVar(
            value="encrypt"
        )

        self.password_visible = False

        self._build_ui()

    # ==========================================================
    # BUILD UI
    # ==========================================================

    def _build_ui(self):
        """
        Build complete interface.
        """

        self.grid_rowconfigure(
            0,
            weight=1
        )
        self.grid_columnconfigure(
            0,
            weight=1
        )

        # ------------------------------------------------------
        # Main scroll container
        # ------------------------------------------------------

        outer = tk.Frame(
            self,
            bg=self.BG
        )
        outer.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        outer.grid_rowconfigure(
            0,
            weight=1
        )
        outer.grid_columnconfigure(
            0,
            weight=1
        )

        self.canvas = tk.Canvas(
            outer,
            bg=self.BG,
            highlightthickness=0,
            bd=0
        )
        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar = tk.Scrollbar(
            outer,
            orient="vertical",
            command=self.canvas.yview
        )
        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )

        self.canvas.configure(
            yscrollcommand=scrollbar.set
        )

        self.content_frame = tk.Frame(
            self.canvas,
            bg=self.BG
        )

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.content_frame,
            anchor="nw"
        )

        self.content_frame.bind(
            "<Configure>",
            self._update_scroll_region
        )

        self.canvas.bind(
            "<Configure>",
            self._resize_canvas_content
        )

        self.canvas.bind_all(
            "<MouseWheel>",
            self._on_mousewheel
        )

        # ------------------------------------------------------
        # Content
        # ------------------------------------------------------

        self._build_content()

    def _build_content(self):
        """Build a compact, task-oriented security workspace."""

        container = tk.Frame(
            self.content_frame,
            bg=self.BG
        )
        container.pack(
            fill="both",
            expand=True,
            padx=42,
            pady=26
        )

        context = tk.Frame(container, bg=self.BG)
        context.pack(fill="x", pady=(0, 16))
        tk.Label(
            context,
            text="DOCUMENT SECURITY WORKFLOW",
            bg=self.BG,
            fg=self.ACCENT,
            font=("Segoe UI Semibold", 8)
        ).pack(anchor="w")
        tk.Label(
            context,
            text="Select a document, choose an action, then configure its protection.",
            bg=self.BG,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(anchor="w", pady=(4, 0))

        overview = tk.Frame(container, bg=self.BG)
        overview.pack(fill="x", pady=(0, 14))
        overview.grid_columnconfigure(0, weight=11, uniform="security")
        overview.grid_columnconfigure(1, weight=9, uniform="security")
        source_column = tk.Frame(overview, bg=self.BG)
        source_column.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        action_column = tk.Frame(overview, bg=self.BG)
        action_column.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self._build_source_card(source_column)
        self._build_action_card(action_column)

        settings = tk.Frame(container, bg=self.BG)
        settings.pack(fill="x")
        settings.grid_columnconfigure(0, weight=1, uniform="security")
        settings.grid_columnconfigure(1, weight=1, uniform="security")
        password_column = tk.Frame(settings, bg=self.BG)
        password_column.grid(row=0, column=0, sticky="nsew", padx=(0, 7))
        output_column = tk.Frame(settings, bg=self.BG)
        output_column.grid(row=0, column=1, sticky="nsew", padx=(7, 0))
        self._build_password_card(password_column)
        self._build_output_card(output_column)
        self._build_action_button(container)

    # ==========================================================
    # SOURCE CARD
    # ==========================================================

    def _build_source_card(self, parent):
        card = self._card(parent)
        self.source_card = card
        card.pack(
            fill="both",
            expand=True,
        )

        self._section_title(
            card,
            "SOURCE PDF"
        )

        tk.Label(
            card,
            text="Select the PDF you want to secure or decrypt.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(
            anchor="w",
            padx=22,
            pady=(0, 12)
        )

        self.open_button = tk.Button(
            card,
            text="Select PDF",
            command=self.open_pdf,
            bg=self.ACCENT,
            fg="white",
            activebackground="#1F2937",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 10),
            padx=18,
            pady=9
        )
        self.open_button.pack(
            anchor="w",
            padx=22,
        )

        self.file_label = tk.Label(
            card,
            text="No PDF selected",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            font=("Segoe UI", 9)
        )
        self.file_label.pack(
            fill="x",
            padx=22,
            pady=(12, 3)
        )

        self.status_label = tk.Label(
            card,
            text="",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            justify="left",
            font=("Segoe UI", 9)
        )
        self.status_label.pack(
            fill="x",
            padx=22,
            pady=(0, 18)
        )

    # ==========================================================
    # ACTION CARD
    # ==========================================================

    def _build_action_card(self, parent):
        card = self._card(parent)
        self.action_card = card
        card.pack(
            fill="both",
            expand=True,
        )

        self._section_title(
            card,
            "SECURITY ACTION"
        )

        tk.Label(
            card,
            text="Choose what you want to do with the selected PDF.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        ).pack(
            anchor="w",
            padx=22,
            pady=(0, 14)
        )

        action_row = tk.Frame(
            card,
            bg=self.CARD
        )
        action_row.pack(
            padx=22,
            pady=(0, 16)
        )

        self.encrypt_radio = tk.Radiobutton(
            action_row,
            text="Encrypt",
            variable=self.action_var,
            value="encrypt",
            command=self._on_action_change,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            activeforeground=self.TEXT,
            selectcolor=self.CARD,
            font=("Segoe UI Semibold", 10)
        )
        self.encrypt_radio.pack(
            side="left",
            padx=(0, 18)
        )

        self.decrypt_radio = tk.Radiobutton(
            action_row,
            text="Decrypt",
            variable=self.action_var,
            value="decrypt",
            command=self._on_action_change,
            bg=self.CARD,
            fg=self.TEXT,
            activebackground=self.CARD,
            activeforeground=self.TEXT,
            selectcolor=self.CARD,
            font=("Segoe UI Semibold", 10)
        )
        self.decrypt_radio.pack(
            side="left"
        )

    # ==========================================================
    # PASSWORD CARD
    # ==========================================================

    def _build_password_card(self, parent):
        card = self._card(parent)
        self.password_card = card
        card.pack(
            fill="both",
            expand=True,
            pady=(0, 14)
        )

        self._section_title(
            card,
            "PASSWORD"
        )

        self.password_description = tk.Label(
            card,
            text="Configure the password used to protect your PDF.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        )
        self.password_description.pack(
            anchor="w",
            padx=22,
            pady=(0, 14)
        )

        # Keep credential controls at a deliberate reading width.  This gives
        # the card a calmer, form-like hierarchy on wide application windows.
        self.password_form = tk.Frame(
            card,
            bg=self.CARD,
            width=620,
        )
        self.password_form.pack(
            anchor="w",
            padx=22,
        )

        tk.Label(
            self.password_form,
            text="Password",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 9)
        ).pack(
            anchor="w",
        )

        password_row = tk.Frame(
            self.password_form,
            bg=self.CARD
        )
        password_row.pack(
            fill="x",
            pady=(6, 8)
        )

        password_row.grid_columnconfigure(
            0,
            weight=1
        )

        self.password_entry = tk.Entry(
            password_row,
            show="•",
            relief="flat",
            bd=0,
            bg="white",
            fg=self.TEXT,
            insertbackground=self.TEXT,
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor=self.ACCENT,
            insertwidth=2,
            width=38,
        )
        self.password_entry.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.show_password_button = tk.Button(
            password_row,
            text="Show",
            command=self.toggle_password,
            bg="#EEF2F7",
            fg=self.TEXT,
            activebackground="#E2E8F0",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI", 9),
            padx=14,
            pady=8
        )
        self.show_password_button.grid(
            row=0,
            column=1,
            padx=(8, 0)
        )

        self.password_hint = tk.Label(
            self.password_form,
            text="",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            justify="left",
            font=("Segoe UI", 8)
        )
        self.password_hint.pack(
            fill="x",
            pady=(0, 8)
        )

        # Owner password only relevant to encryption.
        self.owner_label = tk.Label(
            self.password_form,
            text="Owner Password (Optional)",
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 9)
        )
        self.owner_label.pack(
            anchor="w",
            pady=(4, 0)
        )

        self.owner_entry = tk.Entry(
            self.password_form,
            show="•",
            relief="flat",
            bd=0,
            bg="white",
            fg=self.TEXT,
            insertbackground=self.TEXT,
            font=("Segoe UI", 10),
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor=self.ACCENT,
            insertwidth=2,
            width=45,
        )
        self.owner_entry.pack(
            fill="x",
            pady=(6, 8)
        )

        self.owner_hint = tk.Label(
            self.password_form,
            text="If empty, the main password will be used.",
            bg=self.CARD,
            fg=self.MUTED,
            anchor="w",
            font=("Segoe UI", 8)
        )
        self.owner_hint.pack(
            fill="x",
            pady=(0, 16)
        )

    # ==========================================================
    # OUTPUT CARD
    # ==========================================================

    def _build_output_card(self, parent):
        card = self._card(parent)
        self.output_card = card
        card.pack(
            fill="both",
            expand=True,
            pady=(0, 14)
        )

        self._section_title(
            card,
            "OUTPUT"
        )

        self.output_description = tk.Label(
            card,
            text="Choose where the secured PDF should be saved.",
            bg=self.CARD,
            fg=self.MUTED,
            font=("Segoe UI", 9)
        )
        self.output_description.pack(
            anchor="w",
            padx=22,
            pady=(0, 12)
        )

        # Output paths can be longer than passwords, but are still bounded to
        # avoid an overly stretched control on large displays.
        output_form = tk.Frame(
            card,
            bg=self.CARD,
            width=700,
        )
        output_form.pack(
            anchor="w",
            padx=22,
            pady=(0, 20)
        )

        output_row = tk.Frame(output_form, bg=self.CARD)
        output_row.pack(fill="x")

        output_row.grid_columnconfigure(
            0,
            weight=1
        )

        self.output_entry = tk.Entry(
            output_row,
            relief="flat",
            bd=0,
            bg="white",
            fg=self.TEXT,
            insertbackground=self.TEXT,
            font=("Segoe UI", 9),
            highlightthickness=1,
            highlightbackground="#CBD5E1",
            highlightcolor=self.ACCENT,
            insertwidth=2,
            width=46,
        )
        self.output_entry.grid(
            row=0,
            column=0,
            sticky="ew"
        )

        self.browse_button = tk.Button(
            output_row,
            text="Browse",
            command=self.browse_output,
            bg="#EEF2F7",
            fg=self.TEXT,
            activebackground="#E2E8F0",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 9),
            padx=18,
            pady=8
        )
        self.browse_button.grid(
            row=0,
            column=1,
            padx=(8, 0)
        )

    # ==========================================================
    # MAIN ACTION BUTTON
    # ==========================================================

    def _build_action_button(self, parent):
        self.process_button = tk.Button(
            parent,
            text="Encrypt PDF",
            command=self.process_pdf,
            bg=self.BLUE,
            fg="white",
            activebackground="#1D4ED8",
            activeforeground="white",
            relief="flat",
            bd=0,
            cursor="hand2",
            font=("Segoe UI Semibold", 10),
            padx=24,
            pady=12
        )
        self.process_button.pack(
            anchor="e",
            pady=(2, 24)
        )

    # ==========================================================
    # CARD HELPERS
    # ==========================================================

    def _card(self, parent):
        return tk.Frame(
            parent,
            bg=self.CARD,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            bd=0
        )

    def _section_title(self, parent, text):
        tk.Label(
            parent,
            text=text,
            bg=self.CARD,
            fg=self.TEXT,
            font=("Segoe UI Semibold", 9)
        ).pack(
            anchor="w",
            padx=22,
            pady=(20, 8)
        )

    # ==========================================================
    # OPEN PDF
    # ==========================================================

    def open_pdf(self):
        """
        Select a PDF.

        IMPORTANT:
        We intentionally do NOT attempt to read pages of an
        encrypted PDF here.
        """

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
            status = self.security_service.inspect_pdf(
                path
            )

            self.input_path = path
            self.pdf_encrypted = bool(
                status["encrypted"]
            )

            filename = Path(path).name

            self.file_label.config(
                text=filename,
                fg=self.TEXT
            )

            if self.pdf_encrypted:
                self.status_label.config(
                    text=(
                        "Encrypted PDF detected.\n"
                        "Enter the document password to decrypt it."
                    ),
                    fg=self.WARNING
                )

                # Automatically switch to decrypt.
                self.action_var.set("decrypt")
                self._on_action_change()

            else:
                page_count = status.get(
                    "page_count"
                )

                if page_count is not None:
                    self.status_label.config(
                        text=f"PDF ready • {page_count} page(s)",
                        fg=self.SUCCESS
                    )
                else:
                    self.status_label.config(
                        text="PDF ready",
                        fg=self.SUCCESS
                    )

                # If normal PDF selected while currently
                # decrypting, switch back to encrypt.
                if self.action_var.get() == "decrypt":
                    self.action_var.set("encrypt")
                    self._on_action_change()

            self._set_default_output()

            self._set_status(
                f"Loaded PDF: {filename}"
            )

        except PDFSecurityError as exc:
            self.input_path = None
            self.pdf_encrypted = False

            messagebox.showerror(
                "Unable to Open PDF",
                str(exc)
            )

        except Exception as exc:
            self.input_path = None
            self.pdf_encrypted = False

            messagebox.showerror(
                "Unable to Open PDF",
                f"Unexpected error:\n\n{exc}"
            )

    # ==========================================================
    # ACTION CHANGE
    # ==========================================================

    def _on_action_change(self):
        action = self.action_var.get()

        if action == "encrypt":

            self.process_button.config(
                text="Encrypt PDF"
            )

            self.password_description.config(
                text=(
                    "Configure the password used "
                    "to protect your PDF."
                )
            )

            self.password_hint.config(
                text=(
                    "The password will be required "
                    "to open the encrypted PDF."
                )
            )

            self.owner_label.pack(
                anchor="w",
                pady=(4, 0)
            )

            self.owner_entry.pack(
                fill="x",
                pady=(6, 8)
            )

            self.owner_hint.pack(
                fill="x",
                pady=(0, 18)
            )

            self.output_description.config(
                text=(
                    "Choose where the encrypted PDF "
                    "should be saved."
                )
            )

        else:

            self.process_button.config(
                text="Decrypt PDF"
            )

            self.password_description.config(
                text=(
                    "Enter the password used to protect "
                    "the selected PDF."
                )
            )

            self.password_hint.config(
                text=(
                    "The password will be verified before "
                    "the PDF is decrypted."
                )
            )

            self.owner_label.pack_forget()
            self.owner_entry.pack_forget()
            self.owner_hint.pack_forget()

            self.output_description.config(
                text=(
                    "The decrypted PDF will be saved "
                    "without password protection."
                )
            )

            # If an encrypted PDF is already selected,
            # clearly remind the user.
            if self.input_path and self.pdf_encrypted:
                self.status_label.config(
                    text=(
                        "Encrypted PDF detected.\n"
                        "Enter the document password to decrypt it."
                    ),
                    fg=self.WARNING
                )

        self._set_default_output()

    # ==========================================================
    # PASSWORD VISIBILITY
    # ==========================================================

    def toggle_password(self):
        self.password_visible = not self.password_visible

        if self.password_visible:
            self.password_entry.config(
                show=""
            )
            self.show_password_button.config(
                text="Hide"
            )
        else:
            self.password_entry.config(
                show="•"
            )
            self.show_password_button.config(
                text="Show"
            )

    # ==========================================================
    # OUTPUT
    # ==========================================================

    def _set_default_output(self):
        if not self.input_path:
            return

        source = Path(
            self.input_path
        )

        if self.action_var.get() == "encrypt":
            filename = (
                f"{source.stem}_encrypted.pdf"
            )
        else:
            filename = (
                f"{source.stem}_decrypted.pdf"
            )

        output = source.parent / filename

        self.output_path = str(output)

        self.output_entry.delete(
            0,
            tk.END
        )
        self.output_entry.insert(
            0,
            str(output)
        )

    def browse_output(self):
        action = self.action_var.get()

        if action == "encrypt":
            default_name = "encrypted_document.pdf"
        else:
            default_name = "decrypted_document.pdf"

        path = filedialog.asksaveasfilename(
            title="Save PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[
                ("PDF files", "*.pdf")
            ]
        )

        if not path:
            return

        self.output_path = path

        self.output_entry.delete(
            0,
            tk.END
        )
        self.output_entry.insert(
            0,
            path
        )

    # ==========================================================
    # PROCESS
    # ==========================================================

    def process_pdf(self):
        if not self.input_path:
            messagebox.showwarning(
                "No PDF Selected",
                "Please select a PDF first."
            )
            return

        password = self.password_entry.get()

        if not password:
            messagebox.showwarning(
                "Password Required",
                "Please enter the PDF password."
            )
            self.password_entry.focus_set()
            return

        output = self.output_entry.get().strip()

        if not output:
            self._set_default_output()
            output = self.output_entry.get().strip()

        if not output:
            messagebox.showwarning(
                "Output Required",
                "Please choose an output location."
            )
            return

        output_path = Path(output)
        input_path = Path(self.input_path)

        # Avoid overwriting source.
        try:
            if (
                input_path.resolve()
                == output_path.resolve()
            ):
                messagebox.showwarning(
                    "Invalid Output",
                    (
                        "The output file cannot be "
                        "the same as the source PDF."
                    )
                )
                return
        except Exception:
            pass

        # Ensure PDF extension.
        if output_path.suffix.lower() != ".pdf":
            output_path = output_path.with_suffix(
                ".pdf"
            )
            output = str(output_path)

            self.output_entry.delete(
                0,
                tk.END
            )
            self.output_entry.insert(
                0,
                output
            )

        self.process_button.config(
            state="disabled",
            text=(
                "Encrypting..."
                if self.action_var.get() == "encrypt"
                else "Decrypting..."
            )
        )

        self.update_idletasks()

        try:
            action = self.action_var.get()

            if action == "encrypt":
                self._process_encrypt(
                    output
                )
            else:
                self._process_decrypt(
                    output,
                    password
                )

        except PDFSecurityError as exc:

            messagebox.showerror(
                (
                    "Encryption Error"
                    if self.action_var.get() == "encrypt"
                    else "Decryption Error"
                ),
                str(exc)
            )

        except Exception as exc:

            messagebox.showerror(
                "Security Error",
                f"Unexpected error:\n\n{exc}"
            )

        finally:
            self.process_button.config(
                state="normal",
                text=(
                    "Encrypt PDF"
                    if self.action_var.get() == "encrypt"
                    else "Decrypt PDF"
                )
            )

    # ==========================================================
    # ENCRYPT
    # ==========================================================

    def _process_encrypt(self, output):
        password = self.password_entry.get()
        owner_password = self.owner_entry.get()

        self.security_service.encrypt(
            input_path=self.input_path,
            output_path=output,
            password=password,
            owner_password=owner_password or None
        )

        self.output_path = output

        messagebox.showinfo(
            "Encryption Complete",
            (
                "PDF encrypted successfully.\n\n"
                f"Saved to:\n{output}"
            )
        )

        self._set_status(
            f"Encrypted PDF saved: {Path(output).name}"
        )

    # ==========================================================
    # DECRYPT
    # ==========================================================

    def _process_decrypt(
        self,
        output,
        password
    ):
        # Explicit validation before writing.
        if not self.pdf_encrypted:
            try:
                encrypted = (
                    self.security_service.is_encrypted(
                        self.input_path
                    )
                )
            except Exception:
                encrypted = False

            self.pdf_encrypted = encrypted

        if not self.pdf_encrypted:
            raise PDFSecurityError(
                "This PDF is not encrypted.\n"
                "There is no password to remove."
            )

        # Validate password first.
        valid = (
            self.security_service.validate_password(
                self.input_path,
                password
            )
        )

        if not valid:
            raise PDFSecurityError(
                "Incorrect PDF password.\n\n"
                "Please enter the password used "
                "to open this PDF."
            )

        self.security_service.decrypt(
            input_path=self.input_path,
            output_path=output,
            password=password
        )

        self.output_path = output

        messagebox.showinfo(
            "Decryption Complete",
            (
                "PDF decrypted successfully.\n\n"
                "The password has been removed "
                "from the output PDF.\n\n"
                f"Saved to:\n{output}"
            )
        )

        self._set_status(
            f"Decrypted PDF saved: {Path(output).name}"
        )

    # ==========================================================
    # STATUS CALLBACK
    # ==========================================================

    def _set_status(self, message):
        if callable(self.status_callback):
            try:
                self.status_callback(
                    message
                )
            except Exception:
                pass

    # ==========================================================
    # SCROLL
    # ==========================================================

    def _update_scroll_region(self, event=None):
        self.canvas.configure(
            scrollregion=self.canvas.bbox("all")
        )

    def _resize_canvas_content(self, event):
        self.canvas.itemconfigure(
            self.canvas_window,
            width=event.width
        )

    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(
                int(-1 * (event.delta / 120)),
                "units"
            )
        except Exception:
            pass

    # ==========================================================
    # CLEANUP
    # ==========================================================

    def destroy(self):
        try:
            self.canvas.unbind_all(
                "<MouseWheel>"
            )
        except Exception:
            pass

        super().destroy()


# Backward-compatible aliases
EncryptDecryptView = SecurityView
SecurityView = SecurityView
