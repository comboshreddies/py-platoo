""" example quart web app """

from os import getenv
from sys import exit as sys_exit
from uuid import UUID
import asyncio
from dataclasses import dataclass
from quart import Quart, render_template
from quart_schema import QuartSchema, validate_request
from quart_schema import validate_response, validate_querystring
from quart_schema import RequestSchemaValidationError, DataSource
from hypercorn.asyncio import serve
from hypercorn.config import Config
from data_layer import Data
import importlib.metadata


API_VERSION = "v1"
APP_NAME = "memo"

app = Quart(__name__)


QuartSchema(app, swagger_ui_path=getenv("OAPI_DOCS"), openapi_path=getenv("OAPI_JSON"))

DATA_ONE = Data(getenv("PG_CONNECT"))


def quart_run() -> None:  # pragma: no cover
    """web server entry no async"""
    port = os.getenv("QUART_PORT")
    if not port:
        port = 5000
    app.run(host="127.0.0.1", port=port)


async def run() -> None:  # pragma: no cover
    """web server entry async"""
    config = Config()
    port = os.getenv("HYPERCORN_PORT")
    if not port:
        port = 8040
    config.bind = [f"127.0.0.1:{port}"]
    try:
        asyncio.run(serve(app, config))
    except hypercorn.utils.LifespanFailureError(e):
        print("---------------")
        print(e)


@app.before_serving
async def setup() -> None:
    """setup of db connection"""
    global DATA_ONE
    connect_string = getenv("PG_CONNECT")
    if not connect_string:
        print("before_serving: no data connect string, exiting")
        sys_exit(1)
    if connect_string == "NO_DATA_RUN":
        return True
    if not DATA_ONE:
        print(f"before_serving: no data class, exiting")
        sys_exit(2)
    if not await DATA_ONE.connect_pool():
        print("before_serving: unable to create database pool, exiting")
        sys_exit(3)
    if not await DATA_ONE.check_connection():
        print("before_serving: unable to verify database connection, exiting")
        sys_exit(4)
    if not await DATA_ONE.check_table():
        print("no expected table found, creating")
        if not await DATA_ONE.create_table():
            print("before_serving: failed on table creation, exiting")
            sys_exit(5)
        if not await DATA_ONE.add_indexes():
            print("before_serving: failed to add indexes, exiting")
            sys_exit(6)


@app.after_serving
async def cleanup() -> None:
    """cleanup"""
    global DATA_ONE
    await DATA_ONE.pool_discard()


@app.get("/")
async def serve_rendered_html() -> tuple[str, int]:
    """serve basic html that works without js"""
    global DATA_ONE
    cnt = await DATA_ONE.count_all()
    print(cnt)
    ret = await DATA_ONE.select_all_limit_offset(0, 0)
    render = await render_template("memo_template.html", items=ret, total_items=cnt, name=APP_NAME, version=importlib.metadata.version(APP_NAME))
    return render, 200


@app.get("/dynamic")
async def serve_js_html() -> tuple[str, int]:
    """serving html that requires js"""
    render = await render_template("memo_template.html", items=[], total_items=0, name=APP_NAME, version=importlib.metadata.version(APP_NAME))
    return render, 200


@dataclass
class ApiVersion:
    """data class for ApiVersion"""

    api_version: str
    name: str


@app.get("/version/api")
@validate_response(ApiVersion)
async def api_version() -> tuple[ApiVersion, int]:
    """api version"""
    return ApiVersion(api_version=importlib.metadata.version(APP_NAME),name=APP_NAME), 200


@dataclass
class DbHealth:
    """data class for DbHealth"""

    db_status: bool


@app.get("/health/db")
@validate_response(DbHealth)
async def check_db_health() -> tuple[DbHealth, int]:
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
async def check_app_health() -> tuple[AppHealth, int]:
    """app health check"""
    global DATA_ONE
    if await DATA_ONE.pool_present():
        return AppHealth(app_status=True), 200
    return AppHealth(app_status=False), 400


@dataclass
class MemoListIn:
    """data class for MemoIn"""

    offset: int = 0
    limit: int = 0
    nodata: int = 0


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


@app.get(f"/memos/{API_VERSION}")
@validate_querystring(MemoListIn)
@validate_response(MemoListOut)
async def get_memos(query_args: MemoListIn) -> tuple[MemoListOut, int]:
    """return memos list"""
    global DATA_ONE
    if query_args.nodata:
        return (
            MemoListOut(count=await DATA_ONE.count_all(), limit=0, offset=0, items=[]),
            200,
        )
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


@app.post(f"/memos/{API_VERSION}")
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


@app.delete(f"/memos/{API_VERSION}/<string:uuid>")
@validate_response(MemoDelOut)
async def delete_memo_2(uuid) -> tuple[MemoDelOut, int]:
    """add new memo"""
    global DATA_ONE
    try:
        UUID(uuid)
    except ValueError:
        return MemoDelOut(success=False, uuid=uuid), 400

    ret = await DATA_ONE.delete_one(uuid)
    return MemoDelOut(success=ret, uuid=uuid), 200


@dataclass
class MemoGetIn:
    """data class for MemoDel In"""

    uuid: str


@dataclass
class MemoGetOut(MemoDelIn):
    """data class for MemoDel Out"""

    memo: str


@app.get(f"/memos/{API_VERSION}/<string:uuid>")
@validate_response(MemoGetOut)
async def get_memo(uuid) -> tuple[MemoGetOut, int]:
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
async def handle_request_validation_error(error) -> tuple[dict, int]:
    """providing more or less verbose validation messages"""
    if getenv("VERBOSE_VALIDATION"):
        return {"errors": str(error.validation_error)}, 400
    return {"error": "Validation"}, 400
