from discord.ext import commands
from typing import Union, Optional, List

from .embeds import CheckFailures
from ...constants import BotConfig


class ConfigurationNotFound(Exception):
    def __init__(self, reason: Optional[str]):
        self.reason = reason

    def __str__(self) -> str:
        return getattr(self, 'reason', 'Unable to Locate Configuration File')


def developer_only():
    async def predicate(ctx):
        if ctx.author.id not in BotConfig.developer_ids:
            embed = CheckFailures.DeveloperRestricted()
            await ctx.send(embed=embed)

            return False

        return True

    return commands.check(predicate)


def private_command():
    async def predicate(ctx):
        if ctx.guild is not None:
            embed = CheckFailures.PrivateCommand()
            await ctx.send(embed=embed)

            return False

        return True

    return commands.check(predicate)


def channel_restricted(channels: List[Union[int, str]]):
    async def predicate(ctx):
        if not (ctx.channel.id in channels or ctx.channel.name in channels):
            embed = CheckFailures.ChannelRestriction(channels)
            await ctx.send(embed=embed)

            return False

        return True

    return commands.check(predicate)
