import discord
from typing import List
from discord.ext import commands

from .. import utils


class CommandErrors(commands.Cog):
    ''' Registers Error Handler for Cogs '''

    def __init__(self, bot):
        self.bot = bot


    async def clean_messages(self, messages: List[discord.Message]) -> None:
        for message in messages:
            try:
                await message.delete()
            except discord.NotFound:
                pass

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CheckFailure):
            return


def setup(bot):
    bot.add_cog(CommandErrors(bot))
