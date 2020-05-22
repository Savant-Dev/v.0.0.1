import json
import asyncio
import aiohttp

from discord import LoginFailure
from discord.ext import commands
from typing import Any, Union, Optional
from discord import User, Member, Embed, Message
from discord import Webhook, AsyncWebhookAdapter

from .cogs import ExtensionHandler
from ..api import infractions, database


# Webhook Configuration
webhook_name = 'Project S'
webhook_pfp = 'https://cdn.discordapp.com/attachments/697344429932937226/697344547381968976/Logo_-_Standalone.png'
developer_url = 'Developer Webhook URL Here - Will be migrated to Database'

# Event Configuration
aggressive = ['member_ban', 'member_kick', 'member_warn', 'member_mute']


class DiscordBot(commands.Bot, infractions.API):
    ''' Subclass of `commands.Bot` '''

    def __init__(self, log: Any, *args, **kwargs):
        self.log = log
        self.developer_log = developer_url

        commands.Bot.__init__(self, *args, **kwargs)
        infractions.API.__init__(self, log)
        database.Connector.__init__(self, 'discord-bot', log)

    @staticmethod
    async def dispatch_webhook(*, url: str, message: Union[str, Embed]) -> Optional[Message]:
        if isinstance(message, Embed):
            message.set_author(name=webhook_name, icon_url=webhook_pfp)
            message.set_footer(text='Provided By SimplySavant')

            is_embed = True

        async with aiohttp.ClientSession() as session:
            webhook = Webhook.from_url(url, adapter=AsyncWebhookAdapter(session))
            if isinstance(message, str):
                sent = await webhook.send(message, username=webhook_name, avatar_url=webhook_pfp)
            elif isinstance(message, Embed):
                sent = await webhook.send(embed=message, username=webhook_name, avatar_url=webhook_pfp)
            else:
                raise TypeError(f'Cannot Send Type: {type(message)} via Webhook.')
            await session.close()

        return sent

    async def update_config(self) -> None:
        query = 'SELECT settings FROM configs WHERE name = $1'
        args = ('discord-bot', )

        results = await super().fetchone(query, args)
        config = json.loads(results['settings'])

        # Update Bot Attributes using getattr(), setattr()
        # Dispatch Webhook stating bot config has been updated

    async def update_extension(self, cog_name: str) -> None:
        query = 'SELECT settings FROM configs WHERE name = $1'
        args = (cog_name, )

        results = await super().fetchone(query, args)
        config = json.loads(results['settings'])

        return config

    async def log_event(self, event: str, *, event_details: dict):
        if event in aggressive:
            report = await super().log_infraction(event, event_details)
        else:
            report = await super().log_passive(event, event_details)

        url = event_details['log_channel']
        await self.dispatch_webhook(url=url, message=report)


def connect(token: str, logger: Any) -> None:
    client = DiscordBot(logger, command_prefix='!')

    ExtensionHandler.register_all(client)

    try:
        client.run(token)
    except LoginFailure:
        logger.critical('discord', 'Failed to establish Discord connection - Improper Credentials')
        return
