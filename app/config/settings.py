from pathlib import Path


# ============================================================
# APPLICATION
# ============================================================

APP_NAME = "PDF Studio"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Professional offline PDF utility"


# ============================================================
# WINDOW
# ============================================================

WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 760
MIN_WINDOW_WIDTH = 980
MIN_WINDOW_HEIGHT = 620


# ============================================================
# PDF
# ============================================================

SUPPORTED_PDF_EXTENSIONS = (".pdf",)

DEFAULT_PREVIEW_DPI = 120
DEFAULT_FONT = "Helvetica"
DEFAULT_FONT_SIZE = 12


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

ASSETS_DIR = BASE_DIR / "assets"
ICONS_DIR = ASSETS_DIR / "icons"
IMAGES_DIR = ASSETS_DIR / "images"
FONTS_DIR = ASSETS_DIR / "fonts"

OUTPUT_DIR = BASE_DIR / "output"
LOG_DIR = BASE_DIR / "logs"


# ============================================================
# UI
# ============================================================

SIDEBAR_WIDTH = 235
CONTENT_PADDING = 32
