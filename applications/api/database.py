import asyncpg
import asyncio

from typing import Optional, Any, List

from . import server_address, access_port


class Connector():
    ''' An Asynchronous Connection Handler for PostgreSQL '''

    def __init__(self, child: str, log: Any):
        self.log = log
        self.child = child
        self.database = None

    async def load_connection(self) -> None:
        self.database = await asyncpg.connect(
            user = self.child,
            password = self.child,
            database = 'project-s',

            host = server_address,
            port = access_port
        )

        self.log.info('database', f'Logged into Database as "{self.child}"')


    # Region: Interface Functions

    async def fetchone(self, query: str, args: Optional[tuple]) -> Optional[asyncpg.Record]:
        if not self.database:
            await self.load_connection()

        row = await self.database.fetchrow(query, *args)
        return row

    async def fetchmany(self, query: str, args: Optional[tuple], *, limit: Optional[int]) -> List[asyncpg.Record]:
        if not self.database:
            await self.load_connection()

        rows = await self.database.fetch(query, *args)
        if limit:
            return rows[:limit]

        return rows

    async def fetchall(self, query: str, args: Optional[tuple]) -> List[asyncpg.Record]:
        if not self.database:
            await self.load_connection()

        rows = await self.database.fetch(query, *args)
        return rows

    async def insertone(self, statement: str, args: tuple) -> bool:
        if not self.database:
            await self.load_connection()

        operation = await self.database.execute(statement, *args)
        status = bool(int(operation[-1:]))

        return status

    async def insertmany(self, table: str, args: List[tuple]) -> int:
        if not self.database:
            await self.load_connection()

        operation = await self.database.copy_records_to_table(table, records=args)
        status = int(operation[-1:])

        return status

    async def executeone(self, query: str, args: tuple) -> int:
        if not self.database:
            await self.load_connection()

        operation = await self.database.execute(query, *args)
        status = bool(int(operation[-1:]))

        return status

    async def executemany(self, statement: str, args: List[tuple]) -> None:
        if not self.database:
            await self.load_connection()

        return await self.database.executemany(query, args)
        
