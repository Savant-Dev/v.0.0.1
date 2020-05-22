import json

from discord import Member
from os.path import exists, abspath
from typing import Union, Optional, Any, List

from . import database
from . import ConfigurationError


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

class GuildUser(object):
    def __init__(self, *, user: int, guild: int):
        self.userId = user
        self.guildId = guild

    def from_profile(self, *, data: dict) -> None:
        blocked = ['user_id', 'guild_id']

        for attribute, value in data.items():
            if attribute.lower() not in blocked:
                setattr(self, attribute, value)

        return

class GlobalUser(object):
    def __init__(self, *, user: int):
        self.userId = user


class Statistic(object):
    def __init__(self, **kwargs):
        if kwargs:
            for attribute, value in kwargs.items():
                setattr(self, attribute, value)

        return


# Database Handler & Conversion API

class API(database.Connector):
    ''' Class to Handle Conversion and Migration of Data between Discord & PostgreSQL '''

    def __init__(self, log: Any):
        self.log = log
        self.config = None

        super().__init__('leveling-api', log)

    async def update_config(self):
        query = 'SELECT settings FROM configs WHERE name = $1'
        args = ('leveling-api', )

        raw_config = await super().fetchone(query, args)

        try:
            self.config = json.loads(raw_config["settings"])
        except:
            # Load Config from Sample Config File
            pass

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
        prestige = Statistic()

        bounds = self.config["Prestiges"]["Bounds"]
        current, next, remaining = self._iterate(value=xp, bounds=bounds)

        prestige.current = self.config["Prestiges"]["Names"][current]

        if not next and not remaining:
            prestige.next = prestige.remaining = 'Max Prestige Reached!'
        else:
            prestige.next = self.config["Prestiges"]["Names"][next]
            prestige.remaining = remaining

        return prestige

    def _getLevel(self, *, xp: int, set: Optional[str]) -> Statistic:
        if not set:
            set = self._getLevelSet(xp=xp)
        if set == '0':
            xp %= 50000

        bounds = self.config["Levels"][set]

        i = 0
        for bound in bounds:
            if xp >= bound:
                i += 1
            elif xp < bound or i == 10:
                remaining = bound - xp
                break

        level = Statistic()
        level.current = f'Level {i}'
        if i == 10:
            level.next = 'Prestige Available Soon ...'
        else:
            level.next = f'Level {i+1}'

        level.remaining = remaining

        return level

    def _getLeague(self, *, xp: int) -> Statistic:
        league = Statistic()

        bounds = self.config["Leagues"]["Bounds"]
        current, next, remaining = self._iterate(value=xp, bounds=bounds)

        league.current = self.config["Leagues"]["Names"][current]

        if not next and not remaining:
            league.next = league.remaining = 'Max League Achieved!'
        else:
            league.next = self.config["Leagues"]["Names"][next]
            league.remaining = remaining

        return league

    def _getBoost(self, *, xp: int) -> Statistic:
        boost = Statistic()

        bounds = self.config["Boosts"]["Bounds"]
        current, next, remaining = self._iterate(value=xp, bounds=bounds)

        boost.current = self.config["Boosts"]["Values"][i]

        if not next and not remaining:
            boost.next = boost.remaining = 'Max Boost Earned!'
        else:
            boost.next = self.config["Boosts"]["Values"][next]
            boost.remaining = remaining

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
        if not self.config:
            await self.update_config()

        query = 'SELECT * FROM guild_levels WHERE guild_id = $1 AND user_id = $2'
        args = (guildId, userId)

        results = await super().fetchone(query, args)
        user = GuildUser(user=userId, guild=guildId)
        user.from_profile(data=dict(results))

        user.prestige = self._getPrestige(xp=user.experience)
        user.level = self._getLevel(xp=user.experience, set=None)

        return user

    async def fetch_global_user(self, *, userId: int) -> GlobalUser:
        if not self.config:
            await self.update_config()

        query = 'SELECT * FROM user_levels WHERE user_id = $1'
        args = (userId, )

        results = await super().fetchone(query, args)
        user = GlobalUser(user=userId)
        user.experience = results["experience"]

        user.league = self._getLeague(xp=user.experience)
        user.boost = self._getBoost(xp=user.experience)

        return user

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
