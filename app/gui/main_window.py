import tkinter as tk
from pathlib import Path
from tkinter import ttk

from app.config.settings import (
    APP_NAME,
    APP_VERSION,
    WINDOW_WIDTH,
    WINDOW_HEIGHT,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
)

from app.gui.sidebar import Sidebar
from app.gui.status_bar import StatusBar

from app.gui.merge_view import MergeView
from app.gui.delete_pages_view import DeletePagesView
from app.gui.watermark_view import WatermarkView
from app.gui.header_footer_view import HeaderFooterView
from app.gui.security_view import SecurityView
from app.gui.editor_view import EditorView
from app.gui.theme import (
    ACCENT,
    APP_BG,
    BORDER,
    INK,
    MUTED,
    NAVY,
    NAVY_HOVER,
    SIDEBAR,
    SIDEBAR_ACTIVE,
    SIDEBAR_MUTED,
    SURFACE,
    SURFACE_MUTED,
)


class MainWindow:
    """Main PDF Studio application window."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        # Application icon
        icon_path = (
            Path(__file__).resolve().parents[2]
            / "icons"
            / "pdf_tools.ico"
        )

        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass


        self._configure_window()
        self._configure_styles()
        self._build_layout()
        self._register_shortcuts()

        self.show_welcome()

    # ========================================================
    # WINDOW
    # ========================================================

    def _configure_window(self) -> None:
        self.root.title(f"{APP_NAME}")
        self.root.geometry(
            f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}"
        )

        self.root.minsize(
            MIN_WINDOW_WIDTH,
            MIN_WINDOW_HEIGHT,
        )

        self.root.configure(
            background=APP_BG
        )

        try:
            self.root.iconname(APP_NAME)
        except tk.TclError:
            pass

    # ========================================================
    # STYLES
    # ========================================================

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # ----------------------------------------------------
        # Root / Frames
        # ----------------------------------------------------

        style.configure(
            "Sidebar.TFrame",
            background=SIDEBAR,
        )

        style.configure(
            "Main.TFrame",
            background=APP_BG,
        )

        style.configure(
            "Content.TFrame",
            background=SURFACE,
        )

        style.configure(
            "Header.TFrame",
            background=SURFACE,
        )

        style.configure(
            "Status.TFrame",
            background=SURFACE_MUTED,
        )

        # ----------------------------------------------------
        # Labels
        # ----------------------------------------------------

        style.configure(
            "Brand.TLabel",
            background=SIDEBAR,
            foreground="#ffffff",
            font=("Segoe UI", 14, "bold"),
        )

        style.configure(
            "BrandSub.TLabel",
            background=SIDEBAR,
            foreground=SIDEBAR_MUTED,
            font=("Segoe UI", 8),
        )

        style.configure(
            "Section.TLabel",
            background=SIDEBAR,
            foreground="#81909E",
            font=("Segoe UI", 8, "bold"),
        )

        style.configure(
            "Privacy.TLabel",
            background=SIDEBAR,
            foreground="#D3DAE1",
            font=("Segoe UI", 9, "bold"),
        )

        style.configure(
            "PrivacySub.TLabel",
            background=SIDEBAR,
            foreground=SIDEBAR_MUTED,
            font=("Segoe UI", 8),
        )

        style.configure(
            "Status.TLabel",
            background=SURFACE_MUTED,
            foreground=MUTED,
            font=("Segoe UI", 8),
        )

        style.configure(
            "PageTitle.TLabel",
            background=SURFACE,
            foreground=INK,
            font=("Segoe UI", 24, "bold"),
        )

        style.configure(
            "PageSubtitle.TLabel",
            background=SURFACE,
            foreground=MUTED,
            font=("Segoe UI", 10),
        )

        style.configure(
            "WelcomeTitle.TLabel",
            background=SURFACE,
            foreground=INK,
            font=("Segoe UI", 28, "bold"),
        )

        style.configure(
            "WelcomeSubtitle.TLabel",
            background=SURFACE,
            foreground=MUTED,
            font=("Segoe UI", 11),
        )

        style.configure(
            "CardTitle.TLabel",
            background=SURFACE,
            foreground=INK,
            font=("Segoe UI", 11, "bold"),
        )

        style.configure(
            "CardText.TLabel",
            background=SURFACE,
            foreground=MUTED,
            font=("Segoe UI", 9),
        )

        # ----------------------------------------------------
        # Navigation
        # ----------------------------------------------------

        style.configure(
            "Navigation.TButton",
            background=SIDEBAR,
            foreground="#D3DAE1",
            borderwidth=0,
            relief="flat",
            anchor="w",
            font=("Segoe UI", 9),
            padding=(14, 9),
        )

        style.map(
            "Navigation.TButton",
            background=[
                ("active", NAVY_HOVER),
            ],
            foreground=[
                ("active", "#ffffff"),
            ],
        )

        style.configure(
            "NavigationActive.TButton",
            background=SIDEBAR_ACTIVE,
            foreground="#ffffff",
            borderwidth=0,
            relief="flat",
            anchor="w",
            font=("Segoe UI", 9, "bold"),
            padding=(14, 9),
        )

        # ----------------------------------------------------
        # Action Buttons
        # ----------------------------------------------------

        style.configure(
            "Primary.TButton",
            background=NAVY,
            foreground="#FFFFFF",
            borderwidth=0,
            relief="flat",
            padding=(18, 10),
            font=("Segoe UI", 9, "bold"),
        )

        style.map(
            "Primary.TButton",
            background=[
                ("active", NAVY_HOVER),
            ],
        )

        style.configure(
            "Secondary.TButton",
            background="#EEF1EF",
            foreground=INK,
            borderwidth=0,
            relief="flat",
            padding=(16, 9),
            font=("Segoe UI", 9),
        )

        style.map(
            "Secondary.TButton",
            background=[
                ("active", "#E2E7E3"),
            ],
        )

        # ----------------------------------------------------
        # Cards
        # ----------------------------------------------------

        style.configure(
            "Card.TFrame",
            background=SURFACE,
            relief="flat",
        )

        style.configure(
            "Treeview",
            background=SURFACE,
            fieldbackground=SURFACE,
            foreground=INK,
            rowheight=34,
            borderwidth=0,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Treeview.Heading",
            background="#F2F4F2",
            foreground=MUTED,
            relief="flat",
            font=("Segoe UI", 8, "bold"),
        )
        style.map(
            "Treeview",
            background=[("selected", "#E8EEF0")],
            foreground=[("selected", INK)],
        )
        style.configure(
            "TEntry",
            fieldbackground=SURFACE,
            foreground=INK,
            bordercolor=BORDER,
            lightcolor=SURFACE,
            darkcolor=BORDER,
            padding=(9, 7),
        )
        style.configure(
            "TCombobox",
            fieldbackground=SURFACE,
            foreground=INK,
            background=SURFACE,
            bordercolor=BORDER,
            arrowcolor=MUTED,
            padding=(7, 5),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", SURFACE)],
            selectbackground=[("readonly", "#E8EEF0")],
            selectforeground=[("readonly", INK)],
        )
        style.configure(
            "Vertical.TScrollbar",
            background="#CAD3D0",
            troughcolor="#F1F3F1",
            bordercolor="#F1F3F1",
            arrowcolor=MUTED,
            width=10,
        )

    # ========================================================
    # LAYOUT
    # ========================================================

    def _build_layout(self) -> None:
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = Sidebar(
            self.root,
            on_select=self.navigate,
        )

        self.sidebar.grid(
            row=0,
            column=0,
            sticky="ns",
        )

        # Main container
        self.main_container = ttk.Frame(
            self.root,
            style="Main.TFrame",
        )

        self.main_container.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        self.main_container.columnconfigure(
            0,
            weight=1,
        )

        self.main_container.rowconfigure(
            1,
            weight=1,
        )

        # Header
        self.header = ttk.Frame(
            self.main_container,
            style="Header.TFrame",
        )

        self.header.grid(
            row=0,
            column=0,
            sticky="ew",
        )

        self._build_header()

        # Content
        self.content = ttk.Frame(
            self.main_container,
            style="Content.TFrame",
        )

        self.content.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=18,
            pady=(0, 18),
        )

        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)

        # Status bar
        self.status_bar = StatusBar(
            self.root
        )

        self.status_bar.grid(
            row=1,
            column=0,
            columnspan=2,
            sticky="ew",
        )

    def _build_header(self) -> None:
        self.header.columnconfigure(
            0,
            weight=1,
        )

        title_frame = ttk.Frame(
            self.header,
            style="Header.TFrame",
        )

        title_frame.grid(
            row=0,
            column=0,
            sticky="w",
            padx=28,
            pady=18,
        )

        self.header_title = ttk.Label(
            title_frame,
            text="Welcome",
            style="PageTitle.TLabel",
        )

        self.header_title.pack(
            anchor="w"
        )

        self.header_subtitle = ttk.Label(
            title_frame,
            text="Professional PDF editing, all in one place.",
            style="PageSubtitle.TLabel",
        )

        self.header_subtitle.pack(
            anchor="w",
            pady=(2, 0),
        )

        self._build_security_mark()

    def _build_security_mark(self) -> None:
        """Add a compact personal-brand card to the persistent header."""
        mark_card = tk.Canvas(
            self.header,
            width=390,
            height=68,
            bg="#ffffff",
            highlightthickness=0,
            bd=0,
        )
        mark_card.grid(
            row=0,
            column=1,
            sticky="e",
            padx=28,
            pady=13,
        )

        # The restrained navy accent and warm neutral surface match the app's
        # existing visual language without competing with the page title.
        self._draw_rounded_rectangle(
            mark_card, 4, 5, 386, 64, 15, "#f1eee6"
        )
        self._draw_rounded_rectangle(
            mark_card, 3, 3, 385, 62, 15, "#fbfaf6", "#e7e0d1"
        )
        mark_card.create_line(
            20, 17, 20, 51,
            fill="#b78a31",
            width=3,
        )
        mark_card.create_text(
            36, 25,
            anchor="w",
            text="SENO ALRIANTO",
            fill="#263346",
            font=("Segoe UI", 10, "bold"),
        )
        mark_card.create_text(
            36, 44,
            anchor="w",
            text="AI Assisted Software Engineer · Data & Application Security",
            fill="#7b746a",
            font=("Segoe UI", 8),
        )

    @staticmethod
    def _draw_rounded_rectangle(
        canvas,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        radius: int,
        fill: str,
        outline: str | None = None,
    ) -> None:
        """Draw a simple rounded rectangle on a Tkinter canvas."""
        radius = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1,
        ]
        canvas.create_polygon(
            points,
            smooth=True,
            splinesteps=16,
            fill=fill,
            outline=outline or fill,
        )

    # ========================================================
    # NAVIGATION
    # ========================================================

    def navigate(self, feature: str) -> None:
        """Navigate to selected feature."""
        views = {
            "merge": (
                MergeView,
                "Merge PDF",
                "Combine multiple PDF files into a single document.",
            ),
            "delete_pages": (
                DeletePagesView,
                "Delete Pages",
                "Remove unwanted pages from your PDF document.",
            ),
            "watermark": (
                WatermarkView,
                "Watermark",
                "Add a professional watermark to your document.",
            ),
            "header_footer": (
                HeaderFooterView,
                "Header & Footer",
                "Add headers, footers and page numbering.",
            ),
            "security": (
                SecurityView,
                "Encrypt / Decrypt",
                "Protect or unlock your PDF documents.",
            ),
            "editor": (
                EditorView,
                "Edit PDF",
                "Add text and electronic signatures to your PDF.",
            ),
        }

        selected = views.get(feature)

        if selected is None:
            self.show_welcome()
            return

        view_class, title, subtitle = selected

        self._clear_content()

        self.header_title.config(
            text=title
        )

        self.header_subtitle.config(
            text=subtitle
        )

        view = view_class(
            self.content,
            status_callback=self.set_status,
        )

        view.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.sidebar.set_active(feature)

        self.set_status(
            f"{title} ready"
        )

    def _clear_content(self) -> None:
        for widget in self.content.winfo_children():
            widget.destroy()

    # ========================================================
    # WELCOME
    # ========================================================

    def show_welcome(self) -> None:
        """Show application welcome dashboard."""
        self._clear_content()

        self.header_title.config(
            text="Welcome"
        )

        self.header_subtitle.config(
            text="Professional PDF editing, all in one place."
        )

        frame = ttk.Frame(
            self.content,
            style="Content.TFrame",
        )

        frame.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=28,
            pady=28,
        )

        frame.columnconfigure(
            0,
            weight=1,
        )

        # ----------------------------------------------------
        # Welcome
        # ----------------------------------------------------

        welcome = ttk.Frame(
            frame,
            style="Content.TFrame",
        )

        welcome.grid(
            row=0,
            column=0,
            sticky="ew",
            pady=(20, 30),
        )

        ttk.Label(
            welcome,
            text="Everything you need for PDF work.",
            style="WelcomeTitle.TLabel",
        ).pack(
            anchor="w"
        )

        ttk.Label(
            welcome,
            text=(
                "Merge, organize, protect and edit PDF documents "
                "without uploading your files anywhere."
            ),
            style="WelcomeSubtitle.TLabel",
            wraplength=720,
        ).pack(
            anchor="w",
            pady=(10, 0),
        )

        # ----------------------------------------------------
        # Feature Cards
        # ----------------------------------------------------

        cards = ttk.Frame(
            frame,
            style="Content.TFrame",
        )

        cards.grid(
            row=1,
            column=0,
            sticky="ew",
        )

        for column in range(3):
            cards.columnconfigure(
                column,
                weight=1,
            )

        features = [
            (
                "Merge PDF",
                "Combine multiple documents into one clean PDF.",
                "merge",
            ),
            (
                "Organize",
                "Delete unwanted pages and prepare your document.",
                "delete_pages",
            ),
            (
                "Protect",
                "Encrypt and decrypt PDF documents securely.",
                "security",
            ),
            (
                "Brand",
                "Add watermark, header and footer elements.",
                "watermark",
            ),
            (
                "Edit",
                "Add text and electronic signatures.",
                "editor",
            ),
            (
                "100% Offline",
                "Your files remain on your local computer.",
                None,
            ),
        ]

        for index, (title, description, feature) in enumerate(features):
            row = index // 3
            column = index % 3

            self._create_feature_card(
                cards,
                row,
                column,
                title,
                description,
                feature,
            )

        self.set_status(
            "Ready — select a tool to get started"
        )

    def _create_feature_card(
        self,
        parent,
        row: int,
        column: int,
        title: str,
        description: str,
        feature: str | None,
    ) -> None:

        card = ttk.Frame(
            parent,
            style="Card.TFrame",
        )

        card.grid(
            row=row,
            column=column,
            sticky="nsew",
            padx=6,
            pady=6,
            ipadx=16,
            ipady=14,
        )

        title_label = ttk.Label(
            card,
            text=title,
            style="CardTitle.TLabel",
        )

        title_label.pack(
            anchor="w",
            padx=12,
            pady=(10, 5),
        )

        description_label = ttk.Label(
            card,
            text=description,
            style="CardText.TLabel",
            wraplength=220,
            justify="left",
        )

        description_label.pack(
            anchor="w",
            padx=12,
            pady=(0, 12),
        )

        if feature:
            action = ttk.Button(
                card,
                text="Open Tool  →",
                style="Secondary.TButton",
                command=lambda: self.navigate(feature),
            )

            action.pack(
                anchor="w",
                padx=12,
                pady=(0, 8),
            )

    # ========================================================
    # STATUS
    # ========================================================

    def set_status(self, message: str) -> None:
        self.status_bar.set_message(message)

    # ========================================================
    # KEYBOARD SHORTCUTS
    # ========================================================

    def _register_shortcuts(self) -> None:
        self.root.bind(
            "<Control-m>",
            lambda event: self.navigate("merge"),
        )

        self.root.bind(
            "<Control-d>",
            lambda event: self.navigate("delete_pages"),
        )

        self.root.bind(
            "<Control-e>",
            lambda event: self.navigate("editor"),
        )

        self.root.bind(
            "<Escape>",
            lambda event: self.show_welcome(),
        )

    # ========================================================
    # RUN
    # ========================================================

    def run(self) -> None:
        self.root.mainloop()
