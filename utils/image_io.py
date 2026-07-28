import os
from typing import cast

from PySide6.QtGui import QColor, QImage, QPainter

from utils import config


def infer_image_format(path: str) -> str:
    file_ext = os.path.splitext(path)[1].upper().replace(".", "")
    if file_ext in config.JPEG_EXTENSIONS:
        return config.IMAGE_FORMAT_JPEG
    if file_ext == config.IMAGE_FORMAT_BMP:
        return config.IMAGE_FORMAT_BMP
    return config.IMAGE_FORMAT_PNG


def export_image(image: QImage, filename: str, file_format: str | None, is_transparent: bool) -> bool:
    qt_file_format = _qt_save_format(file_format)
    image_to_save = image.copy()

    if is_transparent:
        return image_to_save.save(filename, qt_file_format)

    background_image = QImage(image_to_save.size(), QImage.Format.Format_ARGB32)
    background_image.fill(QColor(config.COLOR_WHITE))
    painter = QPainter(background_image)
    painter.drawImage(0, 0, image_to_save)
    painter.end()
    return background_image.save(filename, qt_file_format)


def _qt_save_format(file_format: str | None) -> bytes | None:
    # PySide6 accepts string formats at runtime, while its stubs annotate bytes.
    return cast(bytes | None, file_format)
