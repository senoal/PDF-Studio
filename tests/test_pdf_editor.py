from types import SimpleNamespace

import pytest

from app.gui.editor_view import EditorView
from app.core.pdf_editor import PDFEditor
from app.models.text_object import TextObject


class DummyVariable:
    def __init__(self, value=None):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def make_editor_view(text_object):
    view = EditorView.__new__(EditorView)
    view.current_page = 0
    view.preview_scale = 2.0
    view.page_origin = (10, 20)
    view.selected_object = text_object
    view.object_start = (
        text_object.x,
        text_object.y,
        text_object.width,
        text_object.height,
        text_object.font_size,
    )
    view.font_size_var = DummyVariable(text_object.font_size)
    view.editor = SimpleNamespace(
        get_page=lambda _: SimpleNamespace(
            rect=SimpleNamespace(width=600, height=800)
        )
    )
    return view


def test_text_resize_scales_box_and_font_proportionally():
    obj = TextObject("Resizable", 10, 20, 200, 60, font_size=16)
    view = make_editor_view(obj)

    view._resize_selected_object(100, 30)

    assert obj.width == pytest.approx(300)
    assert obj.height == pytest.approx(90)
    assert obj.font_size == pytest.approx(24)
    assert view.font_size_var.get() == pytest.approx(24)


def test_text_resize_cannot_shrink_below_minimum_font_size():
    obj = TextObject("Resizable", 10, 20, 200, 60, font_size=16)
    view = make_editor_view(obj)

    view._resize_selected_object(-1000, -1000)

    assert obj.font_size == pytest.approx(6)
    assert obj.width == pytest.approx(75)
    assert obj.height == pytest.approx(22.5)


def test_resize_handle_hit_area_uses_preview_coordinates():
    obj = TextObject("Resizable", 10, 20, 200, 60, font_size=16)
    view = make_editor_view(obj)

    handle_x = 10 + (10 + 200) * 2
    handle_y = 20 + (20 + 60) * 2

    assert view._is_on_resize_handle(handle_x + 10, handle_y - 10, obj)
    assert not view._is_on_resize_handle(handle_x + 20, handle_y, obj)


def test_text_clone_preserves_background_color():
    obj = TextObject(
        "Colored",
        10,
        20,
        200,
        60,
        background_color=(0.2, 0.4, 0.6),
    )

    assert obj.clone().background_color == (0.2, 0.4, 0.6)


def test_export_draws_colored_and_transparent_text_backgrounds(tmp_path):
    import fitz

    source_path = tmp_path / "source.pdf"
    output_path = tmp_path / "output.pdf"

    source = fitz.open()
    source.new_page(width=300, height=200)
    source.save(source_path)
    source.close()

    editor = PDFEditor()
    editor.load(str(source_path))
    editor.add_text(
        TextObject(
            "",
            20,
            20,
            80,
            50,
            background_color=(1.0, 0.0, 0.0),
        )
    )
    editor.add_text(
        TextObject(
            "",
            120,
            20,
            80,
            50,
            background_color=None,
        )
    )

    editor.export(str(output_path))
    editor.close()

    exported = fitz.open(output_path)
    pixmap = exported[0].get_pixmap()

    assert pixmap.pixel(40, 40)[:3] == (255, 0, 0)
    assert pixmap.pixel(140, 40)[:3] == (255, 255, 255)

    exported.close()
