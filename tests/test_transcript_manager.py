from unittest.mock import MagicMock

import pytest

from app.logic.transcript_manager import TranscriptManager


@pytest.fixture
def manager() -> TranscriptManager:
    return TranscriptManager()


async def test_replace_transcript_builds_snapshot_and_normalizes_roles(manager: TranscriptManager):
    await manager.replace_transcript(
        "call-1",
        [
            {"role": "agent", "content": "How may I help you?"},
            {"role": "patient", "content": "I have chest pain."},
        ],
    )

    messages = manager._messages["call-1"]
    assert [message["role"] for message in messages] == ["agent", "user"]
    assert messages[1]["content"] == "I have chest pain."


async def test_set_emergency_latches_true(manager: TranscriptManager):
    await manager.set_emergency("call-1", True)
    assert manager._emergency_status["call-1"] is True

    await manager.set_emergency("call-1", False)
    assert manager._emergency_status["call-1"] is True


def test_persist_skips_unknown_call_and_clears_memory(manager: TranscriptManager):
    manager._messages["call-missing"] = [
        {
            "call_id": "call-missing",
            "role": "agent",
            "content": "Hello",
            "timestamp": "2026-01-01T00:00:00+00:00",
        }
    ]
    manager._emergency_status["call-missing"] = True

    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = None

    manager.persist("call-missing", db)

    db.add.assert_not_called()
    db.commit.assert_not_called()
    assert "call-missing" not in manager._messages
    assert "call-missing" not in manager._emergency_status
