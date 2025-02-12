""" py-platoo data layer """

import asyncio
from aiopg import create_pool
import psycopg2


class PGData:
    """class for py-platoo data"""

    def __init__(self, connect_info):
        """init of a class"""
        self._connect_info = connect_info
        self._mtable = "tbl"
        self.loop = asyncio.get_event_loop()
        self._pool = None

    async def pool_discard(self) -> bool:
        """pool/connection termination"""
        if self._pool:
            await self._pool.clear()
            self._pool.close()
            await self._pool.wait_closed()
            self._pool.terminate()
            return True
        return False

    async def pool_present(self) -> bool:
        """pool present"""
        if self._pool:
            return True
        return False

    async def pool_info(self) -> bool:
        """pool info"""
        if self._pool:
            print(f"Class: {self.__class__.__name__}, free : {self._pool.freesize}")
            print(f"Class: {self.__class__.__name__}, pool : {self._pool.size}")
            return True
        return False

    async def connect_pool(self) -> bool:
        """create a pool"""
        if self._pool:
            return False
        try:
            self._pool = await create_pool(
                self._connect_info, pool_recycle=True, maxsize=0
            )
        except psycopg2.OperationalError as e:
            print(f"Class: {self.__class__.__name__}, Unable to connect!\n{e}")
            return False
        return True

    async def check_connection(self) -> bool:
        """check connection"""
        if not self._pool:
            return False
        ret = None
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                ret = await cur.execute("SELECT 1")
                ret = await cur.fetchone()
                cur.close()
            await self._pool.release(conn)
        if isinstance(ret, tuple) and ret[0] == 1:
            return True
        return False

    async def check_table(self) -> bool:
        """check if table exists"""
        if not self._pool:
            return False
        ret = None
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                ret = await cur.execute(f"SELECT to_regclass('{self._mtable}')")
                ret = await cur.fetchone()
                cur.close()
            await self._pool.release(conn)
        if isinstance(ret, tuple) and ret[0] == self._mtable:
            return True
        return False

    async def drop_table(self) -> bool:
        """drop table"""
        if not self._pool:
            return False
        if not await self.check_table():
            return True
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute(f"DROP TABLE IF EXISTS {self._mtable}")
                cur.close()
            await self._pool.release(conn)
            return True
        return False

    async def create_table(self) -> bool:
        """create table"""
        if not self._pool:
            return False
        if await self.check_table():
            return False
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute(
                    f"CREATE TABLE {self._mtable} ("
                    + "id uuid DEFAULT gen_random_uuid(),"
                    + "memo VARCHAR NOT NULL,"
                    + "created TIMESTAMP NOT NULL,"
                    + "modified TIMESTAMP,"
                    + "deleted TIMESTAMP,"
                    + "PRIMARY KEY (id)"
                    + ")"
                )
                cur.close()
            await self._pool.release(conn)
            return True
        return False

    async def add_indexes(self) -> bool:
        """create indexes"""
        if not self._pool:
            return False

        if not await self.check_table():
            return False
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute(
                    f"CREATE INDEX deleted_idx ON {self._mtable} (deleted)"
                )
                cur.close()
            async with await conn.cursor() as cur:
                await cur.execute(
                    f"CREATE INDEX modified_idx ON {self._mtable} (modified)"
                )
                cur.close()
            await self._pool.release(conn)
            return True
        return False

    async def insert_one(self, value) -> str:
        """insert one"""
        if not self._pool:
            return ""
        uuid = ""
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute(
                    f"INSERT INTO {self._mtable} (memo,created,modified) VALUES (%(memo)s,now(),now()) RETURNING id;",
                    {"memo": value},
                )
                ret = await cur.fetchone()
                cur.close()
            uuid = ret[0]
            await self._pool.release(conn)
            return uuid
        return ""

    async def select_all(self) -> list:
        """select all"""
        if not self._pool:
            return []
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                # await cur.execute(f"SELECT id,memo FROM {self._imtable}")
                await cur.execute(
                    f"SELECT id,memo FROM {self._mtable} WHERE deleted IS NULL"
                )
                ret = await cur.fetchall()
                cur.close()
            await self._pool.release(conn)
            return ret
        return []

    async def delete_one(self, mid) -> bool:
        """delete one by id"""
        if not self._pool:
            return False
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                # await cur.execute(f"DELETE FROM {self._mtable} WHERE id = %(id)s",{'id':id})
                await cur.execute(
                    f"UPDATE {self._mtable} SET deleted = now() WHERE deleted IS NULL AND id = %(id)s",
                    {"id": mid},
                )
                crows = cur.rowcount
                cur.close()
            await self._pool.release(conn)
            if crows == 1:
                return True
        return False

    async def update_one(self, mid, value) -> bool:
        """update one by id"""
        if not self._pool:
            return False
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute(
                    f"UPDATE {self._mtable} SET modified = now(), memo = %(value)s WHERE id = %(id)s",
                    {"id": mid, "value": value},
                )
                cur.close()
            await self._pool.release(conn)
            return True
        return False

    async def select_all_limit_offset(self, limit, offset) -> list:
        """select by id with limit and offset"""
        if not self._pool:
            return []
        ret = []
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                if limit > 0:
                    if offset > 0:
                        await cur.execute(
                            f"SELECT id,memo FROM {self._mtable} WHERE deleted IS NULL ORDER BY modified DESC LIMIT %(lmt)s OFFSET %(ofs)s",
                            {"lmt": limit, "ofs": offset},
                        )
                    else:
                        await cur.execute(
                            f"SELECT id,memo FROM {self._mtable} WHERE deleted IS NULL ORDER BY modified DESC LIMIT %(lmt)s",
                            {"lmt": limit},
                        )
                else:
                    if offset > 0:
                        await cur.execute(
                            f"SELECT id,memo FROM {self._mtable} WHERE deleted IS NULL ORDER BY modified DESC OFFSET %(ofs)s",
                            {"ofs": offset},
                        )
                    else:
                        await cur.execute(
                            f"SELECT id,memo FROM {self._mtable} WHERE deleted IS NULL ORDER BY modified DESC"
                        )
                ret = await cur.fetchall()
                cur.close()
            await self._pool.release(conn)
            return ret
        return []

    async def count_all(self) -> int:
        """count all"""
        if not self._pool:
            return 0
        cret = []
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute(
                    f"SELECT count(*) FROM {self._mtable} WHERE deleted IS NULL"
                )
                cret = await cur.fetchone()
                cur.close()
            await self._pool.release(conn)
            if len(cret) == 1:
                return cret[0]
        return 0

    async def select_id(self, mid) -> list:
        """select by id with limit and offset"""
        if not self._pool:
            return []
        async with await self._pool.acquire() as conn:
            async with await conn.cursor() as cur:
                await cur.execute(
                    f"SELECT id,memo FROM {self._mtable} WHERE deleted IS NULL AND id = %(id)s",
                    {"id": mid},
                )
                ret = await cur.fetchall()
                cur.close()
            await self._pool.release(conn)
            return ret
        return []
