from dataclasses import dataclass
from typing import Tuple


@dataclass
class TextObject:
    text: str
    x: float
    y: float
    width: float
    height: float

    font_name: str = "helv"
    font_size: float = 16.0

    color: Tuple[float, float, float] = (0.05, 0.05, 0.05)

    align: int = 0

    page_index: int = 0

    bold: bool = False
    italic: bool = False

    @property
    def rect(self):
        return (
            self.x,
            self.y,
            self.x + self.width,
            self.y + self.height,
        )

    def clone(self):
        return TextObject(
            text=self.text,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            font_name=self.font_name,
            font_size=self.font_size,
            color=self.color,
            align=self.align,
            page_index=self.page_index,
            bold=self.bold,
            italic=self.italic,
        )