#!/usr/bin/env python3
""" manual test for Ldata """
""" moved in man_test but runs from root dir """
import asyncio
from ldata import Ldata

CONNECT_STRING = "dbname=postgres user=postgres host=127.0.0.1"


async def test1(conn) -> bool:
    """test of Ldata"""
    ld = Ldata(conn)
    print("a1")
    ret = await ld.connect_pool()
    print(ret)
    ret = await ld.check_connection()
    print(ret)
    ret = await ld.check_table()
    print(ret)
    ret = await ld.create_table()
    print(ret)
    ret = await ld.drop_table()
    print(ret)
    print("--- create table")
    ret = await ld.create_table()
    print(ret)
    print("--- adding indexes")
    ret = await ld.add_indexes()
    print(ret)
    print("ins 1")
    ret = await ld.insert_one("memo 1")
    print(ret)
    print("select ins 1")
    ret = await ld.select_id(ret)
    print(ret)
    ret = await ld.insert_one("memo 2")
    print(ret)
    ret = await ld.insert_one("memo 3")
    await ld.pool_info()
    print(ret)
    ret = await ld.insert_one("memo 4")
    print(ret)
    print("--- pool info")
    ret = await ld.pool_info()
    print(ret)
    print("---- select all ---")
    ret = await ld.select_all()
    print(ret)
    for i in ret:
        print(i)

    ret = await ld.select_all_limit_offset(2, 1)
    print(ret)
    last = None
    if ret:
        for i in ret:
            print(i)
            last = i[0]
    print(last)

    if last:
        ret = await ld.delete_one(last)
        print(ret)
        ret = await ld.delete_one(last)
        print(ret)

    ret = await ld.select_all()
    print(ret)
    for i in ret:
        print(i)

    ret = await ld.count_all()
    print(ret)

    await ld.pool_info()
    await ld.pool_discard()


asyncio.run(test1(CONNECT_STRING))
