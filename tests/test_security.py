import os
import sqlite3
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(TESTS_DIR)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from agy_shim.main import build_child_environment, read_response_from_db


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
