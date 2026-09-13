from pathlib import Path
import tkinter as tk

from app.gui.main_window import MainWindow


# ============================================================
# APPLICATION PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"
ICON_DIR = ASSETS_DIR / "icons"


# ============================================================
# ICON FILES
# ============================================================

ICO_PATH = ICON_DIR / "app_icon.ico"
PNG_PATH = ICON_DIR / "app_icon.ico.png"


# ============================================================
# FIND APPLICATION ICON
# ============================================================

def get_icon_path():
    """
    Find the application icon.

    Priority:
        1. app_icon.ico
        2. app_icon.ico.png
    """

    # Preferred Windows icon
    if ICO_PATH.is_file():
        return ICO_PATH

    # Fallback for existing PNG file
    if PNG_PATH.is_file():
        return PNG_PATH

    return None


# ============================================================
# FIND TKINTER ROOT
# ============================================================

def find_tk_root(app):
    """
    Find the actual Tkinter root window used by MainWindow.
    """

    # MainWindow may itself be a Tk instance
    if isinstance(app, tk.Tk):
        return app

    # Common application architectures
    possible_attributes = (
        "root",
        "window",
        "app",
        "master",
    )

    for attribute in possible_attributes:
        try:
            obj = getattr(app, attribute, None)

            if isinstance(obj, tk.Tk):
                return obj

        except Exception:
            pass

    # Last fallback:
    # Tkinter's default root
    try:
        default_root = tk._default_root

        if isinstance(default_root, tk.Tk):
            return default_root

    except Exception:
        pass

    return None


# ============================================================
# APPLY APPLICATION ICON
# ============================================================

def apply_application_icon(root):
    """
    Apply PDF Studio application icon to the Tkinter window.

    Supports:
        - Windows .ico
        - PNG fallback
    """

    if root is None:
        print("ERROR: Tkinter root not found.")
        return False

    icon_path = get_icon_path()

    # --------------------------------------------------------
    # Icon not found
    # --------------------------------------------------------

    if icon_path is None:

        print()
        print("ERROR: Application icon not found.")
        print()
        print("Expected icon folder:")
        print(f"  {ICON_DIR}")
        print()
        print("Expected files:")
        print(f"  {ICO_PATH}")
        print(f"  {PNG_PATH}")
        print()

        return False

    # --------------------------------------------------------
    # ICO
    # --------------------------------------------------------

    if icon_path.suffix.lower() == ".ico":

        try:
            root.iconbitmap(default=str(icon_path))

            print()
            print("PDF Studio application icon loaded:")
            print(f"  {icon_path}")
            print()

            return True

        except Exception as exc:

            print()
            print("WARNING: Unable to load ICO icon.")
            print(f"Reason: {exc}")
            print()

            # Continue to PNG fallback if available

    # --------------------------------------------------------
    # PNG fallback
    # --------------------------------------------------------

    try:

        image = tk.PhotoImage(file=str(icon_path))

        # Keep a reference so Tkinter does not garbage collect it
        root._pdf_tools_icon = image

        root.iconphoto(True, image)

        print()
        print("PDF Studio PNG application icon loaded:")
        print(f"  {icon_path}")
        print()

        return True

    except Exception as exc:

        print()
        print("ERROR: Unable to load application icon.")
        print(f"Reason: {exc}")
        print()

        return False


# ============================================================
# MAIN APPLICATION
# ============================================================

def main():

    # --------------------------------------------------------
    # Create existing application
    #
    # IMPORTANT:
    # Keep MainWindow() exactly as the existing architecture.
    # --------------------------------------------------------

    app = MainWindow()

    # --------------------------------------------------------
    # Find actual Tk root
    # --------------------------------------------------------

    root = find_tk_root(app)

    if root is None:
        raise RuntimeError(
            "PDF Studio could not find the Tkinter root window."
        )

    # --------------------------------------------------------
    # Application title
    # --------------------------------------------------------

    try:
        root.title("PDF Studio")
    except Exception:
        pass

    # --------------------------------------------------------
    # Apply application icon
    # --------------------------------------------------------

    apply_application_icon(root)

    # --------------------------------------------------------
    # Start Tkinter event loop
    # --------------------------------------------------------

    root.mainloop()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()
