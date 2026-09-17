"""
Hisler Gerçek Düşler Sahte...
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


class ConfigError(RuntimeError):
    pass


def _get_env(name: str, required: bool = True, default: str | None = None) -> str | None:
    value = os.getenv(name, default)
    if required and not value:
        raise ConfigError(f"Zorunlu ortam değişkeni eksik: {name}")
    return value


def _parse_int_list(raw: str | None) -> list[int]:
    if not raw:
        return []
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


@dataclass(frozen=True, slots=True)
class Config:
    token: str
    #Kullanamıyorsan dc sil zaten olm koddan anlasan bunun koruma sniperi olduğunu anlarsın oç
    
    watched_guild_ids: list[int] = field(default_factory=list)
    
    alert_channel_map: dict[int, int] = field(default_factory=dict)
    
    auto_revert: bool = False
    log_level: str = "INFO"

    @classmethod
    def from_env(cls) -> "Config":
        token = _get_env("DISCORD_TOKEN")
        watched = _parse_int_list(os.getenv("WATCHED_GUILD_IDS"))

        alert_map: dict[int, int] = {}
        raw_map = os.getenv("ALERT_CHANNEL_MAP", "")
        for pair in raw_map.split(","):
            pair = pair.strip()
            if not pair:
                continue
            gid, cid = pair.split(":")
            alert_map[int(gid)] = int(cid)

        auto_revert = os.getenv("AUTO_REVERT", "false").lower() in ("1", "true", "yes")
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()

        return cls(
            token=token,
            watched_guild_ids=watched,
            alert_channel_map=alert_map,
            auto_revert=auto_revert,
            log_level=log_level,
        )
