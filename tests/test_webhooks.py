from datetime import datetime
from types import SimpleNamespace

from app.api.webhooks import RETELL_STATUS_TO_INTERNAL, _apply_call_status, _ms_to_datetime


def test_retell_status_mapping():
    assert RETELL_STATUS_TO_INTERNAL["registered"] == "initiated"
    assert RETELL_STATUS_TO_INTERNAL["ongoing"] == "initiated"
    assert RETELL_STATUS_TO_INTERNAL["ended"] == "ended"
    assert RETELL_STATUS_TO_INTERNAL["error"] == "failed"
    assert RETELL_STATUS_TO_INTERNAL["not_connected"] == "failed"


def test_apply_call_status_maps_known_values():
    call_attempt = SimpleNamespace(call_status="pending")
    _apply_call_status(call_attempt, "ended")
    assert call_attempt.call_status == "ended"


def test_apply_call_status_ignores_unknown_and_non_string_values():
    call_attempt = SimpleNamespace(call_status="initiated")
    _apply_call_status(call_attempt, "queued")
    assert call_attempt.call_status == "initiated"
    _apply_call_status(call_attempt, None)
    assert call_attempt.call_status == "initiated"


def test_ms_to_datetime_converts_epoch_milliseconds():
    result = _ms_to_datetime(1_700_000_000_000)
    assert isinstance(result, datetime)
    assert result == datetime.fromtimestamp(1_700_000_000)


def test_ms_to_datetime_rejects_invalid_input():
    assert _ms_to_datetime(None) is None
    assert _ms_to_datetime("1700000000000") is None
