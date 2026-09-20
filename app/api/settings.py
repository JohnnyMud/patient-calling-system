from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.llm.settings_store import (
    SUPPORTED_PROVIDERS,
    load_settings_row,
    normalize_provider,
    settings_to_read_dict,
    upsert_settings,
)
from app.schemas import LlmSettingsRead, LlmSettingsUpdate

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("/llm", response_model=LlmSettingsRead)
def get_llm_settings(db: Session = Depends(get_db)):
    row = load_settings_row(db)
    return settings_to_read_dict(row)


@router.put("/llm", response_model=LlmSettingsRead)
def put_llm_settings(payload: LlmSettingsUpdate, db: Session = Depends(get_db)):
    if payload.provider is not None:
        try:
            normalize_provider(payload.provider)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

    if payload.provider is None and payload.model is None and payload.api_key is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of provider, model, or api_key must be provided",
        )

    if payload.provider is not None and payload.provider.lower() not in SUPPORTED_PROVIDERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported LLM provider: {payload.provider}",
        )

    row = upsert_settings(
        db,
        provider=payload.provider,
        model=payload.model,
        api_key=payload.api_key,
    )
    return settings_to_read_dict(row)
