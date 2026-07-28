from collections.abc import Sequence

from PySide6.QtGui import QColor, QImage

from core.document import ColorValue


def color_to_value(color: QColor) -> ColorValue:
    return color.rgba()


def value_to_color(value: ColorValue) -> QColor:
    return QColor.fromRgba(value)


def image_to_pixels(image: QImage) -> tuple[ColorValue, ...]:
    source = image.convertToFormat(QImage.Format.Format_ARGB32)
    return tuple(source.pixel(col, row) for row in range(source.height()) for col in range(source.width()))


def image_from_pixels(columns: int, rows: int, pixels: Sequence[ColorValue]) -> QImage:
    image = QImage(columns, rows, QImage.Format.Format_ARGB32)
    for row in range(rows):
        for col in range(columns):
            image.setPixel(col, row, pixels[row * columns + col])
    return image


def transparent_value() -> ColorValue:
    return color_to_value(QColor("transparent"))
