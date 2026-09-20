import { useState, type FormEvent } from 'react'
import { createPatient, type Patient, type PatientCreatePayload } from '../api'

type AddPatientModalProps = {
  open: boolean
  onClose: () => void
  onCreated: (patient: Patient) => void
}

const EMPTY_FORM: PatientCreatePayload = {
  first_name: '',
  last_name: '',
  date_of_birth: '',
  phone_number: '',
  home_address: '',
  insurance_number: '',
  medical_record_number: '',
  appointment_date: '',
  appointment_time: '',
  timezone: 'America/New_York',
}

const FIELD_LABELS: { key: keyof PatientCreatePayload; label: string; type: string }[] = [
  { key: 'first_name', label: 'First name', type: 'text' },
  { key: 'last_name', label: 'Last name', type: 'text' },
  { key: 'date_of_birth', label: 'Date of birth', type: 'date' },
  { key: 'phone_number', label: 'Phone number', type: 'tel' },
  { key: 'home_address', label: 'Home address', type: 'text' },
  { key: 'insurance_number', label: 'Insurance number', type: 'text' },
  { key: 'medical_record_number', label: 'Medical record number', type: 'text' },
  { key: 'appointment_date', label: 'Appointment date', type: 'date' },
  { key: 'appointment_time', label: 'Appointment time', type: 'time' },
  { key: 'timezone', label: 'Timezone', type: 'text' },
]

export function AddPatientModal({ open, onClose, onCreated }: AddPatientModalProps) {
  const [form, setForm] = useState<PatientCreatePayload>(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (!open) {
    return null
  }

  function updateField(key: keyof PatientCreatePayload, value: string) {
    setForm((current) => ({ ...current, [key]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitting(true)
    setError(null)

    try {
      const patient = await createPatient(form)
      setForm(EMPTY_FORM)
      onCreated(patient)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create patient')
    } finally {
      setSubmitting(false)
    }
  }

  function handleClose() {
    if (submitting) {
      return
    }
    setError(null)
    setForm(EMPTY_FORM)
    onClose()
  }

  return (
    <div className="modal-backdrop" role="presentation" onClick={handleClose}>
      <div
        className="modal-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-patient-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <h2 id="add-patient-title">Add Patient</h2>
          <button
            type="button"
            className="modal-close-button"
            onClick={handleClose}
            disabled={submitting}
            aria-label="Close"
          >
            ×
          </button>
        </div>

        <form className="modal-form" onSubmit={(event) => void handleSubmit(event)}>
          <div className="modal-fields">
            {FIELD_LABELS.map(({ key, label, type }) => (
              <label key={key} className="modal-field">
                <span>{label}</span>
                <input
                  type={type}
                  name={key}
                  value={form[key]}
                  onChange={(event) => updateField(key, event.target.value)}
                  required
                  disabled={submitting}
                />
              </label>
            ))}
          </div>

          {error ? <p className="status-message error">{error}</p> : null}

          <div className="modal-actions">
            <button
              type="button"
              className="secondary-button"
              onClick={handleClose}
              disabled={submitting}
            >
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={submitting}>
              {submitting ? 'Saving...' : 'Save Patient'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
