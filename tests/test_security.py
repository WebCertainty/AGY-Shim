import os
import sqlite3
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from agy_shim.main import (
    build_child_environment,
    check_agy_logs_for_error,
    read_response_from_db,
)


def test_child_environment_excludes_parent_secrets(monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "secret")
    monkeypatch.setenv("AGY_TEST_PARENT_SECRET", "secret")
    monkeypatch.setenv("PATH", "test-path")

    child_env = build_child_environment()

    assert child_env["PATH"] == "test-path"
    assert child_env["AGY_SHIM_ALLOW_BYPASS"] == "1"
    assert "GITHUB_TOKEN" not in child_env
    assert "AGY_TEST_PARENT_SECRET" not in child_env


def test_conversation_id_cannot_escape_conversations_directory(tmp_path):
    conversations = tmp_path / "conversations"
    conversations.mkdir()
    outside = tmp_path / "outside.db"
    conn = sqlite3.connect(outside)
    conn.execute("CREATE TABLE steps (idx INTEGER, step_type INTEGER, step_payload BLOB)")
    conn.close()

    assert read_response_from_db(str(conversations), "../outside", -1) is None


def test_transient_auth_error_is_cleared_by_silent_auth_success(tmp_path):
    conversations = tmp_path / "antigravity-cli" / "conversations"
    log_dir = conversations.parent / "log"
    conversations.mkdir(parents=True)
    log_dir.mkdir()
    (log_dir / "cli-test.log").write_text(
        "E0608 02:21:07 server.go] You are not logged into Antigravity.\n"
        "I0608 02:21:09 auth.go] ChainedAuth: authenticated via keyring\n"
        "I0608 02:21:13 printmode.go] Print mode: silent auth succeeded\n",
        encoding="utf-8",
    )

    assert check_agy_logs_for_error(str(conversations)) is None


def test_unrecovered_auth_error_is_reported(tmp_path):
    conversations = tmp_path / "antigravity-cli" / "conversations"
    log_dir = conversations.parent / "log"
    conversations.mkdir(parents=True)
    log_dir.mkdir()
    (log_dir / "cli-test.log").write_text(
        "E0608 02:21:07 server.go] You are not logged into Antigravity.\n",
        encoding="utf-8",
    )

    assert "Not logged into Antigravity" in check_agy_logs_for_error(
        str(conversations)
    )


def test_realtime_check_can_defer_unrecovered_auth_error(tmp_path):
    conversations = tmp_path / "antigravity-cli" / "conversations"
    log_dir = conversations.parent / "log"
    conversations.mkdir(parents=True)
    log_dir.mkdir()
    (log_dir / "cli-test.log").write_text(
        "E0608 02:21:07 server.go] You are not logged into Antigravity.\n",
        encoding="utf-8",
    )

    assert (
        check_agy_logs_for_error(
            str(conversations),
            ignore_auth_errors=True,
        )
        is None
    )
