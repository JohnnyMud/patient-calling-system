import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.db import SessionLocal
from app.llm.factory import get_llm_provider
from app.logic.transcript_manager import transcript_manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/websocket", tags=["websocket"])

OPENAI_SYSTEM_PROMPT = (
    "You are a helpful, concise phone agent for patient appointment reminder "
    "calls. Keep responses brief, natural, and easy to understand over the phone."
)
EMERGENCY_DETECTOR_PROMPT = (
    "Determine whether the patient is currently describing a medical emergency "
    "that needs immediate help. Examples include severe chest pain, trouble "
    "breathing, stroke symptoms, uncontrolled bleeding, loss of consciousness, "
    "overdose, or immediate risk of self-harm. Use the full conversation for "
    "context. Do not classify routine symptoms, scheduling questions, or past "
    "resolved events as current emergencies."
)


def extract_transcript_message(payload: dict) -> tuple[str, str] | None:
    content = (
        payload.get("transcript")
        or payload.get("content")
        or payload.get("text")
        or payload.get("message")
    )
    if not isinstance(content, str):
        return None

    raw_role = payload.get("role") or payload.get("speaker") or payload.get("source")
    role = str(raw_role or "agent").lower()
    if role in {"user", "patient", "caller"}:
        role = "user"
    else:
        role = "agent"

    return role, content


def should_persist_transcript(payload: dict) -> bool:
    return bool(
        payload.get("end_call")
        or payload.get("call_ended")
        or payload.get("event") in {"call_ended", "call_finished"}
    )


def is_response_required(payload: dict) -> bool:
    return payload.get("interaction_type") == "response_required"


def normalize_transcript_role(raw_role: str | None) -> str:
    role = str(raw_role or "agent").lower()
    if role in {"user", "patient", "caller"}:
        return "user"
    return "assistant"


def extract_transcript_messages(payload: dict) -> list[dict[str, str]]:
    transcript = payload.get("transcript")
    if not isinstance(transcript, list):
        transcript_message = extract_transcript_message(payload)
        if transcript_message is None:
            return []

        role, content = transcript_message
        return [{"role": "user" if role == "user" else "assistant", "content": content}]

    messages: list[dict[str, str]] = []
    for item in transcript:
        if not isinstance(item, dict):
            continue

        content = item.get("content")
        if not isinstance(content, str) or not content.strip():
            continue

        messages.append(
            {
                "role": normalize_transcript_role(item.get("role")),
                "content": content.strip(),
            }
        )

    return messages


def generate_reply_sync(messages: list[dict[str, str]]) -> str:
    provider = get_llm_provider()
    return provider.generate_reply(messages, OPENAI_SYSTEM_PROMPT)


def detect_emergency_sync(messages: list[dict[str, str]]) -> bool:
    provider = get_llm_provider()
    return provider.detect_emergency(messages, EMERGENCY_DETECTOR_PROMPT)


async def generate_agent_response(messages: list[dict[str, str]]) -> str:
    return await asyncio.to_thread(generate_reply_sync, messages)


async def detect_emergency(messages: list[dict[str, str]]) -> bool:
    if not any(message.get("role") == "user" for message in messages):
        return False

    try:
        return await asyncio.to_thread(detect_emergency_sync, messages)
    except Exception:
        logger.exception("Emergency detection failed")
        return False


async def retell_agent_websocket(websocket: WebSocket, call_id: str):
    await websocket.accept()

    first_event = {
        "response_id": 0,
        "content": "How may I help you?",
        "content_complete": True,
        "end_call": False,
    }
    await websocket.send_text(json.dumps(first_event))
    await transcript_manager.publish(call_id, "agent", first_event["content"])

    try:
        while True:
            message = await websocket.receive_text()
            request = json.loads(message)
            transcript = request.get("transcript")
            if isinstance(transcript, list):
                await transcript_manager.replace_transcript(call_id, transcript)
            else:
                transcript_message = extract_transcript_message(request)
                if transcript_message is not None:
                    role, content = transcript_message
                    await transcript_manager.publish(call_id, role, content)

            if should_persist_transcript(request):
                break

            if is_response_required(request):
                messages = extract_transcript_messages(request)
                response_content, is_emergency = await asyncio.gather(
                    generate_agent_response(messages),
                    detect_emergency(messages),
                )
                await transcript_manager.set_emergency(call_id, is_emergency)
                response_event = {
                    "response_id": request.get("response_id"),
                    "content": response_content,
                    "content_complete": True,
                    "end_call": False,
                }
                await websocket.send_text(json.dumps(response_event))
                await transcript_manager.publish(call_id, "agent", response_content)
    except WebSocketDisconnect:
        pass
    finally:
        db = SessionLocal()
        try:
            transcript_manager.persist(call_id, db)
        finally:
            db.close()


@router.websocket("/llm-websocket/{call_id}")
async def websocket_handler(websocket: WebSocket, call_id: str):
    await retell_agent_websocket(websocket, call_id)


@router.websocket("/live-transcript/{call_id}")
async def live_transcript(websocket: WebSocket, call_id: str):
    await transcript_manager.connect(call_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        transcript_manager.disconnect(call_id, websocket)
