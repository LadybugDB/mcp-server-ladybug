"""Regression tests for https://github.com/LadybugDB/mcp-server-ladybug/issues/3.

`LOAD duckdb` can fail (UnicodeDecodeError on Windows with older
real_ladybug, no network for INSTALL, extension dropped, ...). The json and
duckdb extensions are optional, so DatabaseClient must still start and serve
queries when they fail to load.
"""

import pathlib

import ladybug as lb

from mcp_server_ladybug.database import DatabaseClient

RealConnection = lb.Connection


class _FailingExtensionConnection:
    """Wraps the real Connection but fails the given statements."""

    fail_statements: set = set()

    def __init__(self, db):
        self._real = RealConnection(db)

    def execute(self, query):
        if query.strip().upper() in self.fail_statements:
            # Reproduce issue #3's Windows failure mode.
            raise UnicodeDecodeError(
                "utf-8", b"\xd5", 163, 164, "invalid continuation byte"
            )
        return self._real.execute(query)

    def close(self):
        return self._real.close()


def _make_failing_connection(*statements):
    upper = {s.strip().upper() for s in statements}

    class FailingConnection(_FailingExtensionConnection):
        fail_statements = upper

    return FailingConnection


def test_client_starts_when_load_duckdb_fails(monkeypatch):
    """Exact issue #3 scenario: INSTALL ok, LOAD duckdb raises UnicodeDecodeError."""
    monkeypatch.setattr(
        lb, "Connection", _make_failing_connection("LOAD duckdb")
    )
    client = DatabaseClient(db_path=":memory:")
    try:
        out = client.query(
            "CREATE NODE TABLE Person (id INT64 PRIMARY KEY, name STRING);"
        )
        assert "Person" in out
        out = client.query("MATCH (p:Person) RETURN p.id;")
        assert "No rows" in out
    finally:
        client.close()


def test_client_starts_when_all_extension_installs_fail(monkeypatch):
    """Offline / dropped-extension scenario: every INSTALL/LOAD raises."""
    monkeypatch.setattr(
        lb,
        "Connection",
        _make_failing_connection(
            "INSTALL json", "LOAD json", "INSTALL duckdb", "LOAD duckdb"
        ),
    )
    client = DatabaseClient(db_path=":memory:")
    try:
        assert "Person" in client.query(
            "CREATE NODE TABLE Person (id INT64 PRIMARY KEY, name STRING);"
        )
    finally:
        client.close()


def test_load_extension_helper_swallows_errors(caplog):
    """_load_extension logs a warning and returns instead of raising."""
    client = DatabaseClient.__new__(DatabaseClient)

    class Boom:
        def execute(self, query):
            raise RuntimeError("boom")

    with caplog.at_level("WARNING", logger="mcp_server_ladybug"):
        client._load_extension(Boom(), "duckdb")  # must not raise

    assert any(
        "duckdb" in rec.message and "Continuing without it" in rec.message
        for rec in caplog.records
    )


def test_no_real_ladybug_references():
    """The deprecated real_ladybug package must not be referenced anymore."""
    src = pathlib.Path(__file__).resolve().parents[1]
    offenders = []
    for path in list((src / "src").rglob("*.py")) + [src / "pyproject.toml"]:
        text = path.read_text(encoding="utf-8")
        if "real_ladybug" in text or "real-ladybug" in text:
            offenders.append(str(path))
    assert not offenders, f"real_ladybug references remain: {offenders}"
