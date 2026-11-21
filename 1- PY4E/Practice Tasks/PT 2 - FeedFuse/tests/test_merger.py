"""
Unit tests for merge modes: combine and join.
"""

from feedfuse.merger import combine, join
from feedfuse.models import SourceResult


def test_combine_success_and_failure():
    """combine includes successful data in 'data' and failed sources only in 'status'."""
    results = [
        SourceResult(name="weather", state="ok", data={"temp": 20}, ms=100),
        SourceResult(name="btc", state="timeout", error="Timed out", ms=5000),
    ]

    merged = combine(results)
    assert "weather" in merged["data"]
    assert merged["data"]["weather"] == {"temp": 20}
    assert "btc" not in merged["data"]

    assert merged["status"]["weather"]["state"] == "ok"
    assert merged["status"]["btc"]["state"] == "timeout"
    assert merged["status"]["btc"]["error"] == "Timed out"


def test_join_inner_and_left():
    """join mode correctly performs inner and left joins."""
    users = [
        {"user_id": 1, "name": "Alice"},
        {"user_id": 2, "name": "Bob"},
        {"user_id": 3, "name": "Charlie"},
    ]
    todos = [
        {"user_id": 1, "task": "Write docs"},
        {"user_id": 1, "task": "Run tests"},
        {"user_id": 2, "task": "Deploy"},
    ]

    results = [
        SourceResult(name="users", state="ok", data=users, ms=50),
        SourceResult(name="todos", state="ok", data=todos, ms=60),
    ]

    # Inner join: user 3 has no todos, so only user 1 and user 2 appear
    inner_res = join(results, on="user_id", join_type="inner")
    rows = inner_res["data"]
    assert len(rows) == 3
    user_ids = [r["user_id"] for r in rows]
    assert user_ids == [1, 1, 2]

    # Left join: user 3 is kept
    left_res = join(results, on="user_id", join_type="left")
    left_rows = left_res["data"]
    assert len(left_rows) == 4
    left_user_ids = [r["user_id"] for r in left_rows]
    assert left_user_ids == [1, 1, 2, 3]


def test_join_field_name_collision_renamed():
    """Colliding field names (other than join key) are renamed to <source>_<field>."""
    src1_data = [{"id": 1, "title": "Project A", "status": "active"}]
    src2_data = [{"id": 1, "title": "Lead Dev", "score": 95}]

    results = [
        SourceResult(name="projects", state="ok", data=src1_data, ms=10),
        SourceResult(name="roles", state="ok", data=src2_data, ms=10),
    ]

    joined = join(results, on="id", join_type="inner")
    assert len(joined["data"]) == 1
    row = joined["data"][0]
    assert row["id"] == 1
    assert row["title"] == "Project A"
    assert row["roles_title"] == "Lead Dev"
    assert row["score"] == 95
