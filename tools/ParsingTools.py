from typing import Optional

from PyQt5.QtCore import QVariant


def parse_int_or_default(value, default: int) -> int:
    try:
        if isinstance(value, QVariant):
            if value.isNull():
                return default
        return int(value)
    except ValueError:
        return default

def parse_float_or_default(value, default: float) -> float:
    try:
        if isinstance(value, QVariant):
            if value.isNull():
                return default
        return float(value)
    except ValueError:
        return default
