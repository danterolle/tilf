from PySide6.QtGui import QColor

from core.document import CanvasDocument


def create_document(columns: int = 3, rows: int = 2) -> CanvasDocument:
    return CanvasDocument(
        columns,
        rows,
        QColor("white"),
        history_limit=10,
        tile_cols=1,
        tile_rows=1,
        tile_size=1,
    )


def test_draw_pixel_can_be_undone_and_redone() -> None:
    document = create_document()
    snapshot = document.create_snapshot()

    assert document.draw_pixel(1, 1, QColor("black"))
    document.commit_snapshot(snapshot)

    assert document.image.pixelColor(1, 1) == QColor("black")
    assert document.undo()
    assert document.image.pixelColor(1, 1) == QColor("white")
    assert document.redo()
    assert document.image.pixelColor(1, 1) == QColor("black")


def test_flood_fill_stops_at_different_color() -> None:
    document = create_document(columns=3, rows=1)
    assert document.draw_pixel(1, 0, QColor("black"))

    assert document.flood_fill(0, 0, QColor("red"))

    assert document.image.pixelColor(0, 0) == QColor("red")
    assert document.image.pixelColor(1, 0) == QColor("black")
    assert document.image.pixelColor(2, 0) == QColor("white")


def test_replace_background_updates_matching_pixels_only() -> None:
    document = create_document(columns=2, rows=1)
    assert document.draw_pixel(1, 0, QColor("black"))

    assert document.replace_background(QColor("red"))

    assert document.image.pixelColor(0, 0) == QColor("red")
    assert document.image.pixelColor(1, 0) == QColor("black")
    assert document.undo()
    assert document.image.pixelColor(0, 0) == QColor("white")
    assert document.image.pixelColor(1, 0) == QColor("black")
