from utils import config


def test_default_canvas_size_matches_tile_defaults() -> None:
    assert config.DEFAULT_WIDTH == config.DEFAULT_TILE_COLS * config.DEFAULT_TILE_SIZE
    assert config.DEFAULT_HEIGHT == config.DEFAULT_TILE_ROWS * config.DEFAULT_TILE_SIZE


def test_all_shift_options_have_offsets() -> None:
    assert {option.lower() for option in config.SHIFT_OPTIONS} == set(config.SHIFT_OFFSETS)
