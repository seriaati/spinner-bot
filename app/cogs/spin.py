from __future__ import annotations

import random
from typing import TYPE_CHECKING

import anyio.to_thread
import discord
from discord import app_commands
from discord.ext import commands

from app import ui
from app.spinner import render_spin

if TYPE_CHECKING:
    from app.core.bot import MyBot
    from app.types import Interaction

# Beyond this, slice labels become too small to read.
MAX_ITEMS = 50


class SpinModal(ui.Modal, title="Spin the wheel"):
    items: ui.Label[ui.TextInput] = ui.Label(
        text="Items",
        description=f"One item per line, up to {MAX_ITEMS} items",
        component=ui.TextInput(style=discord.TextStyle.long, max_length=4000),
    )

    async def on_submit(self, i: Interaction) -> None:
        items = [line.strip() for line in self.items.component.value.splitlines() if line.strip()]
        if not items:
            await i.response.send_message("Please enter at least one item.", ephemeral=True)
            return
        if len(items) > MAX_ITEMS:
            await i.response.send_message(
                f"Please enter at most {MAX_ITEMS} items.", ephemeral=True
            )
            return

        await i.response.defer(thinking=True)
        image = await anyio.to_thread.run_sync(render_spin, items, random.randrange(len(items)))
        await i.followup.send(file=discord.File(image, filename="spin.webp"))


class SpinCog(commands.Cog):
    def __init__(self, bot: MyBot) -> None:
        self.bot = bot

    @app_commands.command(name="spin", description="Spin a wheel to pick a random item")
    @app_commands.allowed_installs(guilds=True, users=True)
    @app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def spin(self, i: Interaction) -> None:
        await i.response.send_modal(SpinModal())


async def setup(bot: MyBot) -> None:
    await bot.add_cog(SpinCog(bot))
