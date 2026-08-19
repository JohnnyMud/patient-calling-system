import logging
import os
from datetime import datetime

from retell import Retell
from sqlalchemy.orm import Session

from app.models import CallAttempts, Patients

logger = logging.getLogger(__name__)

retell_client = Retell(
    api_key=os.getenv("RETELL_API_KEY")
)

def initiate_retell_call(patient: Patients):
    from_number = os.getenv("RETELL_FROM_NUMBER")
    if not from_number:
        logger.error("RETELL_FROM_NUMBER is not configured")
        return False

    try:
        response = retell_client.call.create_phone_call(
            from_number=from_number,
            to_number=patient.phone_number,
            retell_llm_dynamic_variables={
                "patient_name": patient.first_name + " " + patient.last_name,
                "appointment_date": patient.appointment_date.strftime("%Y-%m-%d"),
                "appointment_time": patient.appointment_time.strftime("%H:%M"),
            }
        )
        logger.info("Call initiated: %s", response.call_id)
        return response
    except Exception:
        logger.exception("Error making call")
        return False

def create_call_attempt(patient_id: str, db: Session):
    record = CallAttempts(
        patient_id=patient_id,
        created_at=datetime.now(),
        call_status="pending"
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def call_patient(patient: Patients, db: Session):
    patient_id = patient.id
    call_attempt = create_call_attempt(patient_id, db)
    call_succeeded = initiate_retell_call(patient)

    if not call_succeeded:
        call_attempt.call_status = "failed"
        db.commit()
        db.refresh(call_attempt)

    if call_succeeded:
        retell_call_id = call_succeeded.call_id
        call_attempt.call_status = "initiated"
        call_attempt.retell_call_id = retell_call_id
        db.commit()
        db.refresh(call_attempt)

    return call_attempt
