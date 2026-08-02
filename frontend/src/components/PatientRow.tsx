import type { Patient } from '../api'

type PatientRowProps = {
  patient: Patient
  selected: boolean
  deleting: boolean
  onSelect: (patientId: string) => void
  onDelete: (patientId: string) => void
}

function formatDate(value: string): string {
  const date = new Date(`${value}T00:00:00`)
  return date.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatTime(value: string): string {
  const [hours, minutes] = value.split(':')
  const date = new Date()
  date.setHours(Number(hours), Number(minutes), 0, 0)
  return date.toLocaleTimeString(undefined, {
    hour: 'numeric',
    minute: '2-digit',
  })
}

function TrashIcon() {
  return (
    <svg
      className="patient-delete-icon"
      viewBox="0 0 16 16"
      aria-hidden="true"
      focusable="false"
    >
      <path
        fill="currentColor"
        d="M6.5 1.5h3a.5.5 0 0 1 .5.5v1h3v1.25H2.5V3H5.5V2a.5.5 0 0 1 .5-.5Zm.75 1V3h1.5v-.5h-1.5ZM3.75 5.5h8.5l-.55 8.05A1.25 1.25 0 0 1 10.46 14.7H5.54a1.25 1.25 0 0 1-1.24-1.15L3.75 5.5Zm2 .75-.35 6h1.1l.35-6H5.75Zm2.35 0-.05 6h1.1l-.05-6H8.1Zm2.15 0-.35 6h1.1l.35-6h-1.1Z"
      />
    </svg>
  )
}

export function PatientRow({
  patient,
  selected,
  deleting,
  onSelect,
  onDelete,
}: PatientRowProps) {
  return (
    <tr
      className={selected ? 'patient-row selected' : 'patient-row'}
      onClick={() => onSelect(patient.id)}
    >
      <td>
        <input
          type="radio"
          name="selected-patient"
          checked={selected}
          onChange={() => onSelect(patient.id)}
          aria-label={`Select ${patient.first_name} ${patient.last_name}`}
        />
      </td>
      <td>
        <div className="patient-name">
          {patient.first_name} {patient.last_name}
        </div>
        <div className="patient-meta">{patient.medical_record_number}</div>
      </td>
      <td>{patient.phone_number}</td>
      <td>
        <div>{formatDate(patient.appointment_date)}</div>
        <div className="patient-meta">
          {formatTime(patient.appointment_time)} ({patient.timezone})
        </div>
      </td>
      <td className="patient-actions">
        <button
          type="button"
          className="patient-delete-button"
          disabled={deleting}
          aria-label={`Delete ${patient.first_name} ${patient.last_name}`}
          onClick={(event) => {
            event.stopPropagation()
            onDelete(patient.id)
          }}
        >
          <TrashIcon />
        </button>
      </td>
    </tr>
  )
}
