# Product notes

This project is an operator portal for AI appointment-reminder phone calls.

Clinic staff can browse synthetic patient records, start an outbound call, watch a live transcript, and review call history including summaries from the voice provider.

## Data

All bundled patient records are synthetic. Demo medical record numbers are prefixed with `DEMO-`. Never load real patient information into this app.

## Known limitations

- There is no authentication or authorization.
- Placing a real call requires Retell and OpenAI API credentials, plus a provisioned caller ID.
- Emergency detection is a model classification used to flag the live transcript. It is not a medical device or a substitute for emergency services.

## Possible follow-ups

- Filter patients with no call attempts
- Spreadsheet upload for appointment lists
- SMS or voicemail fallback after repeated failed calls
