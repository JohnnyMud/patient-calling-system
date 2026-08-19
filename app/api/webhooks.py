from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CallAttempts

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Map Retell call_status values onto the statuses used by the UI.
RETELL_STATUS_TO_INTERNAL = {
    "registered": "initiated",
    "ongoing": "initiated",
    "ended": "ended",
    "error": "failed",
    "not_connected": "failed",
}


def _ms_to_datetime(timestamp_ms: object) -> datetime | None:
    if not isinstance(timestamp_ms, (int, float)):
        return None
    return datetime.fromtimestamp(timestamp_ms / 1000)


def _find_call_attempt(db: Session, call_id: str) -> CallAttempts | None:
    return (
        db.query(CallAttempts)
        .filter(CallAttempts.retell_call_id == call_id)
        .first()
    )


def _apply_call_status(call_attempt: CallAttempts, retell_status: object) -> None:
    if not isinstance(retell_status, str):
        return
    mapped = RETELL_STATUS_TO_INTERNAL.get(retell_status)
    if mapped is not None:
        call_attempt.call_status = mapped


@router.post("/retell", status_code=status.HTTP_200_OK)
async def retell_webhook(
    payload: dict,
    db: Session = Depends(get_db),
):
    # Retell payload shape: {"event": "...", "call": {...}}
    event = payload.get("event")
    call = payload.get("call")
    if not isinstance(call, dict):
        return {"message": "Webhook received"}

    call_id = call.get("call_id")
    if not isinstance(call_id, str) or not call_id:
        return {"message": "Webhook received"}

    call_attempt = _find_call_attempt(db, call_id)
    if call_attempt is None:
        # Acknowledge unknown calls so Retell does not retry forever.
        return {"message": "Webhook received"}

    if event == "call_started":
        _apply_call_status(call_attempt, call.get("call_status") or "ongoing")
        started_at = _ms_to_datetime(call.get("start_timestamp"))
        if started_at is not None:
            call_attempt.started_at = started_at

    elif event == "call_ended":
        # call_ended includes full call object except call_analysis.
        _apply_call_status(call_attempt, call.get("call_status"))

        started_at = _ms_to_datetime(call.get("start_timestamp"))
        ended_at = _ms_to_datetime(call.get("end_timestamp"))
        if started_at is not None:
            call_attempt.started_at = started_at
        if ended_at is not None:
            call_attempt.ended_at = ended_at

        duration_ms = call.get("duration_ms")
        if isinstance(duration_ms, (int, float)):
            call_attempt.call_duration = int(duration_ms / 1000)

        recording_url = call.get("recording_url")
        if isinstance(recording_url, str) and recording_url:
            call_attempt.recording_url = recording_url

    elif event == "call_analyzed":
        # Summary/success arrive here, not on call_ended.
        _apply_call_status(call_attempt, call.get("call_status"))

        analysis = call.get("call_analysis")
        if isinstance(analysis, dict):
            summary = analysis.get("call_summary")
            if isinstance(summary, str) and summary:
                call_attempt.summary = summary

            successful = analysis.get("call_successful")
            if isinstance(successful, bool):
                call_attempt.successful = successful

    db.commit()
    return {"message": "Webhook received"}
