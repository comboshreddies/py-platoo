#!/usr/bin/env python3
import asyncio
from data_layer import Data

CONNECT_STRING = "dbname=postgres user=postgres host=127.0.0.1"


async def test1(conn) -> bool:
    """test of Ldata"""
    dh = Data(conn)
    print("a1")
    ret1 = await dh.connect_pool()
    print(ret1)
    ret2 = await dh.check_connection()
    print(ret2)
    ret3 = await dh.check_table()
    print(ret3)
    ret4 = await dh.create_table()
    print(ret4)
    ret5 = await dh.drop_table()
    print(ret5)
    print("--- create table")
    ret6 = await dh.create_table()
    print(ret6)
    print("--- adding indexes")
    ret7 = await dh.add_indexes()
    print(ret7)
    print("ins 1")
    ret8 = await dh.insert_one("memo 1")
    print(ret8)
    print("select ins 1")
    ret9 = await dh.select_id(ret8)
    print(ret9)
    ret10 = await dh.insert_one("memo 2")
    print(ret10)
    ret11 = await dh.insert_one("memo 3")
    await dh.pool_info()
    print(ret11)
    ret12 = await dh.insert_one("memo 4")
    print(ret12)
    print("--- pool info")
    ret13 = await dh.pool_info()
    print(ret13)
    print("---- select all ---")
    ret14 = await dh.select_all()
    print(ret14)
    for i in ret14:
        print(i)

    ret15 = await dh.select_all_limit_offset(2, 1)
    print(ret15)
    last = None
    if ret15:
        for i in ret15:
            print(i)
            last = i[0]
    print(last)

    if last:
        ret16 = await dh.delete_one(last)
        print(ret16)
        ret17 = await dh.delete_one(last)
        print(ret17)

    ret18 = await dh.select_all()
    print(ret18)
    for i in ret18:
        print(i)

    ret19 = await dh.count_all()
    print(ret19)

    await dh.pool_info()
    await dh.pool_discard()
    return True


asyncio.run(test1(CONNECT_STRING))
