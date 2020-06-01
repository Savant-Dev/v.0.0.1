import json

from discord import Member, User, Embed
from typing import Union, Optional, List, Any

from . import database
from ..constants import EventConfig


class InfractionNotFound(Exception):
    def __init__(self, reason: Optional[str]):
        self.reason = reason

    def __str__(self) -> str:
        return getattr(self, 'reason', 'Unable To Locate Infraction Specified')


class API(database.Connector):
    ''' Tracks and Reports Events in the Server '''

    def __init__(self, log: Any):
        self.log = log

        super().__init__('infraction-api', log)

    @staticmethod
    def build_embed(event: str, details: dict) -> Embed:
        color = getattr(EventConfig, event, 0x00ff00)
        event = event.replace('_', ' ').title()

        if not details["Moderator"]:
            moderator = 'None'
        else:
            moderator = details["Moderator"].mention

        embed = Embed(
            title = f'Event Logging --> {event}',
            color = color,
            description = (
                f'A __{event}__ Event was triggered by: {details["User"].mention} \n\n'
                f'Moderator Influence: {moderator}\n'
                f'Event Duration: {details["Duration"]}\n\n'
                f'Event Details: \n{details["Reason"]}'
            )
        )

        return embed

    async def store_event(self, event: tuple) -> bool:
        statement = 'INSERT INTO infractions (guild_id, user_id, event_type, embed) VALUES ($1, $2, $3, $4)'
        status = await super().insertone(statement, *event)

        return status

    async def log_infraction(self, event: str, details: dict) -> Embed:
        report = self.build_embed(event, details)

        try:
            guild = details["User"].guild.id
        except AttributeError:
            guild = details["Guild"].id

        args = (
            guild,
            details["User"].id,
            event,
            json.dumps(report.to_dict())
        )

        saved = await self.store_event(args)
        if saved:
            report.description += '\n\n*Event Successfully Committed To Database*'
            self.log.trace('infractions', f'An Infraction has been placed against {args[1]}')
        else:
            report.description += '\n\n*Event Failed to Commit to Database*'
            self.log.warn('infractions', f'An Infraction against {args[1]} Failed to Commit')

        return report

    async def log_passive(self, event: str, details: dict) -> Embed:
        report = self.build_embed(event, details)

        return report
