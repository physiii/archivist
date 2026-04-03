"""Tests for chat session persistence (chat_store.py)."""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def _temp_db(monkeypatch, tmp_path):
    """Use a temporary database for each test."""
    db_path = tmp_path / "test_chat.db"
    monkeypatch.setattr("chat_store.DB_PATH", db_path)
    import chat_store
    chat_store.init_db()
    yield


def test_create_and_list_sessions():
    import chat_store
    session = chat_store.create_session("Test Session")
    assert session["id"]
    assert session["title"] == "Test Session"

    sessions = chat_store.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["id"] == session["id"]
    assert sessions[0]["title"] == "Test Session"


def test_create_multiple_sessions_ordered_by_updated():
    import chat_store
    s1 = chat_store.create_session("First")
    s2 = chat_store.create_session("Second")

    sessions = chat_store.list_sessions()
    assert len(sessions) == 2
    # Most recently created should be first
    assert sessions[0]["id"] == s2["id"]


def test_add_and_get_messages():
    import chat_store
    session = chat_store.create_session()
    chat_store.add_message(session["id"], "user", "Hello")
    chat_store.add_message(session["id"], "assistant", "Hi there!")

    messages = chat_store.get_session_messages(session["id"])
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"


def test_delete_session_cascades_messages():
    import chat_store
    session = chat_store.create_session("To Delete")
    chat_store.add_message(session["id"], "user", "Message 1")
    chat_store.add_message(session["id"], "assistant", "Response")

    chat_store.delete_session(session["id"])

    sessions = chat_store.list_sessions()
    assert len(sessions) == 0
    messages = chat_store.get_session_messages(session["id"])
    assert len(messages) == 0


def test_update_session_title():
    import chat_store
    session = chat_store.create_session("")
    assert session["title"] == ""

    chat_store.update_session_title(session["id"], "Updated Title")
    sessions = chat_store.list_sessions()
    assert sessions[0]["title"] == "Updated Title"


def test_message_count_in_list():
    import chat_store
    session = chat_store.create_session("Counted")
    for i in range(5):
        chat_store.add_message(session["id"], "user", f"msg {i}")

    sessions = chat_store.list_sessions()
    assert sessions[0]["message_count"] == 5


def test_last_message_in_list():
    import chat_store
    session = chat_store.create_session()
    chat_store.add_message(session["id"], "user", "First")
    chat_store.add_message(session["id"], "assistant", "Last message here")

    sessions = chat_store.list_sessions()
    assert "Last message" in sessions[0]["last_message"]


def test_empty_sessions_list():
    import chat_store
    sessions = chat_store.list_sessions()
    assert sessions == []


def test_messages_for_nonexistent_session():
    import chat_store
    messages = chat_store.get_session_messages("nonexistent")
    assert messages == []
