"""Single source of truth для палитры областей и дефолтного сидинга."""
from typing import get_args

from domain.schemas.area import PaletteKey

PALETTE_KEYS: tuple[str, ...] = get_args(PaletteKey)


# (name, palette_key) — сидится при регистрации каждому новому юзеру
DEFAULT_AREAS: list[tuple[str, PaletteKey]] = [
    ("Machine Learning", "sienna"),
    ("Biology", "moss"),
    ("Physics", "azure"),
    ("Chemistry", "plum"),
    ("Neuroscience", "teal"),
    ("Mathematics", "forest"),
    ("Computer Science", "ochre"),
    ("Materials Science", "amber"),
    ("Medicine", "rose"),
    ("Economics", "slate"),
]
