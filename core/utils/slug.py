"""Нормализация имён в slug-форму (dedup-key для areas / tags)."""
import re
import unicodedata


def slugify(s: str) -> str:
    """Lowercase, без диакритики, без спецсимволов, пробелы/подчёркивания → '-'.

    Пустая строка / только мусор → ''.
    """
    s = s.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s
