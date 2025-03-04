""" tests for echo and todos paths """

from api import app, MemoIn


async def test_echo() -> None:
    """echo path test"""
    test_client = app.test_client()
    response = await test_client.post("/echo", json={"a": "b"})
    data = await response.get_json()
    assert data == {"extra": True, "input": {"a": "b"}}


async def test_create_todo() -> None:
    """todos path test"""
    test_client = app.test_client()
    response = await test_client.post("/todos/", json=MemoIn(memo="Abc"))
    data = await response.get_json()
    assert data == {"id": 1, "task": "Abc"}
