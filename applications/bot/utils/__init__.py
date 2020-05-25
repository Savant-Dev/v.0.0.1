from discord.ext import commands
from typing import Union, Optional, List

# Configure Developer Access
developer_ids = [654887208603615263, 496806918791102475]


def developer_only():
    async def predicate(ctx):
        return ctx.author.id in developer_ids

    return commands.check(predicate)


def private_command():
    async def predicate(ctx):
        return ctx.guild is None

    return commands.check(predicate)


def channel_restricted(channels: List[Union[int, str]]):
    async def predicate(ctx):
        return ctx.channel.id or ctx.channel.name in channels

    return commands.check(predicate)


class ConfigurationNotFound(Exception):
    def __init__(self, reason: Optional[str]):
        self.reason = reason
        
    def __str__(self) -> str:
        return getattr(self, 'reason', 'Unable to Locate Configuration File')
