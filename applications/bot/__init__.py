import json
import aiohttp

from discord.ext import commands
from discord import LoginFailure
from discord import Embed, Message
from typing import Any, Union, Optional, List
from discord import Webhook, AsyncWebhookAdapter

from .cogs import ExtensionHandler
from ..api import infractions, database

from ..constants import BotConfig, Webhooks, EventConfig


# Webhook Configuration
webhook_name = 'Project S'
webhook_pfp = 'https://cdn.discordapp.com/attachments/697344429932937226/697344547381968976/Logo_-_Standalone.png'


class DiscordBot(commands.Bot, infractions.API):
    ''' Subclass of `commands.Bot` '''

    def __init__(self, log: Any, *args, **kwargs):
        self.log = log
        self.developer_log = Webhooks.developer_logs

        commands.Bot.__init__(self, *args, **kwargs)
        infractions.API.__init__(self, log)
        database.Connector.__init__(self, 'discord-bot', log)

    @staticmethod
    async def dispatch_webhook(*, url: str, message: Union[str, Embed]) -> Optional[Message]:
        if isinstance(message, Embed):
            message.set_author(name=webhook_name, icon_url=webhook_pfp)
            message.set_footer(text='Provided By SimplySavant')

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

        return config

        # Update Bot Attributes using getattr(), setattr()
        # Dispatch Webhook stating bot config has been updated

    async def update_extension(self, cog_name: str) -> None:
        query = 'SELECT settings FROM configs WHERE name = $1'
        args = (cog_name, )

        results = await super().fetchone(query, args)
        config = json.loads(results['settings'])

        return config

    async def log_event(self, event: str, *, event_details: Union[dict, Embed], log: str=None):
        if event in EventConfig.aggressive:
            report = await super().log_infraction(event, event_details)
        else:
            report = await super().log_passive(event, event_details)

        if not log:
            url = event_details['log_channel']
        else:
            url = log

        return await self.dispatch_webhook(url=url, message=report)

    async def record_search(self, *, case: Optional[int], guild: Optional[int], user: Optional[int]) -> Union[Embed, List]:
        if case:
            result = await super().fetch_infraction(id=case)

            return result

        elif user:
            try:
                results = await super().fetch_records(user_id=user, guild_id=guild)
            except infractions.InfractionNotFound as e:
                raise e

            return results

        else:
            raise ValueError('Insufficient Filter Values')


def get_prefix(bot: commands.Bot, message: Message) -> str:
    return BotConfig.prefix


def connect(token: str, logger: Any) -> None:
    client = DiscordBot(logger, command_prefix=get_prefix)

    ExtensionHandler.register_all(client)

    if token != BotConfig.token:
        return logger.critical('discord', 'Failed to verify tokens: Check your Environment Variables')

    try:
        client.run(token)
    except LoginFailure:
        logger.critical('discord', 'Failed to establish Discord connection - Improper Credentials')
        return
