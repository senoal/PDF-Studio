import os
import fitz

from app.models.text_object import TextObject
from app.models.signature_object import SignatureObject


class PDFEditor:
    """
    Core engine for editing PDF documents.

    Responsibilities:
    - Load PDF
    - Manage text objects
    - Manage signature/image objects
    - Render preview pages
    - Export edited PDF
    """

    def __init__(self):
        self.doc = None
        self.source_path = None

        self.text_objects = []
        self.signature_objects = []

    # =========================================================
    # DOCUMENT
    # =========================================================

    def load(self, path):
        if not path:
            raise ValueError("PDF path is required.")

        if not os.path.isfile(path):
            raise FileNotFoundError(path)

        if self.doc is not None:
            self.doc.close()

        self.doc = fitz.open(path)
        self.source_path = path

        self.text_objects.clear()
        self.signature_objects.clear()

        return self.doc.page_count

    def close(self):
        if self.doc is not None:
            self.doc.close()
            self.doc = None

    @property
    def page_count(self):
        if self.doc is None:
            return 0

        return self.doc.page_count

    def get_page(self, index):
        if self.doc is None:
            raise RuntimeError("No PDF loaded.")

        if index < 0 or index >= self.doc.page_count:
            raise IndexError("Invalid page index.")

        return self.doc[index]

    # =========================================================
    # PREVIEW
    # =========================================================

    def render_page(self, page_index, scale=1.5):
        page = self.get_page(page_index)

        matrix = fitz.Matrix(scale, scale)

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False,
        )

        return pix

    # =========================================================
    # TEXT
    # =========================================================

    def add_text(self, obj: TextObject):
        self.text_objects.append(obj)

    def remove_text(self, obj):
        if obj in self.text_objects:
            self.text_objects.remove(obj)

    # =========================================================
    # SIGNATURE
    # =========================================================

    def add_signature(self, obj: SignatureObject):
        self.signature_objects.append(obj)

    def remove_signature(self, obj):
        if obj in self.signature_objects:
            self.signature_objects.remove(obj)

    # =========================================================
    # PAGE OBJECTS
    # =========================================================

    def get_objects_for_page(self, page_index):
        objects = []

        for obj in self.text_objects:
            if obj.page_index == page_index:
                objects.append(obj)

        for obj in self.signature_objects:
            if obj.page_index == page_index:
                objects.append(obj)

        return objects

    # =========================================================
    # EXPORT
    # =========================================================

    def export(self, output_path):
        if self.doc is None:
            raise RuntimeError("No PDF loaded.")

        if not output_path:
            raise ValueError("Output path is required.")

        output_dir = os.path.dirname(os.path.abspath(output_path))

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # Work on a copy of the source document.
        output_doc = fitz.open()

        try:
            output_doc.insert_pdf(self.doc)

            # -------------------------------------------------
            # TEXT
            # -------------------------------------------------

            for obj in self.text_objects:

                if obj.page_index >= output_doc.page_count:
                    continue

                page = output_doc[obj.page_index]

                rect = fitz.Rect(
                    obj.x,
                    obj.y,
                    obj.x + obj.width,
                    obj.y + obj.height,
                )

                font_name = self._resolve_font(
                    obj.font_name,
                    obj.bold,
                    obj.italic,
                )

                page.insert_textbox(
                    rect,
                    obj.text,
                    fontname=font_name,
                    fontsize=max(1, float(obj.font_size)),
                    color=obj.color,
                    align=obj.align,
                    overlay=True,
                )

            # -------------------------------------------------
            # SIGNATURE
            # -------------------------------------------------

            for obj in self.signature_objects:

                if obj.page_index >= output_doc.page_count:
                    continue

                if not os.path.isfile(obj.image_path):
                    continue

                page = output_doc[obj.page_index]

                rect = fitz.Rect(
                    obj.x,
                    obj.y,
                    obj.x + obj.width,
                    obj.y + obj.height,
                )

                page.insert_image(
                    rect,
                    filename=obj.image_path,
                    keep_proportion=True,
                    overlay=True,
                )

            # -------------------------------------------------
            # SAVE
            # -------------------------------------------------

            output_doc.save(
                output_path,
                garbage=4,
                deflate=True,
                clean=True,
            )

        finally:
            output_doc.close()

        return output_path

    # =========================================================
    # FONT
    # =========================================================

    @staticmethod
    def _resolve_font(font_name, bold=False, italic=False):

        if bold and italic:
            return "hebi"

        if bold:
            return "hebo"

        if italic:
            return "heit"

        if font_name in {
            "helv",
            "hebo",
            "heit",
            "hebi",
            "cour",
            "tiro",
            "symb",
        }:
            return font_name

        return "helv"