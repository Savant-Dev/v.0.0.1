import json

from discord import Member
from os.path import exists, abspath
from typing import Union, Optional, Any, List

from . import database
from . import ConfigurationError

from ..constants import Boosts, Leagues
from ..constants import Levels, Prestiges


# Custom Exceptions

class NoBackupFound(Exception):
    def __init__(self, reason: Optional[str]):
        self.reason = reason

    def __str__(self):
        return getattr(self, 'reason', 'Unable to Locate Backup File')


class UserOverwriteError(Exception):
    def __init__(self, reason: Optional[str]):
        self.reason = reason

    def __str__(self):
        return getattr(self, 'reason', 'Ignoring Overwrite Command')


class GlobalPermissionsError(Exception):
    def __init__(self, reason: Optional[str]):
        self.reason = reason

    def __str__(self):
        return getattr(self, 'reason', 'You Cannot Edit Global Records')


# Data Containers

class GuildUser():
    def __init__(self, guild: int, **kwargs):
        self.guild_id = guild

        for attribute in kwargs:
            setattr(self, attribute, kwargs[attribute])

    def __str__(self):
        try:
            message = (
                f'User ID: {self.user_id} - Guild ID: {self.guild_id} - '
                f'Prestige: {self.prestige.current} - Level: {self.level.current} - '
                f'Current Experience: {self.experience}'
            )
        except AttributeError:
            message = (
                f'User ID: {self.user_id} - Guild ID: {self.guild_id} - '
                f'Experience: {self.experience}'
            )

        return message

    def __repr__(self):
        return self.__str__()


class GlobalUser():
    def __init__(self, **kwargs):
        for attribute in kwargs:
            setattr(self, attribute, kwargs[attribute])

    def __str__(self):
        try:
            message = (
                f'User ID: {self.user_id} - League: {self.league.current} - '
                f'Boost Increment: {self.boost.current} - '
                f'Current Experience: {self.experience}'
            )
        except AttributeError:
            message = f'User ID: {self.user_id} - Current Experience: {self.experience}'

        return message


class Statistic(object):
    def __init__(self, **kwargs):
        if kwargs:
            for attribute in kwargs:
                setattr(self, attribute, kwargs[attribute])

    def __str__(self):
        message = (
            f'Current: {self.current} - Next: {self.next} - '
            f'Remaining: {self.remaining}'
        )

        return message

    def __repr__(self):
        return self.__str__()


# Database Handler & Conversion API

