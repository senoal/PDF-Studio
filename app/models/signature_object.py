from dataclasses import dataclass


@dataclass
class SignatureObject:
    image_path: str
    x: float
    y: float
    width: float
    height: float
    page_index: int = 0

    @property
    def rect(self):
        return (
            self.x,
            self.y,
            self.x + self.width,
            self.y + self.height,
        )

    def clone(self):
        return SignatureObject(
            image_path=self.image_path,
            x=self.x,
            y=self.y,
            width=self.width,
            height=self.height,
            page_index=self.page_index,
        )