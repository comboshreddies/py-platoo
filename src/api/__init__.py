""" example quart web app """

from os import getenv
from sys import exit as sys_exit
from uuid import UUID
import asyncio
from dataclasses import dataclass
from quart import Quart, request, render_template
from quart_schema import QuartSchema, validate_request
from quart_schema import validate_response, validate_querystring
from quart_schema import RequestSchemaValidationError, DataSource
from hypercorn.asyncio import serve
from hypercorn.config import Config
from data_layer import Data

L_VERSION = "v1"

app = Quart(__name__)


QuartSchema(app,swagger_ui_path=getenv('OAPI_DOCS'),openapi_path=getenv('OAPI_JSON'))

DATA_ONE = False


def quart_run() -> None:  # pragma: no cover
    """web server entry no async"""
    app.run(host="127.0.0.1", port=5000)


async def run() -> None:  # pragma: no cover
    """web server entry async"""
    config = Config()
    config.bind = ["localhost:8040"]
    asyncio.run(serve(app, config))


@app.before_serving
async def setup() -> None:
    """setup of db connection"""
    global DATA_ONE
    connect_string = getenv("PG_CONNECT")
    if not connect_string:
        print("no connect string, exiting")
        sys_exit(1)
    DATA_ONE = Data(connect_string)
    if not await DATA_ONE.connect_pool():
        print("unable to create pool, exiting")
        sys_exit(2)
    if not await DATA_ONE.check_connection():
        print("unable to verify connection, exiting")
        sys_exit(3)
    if not await DATA_ONE.check_table():
        print("no expected table found, creating")
        if not await DATA_ONE.create_table():
            print("failed on table creation, exiting")
            sys_exit(4)
        if not await DATA_ONE.add_indexes():
            print("failed to add indexes, exiting")
            sys_exit(5)


@app.after_serving
async def cleanup() -> None:
    """cleanup"""
    global DATA_ONE
    await DATA_ONE.pool_discard()


@app.get("/")
async def serve_rendered_html() -> str:
    """serve basic html that works without js"""
    global DATA_ONE
    cnt = await DATA_ONE.count_all()
    print(cnt)
    ret = await DATA_ONE.select_all_limit_offset(0, 0)
    render = await render_template("memo_template.html", items=ret, total_items=cnt)
    return render, 200


@app.get("/dynamic")
async def serve_js_html() -> str:
    """serving html that requires js"""
    render = await render_template("memo_template.html", items=[], total_items=0)
    return render, 200


@dataclass
class DbHealth:
    """data class for DbHealth"""

    db_status: bool


@app.get("/health/db")
@validate_response(DbHealth)
async def check_db_health() -> DbHealth:
    """db health check select 1"""
    global DATA_ONE
    if await DATA_ONE.check_connection():
        return DbHealth(db_status=True), 200
    return DbHealth(db_status=False), 400


@dataclass
class AppHealth:
    """data class for AppHealth"""

    app_status: bool


@app.get("/health/app")
@validate_response(AppHealth)
async def check_app_health() -> AppHealth:
    """app health check"""
    global DATA_ONE
    if await DATA_ONE.pool_present():
        return AppHealth(app_status=True), 200
    return AppHealth(app_status=False), 400


@dataclass
class MemoListIn:
    """data class for MemoIn"""

    offset: int | None = 0
    limit: int | None = 0
    nodata: int | None = 0


@dataclass
class MemoItem:
    """data class for MemoItem"""

    uuid: str
    memo: str


@dataclass
class MemoListOut:
    """data class for MemoList Out"""

    count: int
    limit: int
    offset: int
    items: list[MemoItem]


@app.get(f"/memos/{L_VERSION}")
@validate_querystring(MemoListIn)
@validate_response(MemoListOut)
async def get_memos(query_args: MemoListIn) -> MemoListOut:
    """return memos list"""
    global DATA_ONE
    if query_args.nodata:
        ret = await DATA_ONE.count_all()
        return MemoListOut(count=ret, limit=0, offset=0, items=[])
    ret = await DATA_ONE.select_all_limit_offset(query_args.limit, query_args.offset)
    ret_list = []
    for item in ret:
        x = MemoItem(memo=item[1], uuid=item[0])
        ret_list.append(x)
    return (
        MemoListOut(
            count=len(ret_list),
            limit=query_args.limit,
            offset=query_args.offset,
            items=ret_list,
        ),
        200,
    )


@dataclass
class MemoIn:
    """data class for Memo In"""

    memo: str


@dataclass
class MemoOut:
    """data class for Memo Out"""

    uuid: str


@app.post(f"/memos/{L_VERSION}")
@validate_request(MemoIn)
@validate_response(MemoOut)
async def add_memo_versioned(data: MemoIn) -> MemoOut:
    """add new memo"""
    global DATA_ONE
    ret = await DATA_ONE.insert_one(data.memo)
    return MemoOut(uuid=ret)


@app.post("/addMemo")
@validate_request(MemoIn, source=DataSource.FORM)
@validate_response(MemoOut)
async def html_add_memo2(data: MemoIn) -> MemoOut:
    """add new memo, html form submit endpoint"""
    global DATA_ONE
    ret = await DATA_ONE.insert_one(data.memo)
    return MemoOut(uuid=ret)


@dataclass
class MemoDelIn:
    """data class for MemoDel In"""

    uuid: str


@dataclass
class MemoDelOut(MemoDelIn):
    """data class for MemoDel Out"""

    success: bool


@app.delete(f"/memos/{L_VERSION}/<string:uuid>")
@validate_response(MemoDelOut)
async def delete_memo_2(uuid) -> MemoDelOut:
    """add new memo"""
    global DATA_ONE
    try:
        UUID(uuid)
    except ValueError:
        return MemoGetOut(memo="invalid uuid", uuid=uuid), 400

    ret = await DATA_ONE.delete_one(uuid)
    return MemoDelOut(success=ret, uuid=uuid)


@dataclass
class MemoGetIn:
    """data class for MemoDel In"""

    uuid: str


@dataclass
class MemoGetOut(MemoDelIn):
    """data class for MemoDel Out"""

    memo: str


@app.get(f"/memos/{L_VERSION}/<string:uuid>")
@validate_response(MemoGetOut)
async def get_memo(uuid) -> MemoGetOut:
    """add new memo"""
    global DATA_ONE
    try:
        UUID(uuid)
    except ValueError:
        return MemoGetOut(memo="invalid uuid", uuid=uuid), 400
    ret = await DATA_ONE.select_id(uuid)
    if len(ret) == 1 and len(ret[0]) == 2:
        return MemoGetOut(memo=ret[0][1], uuid=uuid), 200
    return MemoGetOut(memo="", uuid=uuid), 400


@app.errorhandler(RequestSchemaValidationError)
async def handle_request_validation_error(error):
    """providing more or less verbose validation messages"""
    if getenv("VERBOSE_VALIDATION"):
        return {"errors": str(error.validation_error)}, 400
    return {"error": "Validation"}, 400