class API(database.Connector):
    ''' Class to Handle Conversion and Migration of Data between Discord & PostgreSQL '''

    def __init__(self, log: Any):
        self.log = log
        self.api_config = None

        super().__init__('leveling-api', log)

    @staticmethod
    def get_static_config() -> dict:
        config = {
            "Boosts": {
                "Values": Boosts.values,
                "Bounds": Boosts.bounds
            },
            "Leagues": {
                "Names": Leagues.names,
                "Bounds": Leagues.bounds
            },
            "Prestiges": {
                "Names": Prestiges.names,
                "Bounds": Prestiges.bounds
            },
            "Levels": {
                "0": Levels.base,
                "1": Levels.master,
                "2": Levels.elite
            }
        }

        return config

    async def update_config(self):
        query = 'SELECT settings FROM configs WHERE name = $1'
        args = ('leveling-api', )

        raw_config = await super().fetchone(query, args)

        try:
            self.api_config = json.loads(raw_config["settings"])
            self.log.trace('startup', 'Loaded Leveling API configuration from Database')
        except:
            self.api_config = self.get_static_config()
            self.log.trace('startup', 'Loaded Leveling API configuration from local file')

        return

    async def check_existing(self, *, userId: int, guildId: Optional[int]) -> bool:
        query = 'SELECT * FROM user_levels WHERE user_id = $1'
        args = (userId, )

        if guildId:
            query = 'SELECT * FROM guild_levels WHERE user_id = $1 AND guild_id = $2'
            args = (userId, guildId)

        results = await super().fetchone(query, args)
        if results:
            return True

        return False


    # Region: Data Converters

    @staticmethod
    def _batchRecords(*, guildId: Optional[int], members: List[Member], guild: bool) -> list:
        if guild:
            for member in members:
                yield (guildId, member.id, 0, 0)
        else:
            for member in members:
                yield (member.id, 0)

    @staticmethod
    def _iterate(*, value: int, bounds: list):
        pos = -1

        for bound in bounds:
            if value >= bound:
                pos += 1
            else:
                remaining = bound - value
                break

        try:
            _ = bounds[pos+1]
        except IndexError:
            next = remaining = None
        else:
            next = pos+1

        return pos, next, remaining

    @staticmethod
    def _getLevelSet(*, xp: int) -> str:
        if xp < 300000:
            return '0'
        elif xp < 1000000:
            return '1'
        else:
            return '2'

    def _getPrestige(self, *, xp: int) -> Statistic:
        bounds = self.api_config["Prestiges"]["Bounds"]
        current, next, remaining = self._iterate(value=xp, bounds=bounds)

        current = self.api_config["Prestiges"]["Names"][current]

        if not next and not remaining:
            next = remaining = 'Max Prestige Reached!'
        else:
            next = self.api_config["Prestiges"]["Names"][next]
            remaining = remaining

        prestige = Statistic(
            current = current,
            next = next,
            remaining = remaining
        )

        return prestige

    def _getLevel(self, *, xp: int, set: Optional[str]) -> Statistic:
        if not set:
            set = self._getLevelSet(xp=xp)
        if set == '0':
            xp %= 50000

        bounds = self.api_config["Levels"][set]

        i = 0
        for bound in bounds:
            if xp >= bound:
                i += 1
            elif xp < bound or i == 10:
                remaining = bound - xp
                break

        current = f'Level {i}'
        if i == 10:
            next = 'Prestige Available Soon ...'
        else:
            next = f'Level {i+1}'

        remaining = remaining

        level = Statistic(
            current = current,
            next = next,
            remaining = remaining
        )

        return level

    def _getLeague(self, *, xp: int) -> Statistic:
        bounds = self.api_config["Leagues"]["Bounds"]
        current, next, remaining = self._iterate(value=xp, bounds=bounds)

        current = self.api_config["Leagues"]["Names"][current]

        if not next and not remaining:
            next = remaining = 'Max League Achieved!'
        else:
            next = self.api_config["Leagues"]["Names"][next]
            remaining = remaining

        league = Statistic(
            current = current,
            next = next,
            remaining = remaining
        )

        return league

    def _getBoost(self, *, xp: int) -> Statistic:
        boost = Statistic()

        bounds = self.api_config["Boosts"]["Bounds"]
        current, next, remaining = self._iterate(value=xp, bounds=bounds)

        current = self.api_config["Boosts"]["Values"][current]

        if not next and not remaining:
            next = remaining = 'Max Boost Earned!'
        else:
            next = self.api_config["Boosts"]["Values"][next]
            remaining = remaining

        boost = Statistic(
            current = current,
            next = next,
            remaining = remaining
        )

        return boost

    # End Region

    # Region: Interactive Handlers

    async def fetch_boost(self, *, userId: int) -> int:
        query = 'SELECT experience FROM user_levels WHERE user_id = $1'
        args = (userId, )

        results = await super().fetchone(query, args)
        boost = self._getBoost(xp=results["experience"])

        return boost.current

    async def fetch_guild_user(self, *, guildId: int, userId: int) -> GuildUser:
        if not self.api_config:
            await self.update_config()

        query = 'SELECT * FROM guild_levels WHERE guild_id = $1 AND user_id = $2'
        args = (guildId, userId)

        results = await super().fetchone(query, args)
        experience = results['experience']

        prestige = self._getPrestige(xp=experience)
        level = self._getLevel(xp=experience, set=None)

        user = GuildUser(guildId,
            user_id = userId,
            experience = results['experience'],
            artificial = results['artificial'],
            prestige = prestige,
            level = level
        )

        return user

    async def fetch_global_user(self, *, userId: int) -> GlobalUser:
        if not self.api_config:
            await self.update_config()

        query = 'SELECT * FROM user_levels WHERE user_id = $1'
        args = (userId, )

        results = await super().fetchone(query, args)
        experience = results['experience']

        league = self._getLeague(xp=experience)
        boost = self._getBoost(xp=experience)

        user = GlobalUser(
            user_id = userId,
            experience = experience,
            league = league,
            boost = boost
        )

        return user

    async def fetch_guild_ranks(self, *, guildId: int, userId: Optional[int], limit: Optional[int]):
        '''
            Either selects the first `limit` results ordered by experience OR
            selects all records ordered by experience, and returns the position of the user specified
        '''

    async def fetch_global_ranks(self, *, userId: Optional[int], limit: Optional[int]):
        '''
            Either selects the first `limit` results ordered by experience OR
            selects all records ordered by experience and returns the position of the user specified
        '''

    async def insert_guild_user(self, *, guildId: int, userId: int) -> bool:
        overwrite = await self.check_existing(userId=userId, guildId=guildId)

        if overwrite:
            raise UserOverwriteError(f'Cannot Overwrite Index (guild, user) - ({guildId}, {userId})')

        query = 'INSERT INTO guild_levels (guild_id, user_id, experience, artificial) VALUES ($1, $2, $3, $4)'
        args = (guildId, userId, 0, 0)
        status = await super().insertone(query, args)

        return status

    async def insert_global_user(self, *, userId: int) -> bool:
        overwrite = await self.check_existing(userId=userId)

        if overwrite:
            raise UserOverwriteError(f'Cannot Overwrite Index (user) - ({userId})')

        query = 'INSERT INTO user_levels (user_id, experience) VALUES ($1, $2)'
        args = (userId, 0)
        status = await super().insertone(query, args)

        return status

    async def force_insert(self, data: tuple, *, guild: bool=False) -> bool:
        if guild:
            overwrite = await self.check_existing(userId=data[1], guildId=data[0])
            record = f'({data[0]}, {data[1]})'
        else:
            ovewrite = await self.check_existing(userId=data[0])
            record = f'({data[0]})'

        if overwrite:
            self.log.info('database', f'Overwriting Record: {record} ...')

            if guild:
                statement = 'DELETE FROM guild_levels WHERE guild_id = $1 AND user_id = $2'
                args = (data[0], data[1])
            else:
                statement = 'DELETE FROM user_levels WHERE user_id = $1'
                args = (data[0], )

            status = await super().executeone(statement, args)

        if guild:
            query = 'INSERT INTO guild_levels (guild_id, user_id, experience, artificial) VALUES ($1, $2, $3, $4)'
        else:
            query = 'INSERT INTO user_levels (user_id, experience) VALUES ($1, $2)'

        status = await super().insertone(query, data)

        return status

    async def add_experience(self, userId: int, *, guildId: Optional[int], amount: int, artificial: bool=False) -> bool:
        if guildId:
            query = 'UPDATE guild_levels SET experience + $1 WHERE guild_id = $2 AND user_id = $3'
            args = (amount, guildId, userId)

            if artificial:
                query = 'UPDATE guild_levels SET experience + $1, artificial + $1 WHERE guild_id = $2 AND user_id = $3'

            status = await super().executeone(query, args)

        if not artificial:
            query = 'UPDATE user_levels SET experience + $1 WHERE user_id = $2'
            args = (amount, userId)

            status = await super().executeone(query, args)

        if not guildId and not artificial:
            raise GlobalPermissionsError()
