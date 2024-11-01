from typing import TypeVar

T = TypeVar('T')


def x_or_none(x: T) -> T | None:
	return x or None
