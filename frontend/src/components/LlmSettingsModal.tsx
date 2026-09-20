import { useEffect, useState, type FormEvent } from 'react'
import {
  fetchLlmSettings,
  updateLlmSettings,
  type LlmProvider,
  type LlmSettings,
} from '../api'

type LlmSettingsModalProps = {
  open: boolean
  onClose: () => void
}

const PROVIDERS: { value: LlmProvider; label: string }[] = [
  { value: 'openai', label: 'OpenAI' },
  { value: 'gemini', label: 'Gemini' },
]

const DEFAULT_MODELS: Record<LlmProvider, string> = {
  openai: 'gpt-5.1',
  gemini: 'gemini-2.0-flash',
}

export function LlmSettingsModal({ open, onClose }: LlmSettingsModalProps) {
  const [provider, setProvider] = useState<LlmProvider>('openai')
  const [model, setModel] = useState(DEFAULT_MODELS.openai)
  const [apiKey, setApiKey] = useState('')
  const [settings, setSettings] = useState<LlmSettings | null>(null)
  const [loading, setLoading] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedMessage, setSavedMessage] = useState<string | null>(null)

  useEffect(() => {
    if (!open) {
      return
    }

    let cancelled = false

    async function loadSettings() {
      setLoading(true)
      setError(null)
      setSavedMessage(null)
      setApiKey('')

      try {
        const data = await fetchLlmSettings()
        if (cancelled) {
          return
        }
        setSettings(data)
        setProvider(data.provider)
        setModel(data.model || DEFAULT_MODELS[data.provider])
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : 'Failed to load LLM settings',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    void loadSettings()

    return () => {
      cancelled = true
    }
  }, [open])

  if (!open) {
    return null
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    setSavedMessage(null)

    try {
      const updated = await updateLlmSettings({
        provider,
        model: model.trim() || DEFAULT_MODELS[provider],
        api_key: apiKey.trim() ? apiKey.trim() : undefined,
      })
      setSettings(updated)
      setProvider(updated.provider)
      setModel(updated.model)
      setApiKey('')
      setSavedMessage('Settings saved.')
    } catch (saveError) {
      setError(
        saveError instanceof Error ? saveError.message : 'Failed to save settings',
      )
    } finally {
      setSaving(false)
    }
  }

  function handleProviderChange(next: LlmProvider) {
    setProvider(next)
    setModel((current) => {
      const previousDefault = DEFAULT_MODELS[provider]
      if (!current.trim() || current === previousDefault) {
        return DEFAULT_MODELS[next]
      }
      return current
    })
  }

  const keyHint = settings?.api_key_set
    ? `Key on file${settings.api_key_last4 ? ` (…${settings.api_key_last4})` : ''}. Leave blank to keep.`
    : 'No API key stored yet.'

  return (
    <div className="modal-backdrop" role="presentation" onClick={onClose}>
      <div
        className="modal-panel"
        role="dialog"
        aria-modal="true"
        aria-labelledby="llm-settings-title"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="modal-header">
          <div>
            <h2 id="llm-settings-title">LLM Settings</h2>
            <p>Choose the model provider used for live call replies.</p>
          </div>
          <button type="button" className="ghost-button" onClick={onClose}>
            Close
          </button>
        </div>

        {loading ? (
          <p className="status-message">Loading settings…</p>
        ) : (
          <form className="settings-form" onSubmit={(event) => void handleSubmit(event)}>
            <label className="settings-field">
              <span>Provider</span>
              <select
                value={provider}
                onChange={(event) =>
                  handleProviderChange(event.target.value as LlmProvider)
                }
              >
                {PROVIDERS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="settings-field">
              <span>Model</span>
              <input
                type="text"
                value={model}
                onChange={(event) => setModel(event.target.value)}
                placeholder={DEFAULT_MODELS[provider]}
                autoComplete="off"
              />
            </label>

            <label className="settings-field">
              <span>API key</span>
              <input
                type="password"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="••••••••"
                autoComplete="off"
              />
              <span className="settings-hint">{keyHint}</span>
            </label>

            {error ? <p className="status-message error">{error}</p> : null}
            {savedMessage ? <p className="status-message success">{savedMessage}</p> : null}

            <div className="modal-actions">
              <button type="button" className="secondary-button" onClick={onClose}>
                Cancel
              </button>
              <button type="submit" className="primary-button" disabled={saving}>
                {saving ? 'Saving…' : 'Save settings'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
