"""
Siz Şah Olsanız Biz Mat Ederiz Kim Olursanız Olun Farketmez...
                                                     Scream
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time

import discord
from discord.ext import commands

from bot.core.config import Config, ConfigError
from bot.core.logger import setup_logging
from bot.core.state import VanityStateStore

try:
    import uvloop
    uvloop.install()
    _UVLOOP_ACTIVE = True
except ImportError:
    _UVLOOP_ACTIVE = False


def build_bot(config: Config) -> commands.Bot:
    intents = discord.Intents.none()
    intents.guilds = True  

    bot = commands.Bot(
        command_prefix=commands.when_mentioned,  
        intents=intents,
        chunk_guilds_at_startup=False,  
        max_messages=None,              
    )
    bot.vg_config = config          
    bot.vg_store = VanityStateStore()  
    return bot
    #Yoluma Koyduğunuz Taşları Cebinize Koyunda Biraz Ağırlığınız Olsun Bilocann

def register_connection_logging(bot: commands.Bot, logger: logging.Logger) -> None:
    state = {"connect_start": None}

    @bot.event
    async def on_connect() -> None:
        state["connect_start"] = time.perf_counter()
        logger.info("Gateway bağlantısı kuruldu (handshake tamamlandı).")

    @bot.event
    async def on_ready() -> None:
        if state["connect_start"] is not None:
            elapsed_ms = (time.perf_counter() - state["connect_start"]) * 1000
            logger.info("READY alındı | toplam hazırlık süresi: %.3f ms", elapsed_ms)
        logger.info("Giriş yapıldı: %s (id=%s)", bot.user, bot.user.id if bot.user else "?")

    @bot.event
    async def on_disconnect() -> None:
        logger.warning("Gateway bağlantısı koptu, discord.py yeniden bağlanmayı deneyecek.")

    @bot.event
    async def on_resumed() -> None:
        logger.info("Gateway session RESUME edildi (state kaybı yok).")

    @bot.event
    async def on_error(event_method: str, *args, **kwargs) -> None:
        logger.exception("Beklenmeyen hata: event=%s", event_method)


async def main() -> None:
    try:
        config = Config.from_env()
    except ConfigError as exc:
        print(f"Yapılandırma hatası: {exc}", file=sys.stderr)
        sys.exit(1)

    logger = setup_logging(config.log_level)
    logger.info("uvloop aktif: %s", _UVLOOP_ACTIVE)

    bot = build_bot(config)
    register_connection_logging(bot, logger)

    async with bot:
        await bot.load_extension("bot.cogs.vanity_watch")
        await bot.start(config.token, reconnect=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
