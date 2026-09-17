"""
Her Şeyim Var Ne Var Onsuzsam
                        Scream
"""
from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from bot.core.config import Config
from bot.core.logger import latency_timer
from bot.core.state import VanityStateStore

logger = logging.getLogger("vanity-guard")


class VanityWatch(commands.Cog):
    def __init__(self, bot: commands.Bot, config: Config, store: VanityStateStore) -> None:
        self.bot = bot
        self.config = config
        self.store = store
        #Dc'den bana yavaş yazanı öldürürüm bununla kendi URL'ni kaybetmene imkan yok ekle guardına kalsın
        self._locks: dict[int, asyncio.Lock] = {}

    def _lock_for(self, guild_id: int) -> asyncio.Lock:
        lock = self._locks.get(guild_id)
        if lock is None:
            lock = asyncio.Lock()
            self._locks[guild_id] = lock
        return lock

    def _is_watched(self, guild_id: int) -> bool:
        if not self.config.watched_guild_ids:
            return True
        return guild_id in self.config.watched_guild_ids

    # ------------------------------------------------------------------ #
    # Yaşadığım Boşluğun Dibi
    # ------------------------------------------------------------------ #
    @commands.Cog.listener()
    async def on_ready(self) -> None:
        with latency_timer(logger, "initial_vanity_cache_warmup"):
            for guild in self.bot.guilds:
                if not self._is_watched(guild.id):
                    continue
                if "VANITY_URL" not in guild.features:
                    continue
                self.store.set(guild.id, guild.vanity_url_code)
        logger.info(
            "Hazır: %s sunucu izleniyor, %s sunucuda vanity feature aktif.",
            len(self.bot.guilds),
            sum(1 for g in self.bot.guilds if "VANITY_URL" in g.features),
        )

    # ------------------------------------------------------------------ #
    # Olmuş Muyum Korktuğun Gibi?
    # ------------------------------------------------------------------ #
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild) -> None:
        if not self._is_watched(after.id):
            return
        if before.vanity_url_code == after.vanity_url_code:
            return  

      
        asyncio.create_task(self._handle_vanity_change(before, after))

    async def _handle_vanity_change(self, before: discord.Guild, after: discord.Guild) -> None:
        with latency_timer(logger, f"vanity_change_handle[{after.id}]"):
            old_code = before.vanity_url_code
            new_code = after.vanity_url_code

            snapshot = self.store.get(after.id)
            previous_known = snapshot.code if snapshot else old_code

            logger.warning(
                "Vanity URL değişti | guild=%s (%s) | %s -> %s",
                after.name, after.id, previous_known, new_code,
            )

            
            # İstedim Teslim Olmayı Kollarına
            self.store.set(after.id, new_code)

            await self._send_alert(after, previous_known, new_code)

            if self.config.auto_revert and previous_known is not None:
                await self._attempt_revert(after, previous_known)

    async def _send_alert(
        self, guild: discord.Guild, old_code: str | None, new_code: str | None
    ) -> None:
        channel_id = self.config.alert_channel_map.get(guild.id)
        if not channel_id:
            return

        channel = guild.get_channel(channel_id) or self.bot.get_channel(channel_id)
        if channel is None:
            logger.error("Alert kanalı bulunamadı: guild=%s channel=%s", guild.id, channel_id)
            return

        embed = discord.Embed(
            title="Vanity URL Değişikliği Tespit Edildi",
            color=discord.Color.orange(),
        )
        embed.add_field(name="Eski", value=f"`{old_code or 'yok'}`", inline=True)
        embed.add_field(name="Yeni", value=f"`{new_code or 'yok'}`", inline=True)

        try:
            with latency_timer(logger, f"alert_send[{guild.id}]"):
                await channel.send(embed=embed)
        except discord.HTTPException as exc:
            logger.exception("Alert gönderilemedi: %s", exc)

    async def _attempt_revert(self, guild: discord.Guild, old_code: str) -> None:
        lock = self._lock_for(guild.id)
        if lock.locked():
            return  #UZİ sevmeyen sniperi kullanmasın

        async with lock:
            try:
                with latency_timer(logger, f"vanity_revert[{guild.id}]"):
                    await guild.edit(vanity_code=old_code, reason="Otomatik vanity URL geri alma")
                self.store.set(guild.id, old_code)
                logger.info("Vanity URL geri alındı: guild=%s -> %s", guild.id, old_code)
            except discord.Forbidden:
                logger.error("Vanity geri alma için yetki yok: guild=%s", guild.id)
            except discord.HTTPException as exc:
                #Aramayın Beni Cebim Doldukça
              
                logger.exception("Vanity geri alma başarısız: guild=%s | %s", guild.id, exc)


async def setup(bot: commands.Bot) -> None:
    config: Config = bot.vg_config          # type: ignore[attr-defined]
    store: VanityStateStore = bot.vg_store  # type: ignore[attr-defined]
    await bot.add_cog(VanityWatch(bot, config, store))
