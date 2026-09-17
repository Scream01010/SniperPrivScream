"""
In-memory guild -> vanity_url_code cache
Ne Kadar Hızlı Olursan Ol Nasibin Değilse Yetişemezsin...
                                                Scream
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class VanitySnapshot:
    code: str | None
    uses: int | None = None


class VanityStateStore:
    __slots__ = ("_cache",)

    def __init__(self) -> None:
        self._cache: dict[int, VanitySnapshot] = {}

    def get(self, guild_id: int) -> VanitySnapshot | None:
        return self._cache.get(guild_id)

    def set(self, guild_id: int, code: str | None, uses: int | None = None) -> None:
        self._cache[guild_id] = VanitySnapshot(code=code, uses=uses)

    def has(self, guild_id: int) -> bool:
        return guild_id in self._cache
