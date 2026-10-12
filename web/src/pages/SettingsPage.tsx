import { useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api/client'
import type { Profile } from '../api/types'
import { DataView } from '../components/DataView'
import { useAction } from '../hooks/useAction'
import { useResource } from '../hooks/useApi'

interface Draft {
  name: string
  model: string
  temperature: string
  maxTokens: string
  apiBase: string
}

const BLANK: Draft = {
  name: '',
  model: '',
  temperature: '0.7',
  maxTokens: '',
  apiBase: '',
}

function toDraft(profile: Profile): Draft {
  return {
    name: profile.name,
    model: profile.model,
    temperature: String(profile.temperature),
    maxTokens: profile.max_tokens === null ? '' : String(profile.max_tokens),
    apiBase: profile.api_base ?? '',
  }
}

function ProfileState({ profile }: { profile: Profile }) {
  if (profile.configured)
    return <span className="badge badge--active">ready</span>
  if (profile.missing_env.length > 0) {
    return (
      <span className="badge badge--paused">
        needs {profile.missing_env.join(', ')}
      </span>
    )
  }
  return <span className="badge">unverified provider</span>
}

export function SettingsPage() {
  const { state: profiles, reload: reloadProfiles } = useResource(api.profiles)
  const { state: settings, reload: reloadSettings } = useResource(api.settings)
  const action = useAction()
  const [draft, setDraft] = useState<Draft>(BLANK)
  // The profile being edited, or null while adding a new one.
  const [editing, setEditing] = useState<string | null>(null)

  const envLocked =
    settings.status === 'ready' && settings.data.default_profile_from_env

  function reload() {
    reloadProfiles()
    reloadSettings()
  }

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((d) => ({ ...d, [key]: value }))
  }

  function edit(profile: Profile | null) {
    setEditing(profile?.name ?? null)
    setDraft(profile ? toDraft(profile) : BLANK)
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    const saved = await action.run(() =>
      api.saveProfile(draft.name.trim(), {
        model: draft.model.trim(),
        temperature: Number(draft.temperature),
        max_tokens: draft.maxTokens ? Number(draft.maxTokens) : null,
        api_base: draft.apiBase.trim() || null,
      }),
    )
    if (saved) edit(null)
    reload()
  }

  async function makeDefault(profile: Profile) {
    await action.run(() => api.setDefaultProfile(profile.name))
    reload()
  }

  async function remove(profile: Profile) {
    const question = profile.builtin
      ? `Reset “${profile.name}” to its built-in settings?`
      : `Remove the profile “${profile.name}”?`
    if (!window.confirm(question)) return
    await action.run(() => api.deleteProfile(profile.name))
    if (editing === profile.name) edit(null)
    reload()
  }

  return (
    <>
      <header className="page-header">
        <h1>Settings</h1>
        <p>Which models your coaches talk to.</p>
      </header>

      <p className="notice">
        API keys are never stored by masta. Set them in the environment where{' '}
        <code>masta serve</code> runs (for example{' '}
        <code>ANTHROPIC_API_KEY</code>
        ), then restart it.
      </p>

      {envLocked && (
        <p className="notice">
          The default profile is fixed by <code>MASTA_DEFAULT_PROFILE</code> in
          the environment.
        </p>
      )}

      {action.error && (
        <p className="notice notice--error" role="alert">
          {action.error}
        </p>
      )}

      <DataView state={profiles} empty="No model profiles.">
        {(rows) => (
          <ul className="rows">
            {rows.map((profile) => (
              <li key={profile.name} className="row">
                <span className="row-title">
                  <strong>{profile.name}</strong>{' '}
                  <span className="muted">{profile.model}</span>
                </span>
                {profile.is_default && <span className="badge">default</span>}
                <ProfileState profile={profile} />
                <span className="row-actions">
                  {!profile.is_default && (
                    <button
                      type="button"
                      className="link-button"
                      disabled={action.busy || envLocked}
                      onClick={() => makeDefault(profile)}
                    >
                      Make default
                    </button>
                  )}
                  <button
                    type="button"
                    className="link-button"
                    onClick={() => edit(profile)}
                  >
                    Edit
                  </button>
                  {profile.customized && (
                    <button
                      type="button"
                      className="link-button"
                      disabled={action.busy}
                      onClick={() => remove(profile)}
                    >
                      {profile.builtin ? 'Reset' : 'Remove'}
                    </button>
                  )}
                </span>
              </li>
            ))}
          </ul>
        )}
      </DataView>

      <form className="form" onSubmit={save}>
        <h2>{editing ? `Edit “${editing}”` : 'Add a model profile'}</h2>
        <div className="form-row">
          <label className="field">
            <span>Name</span>
            <input
              value={draft.name}
              onChange={(e) => set('name', e.target.value)}
              disabled={editing !== null}
              required
              pattern="[A-Za-z0-9_\-]+"
              placeholder="my-local"
            />
          </label>
          <label className="field field--grow">
            <span>Model</span>
            <input
              value={draft.model}
              onChange={(e) => set('model', e.target.value)}
              required
              placeholder="ollama/llama3.1"
            />
            <small>
              A LiteLLM model string: <code>provider/model</code>.
            </small>
          </label>
        </div>
        <div className="form-row">
          <label className="field">
            <span>Temperature</span>
            <input
              type="number"
              min="0"
              max="2"
              step="0.1"
              value={draft.temperature}
              onChange={(e) => set('temperature', e.target.value)}
              required
            />
          </label>
          <label className="field">
            <span>Max tokens</span>
            <input
              type="number"
              min="1"
              value={draft.maxTokens}
              onChange={(e) => set('maxTokens', e.target.value)}
              placeholder="provider default"
            />
          </label>
          <label className="field field--grow">
            <span>API base URL</span>
            <input
              value={draft.apiBase}
              onChange={(e) => set('apiBase', e.target.value)}
              placeholder="http://localhost:11434"
            />
            <small>Only for local or self-hosted models.</small>
          </label>
        </div>
        <div className="form-actions">
          <button
            type="submit"
            className="button button--primary"
            disabled={action.busy}
          >
            {editing ? 'Save profile' : 'Add profile'}
          </button>
          {editing && (
            <button
              type="button"
              className="link-button"
              onClick={() => edit(null)}
            >
              Cancel
            </button>
          )}
        </div>
      </form>

      {settings.status === 'ready' && (
        <dl className="paths">
          <dt>Config file</dt>
          <dd>
            <code>{settings.data.config_file}</code>
          </dd>
          <dt>Your coaches</dt>
          <dd>
            <code>{settings.data.coaches_dir}</code>
          </dd>
          <dt>Data</dt>
          <dd>
            <code>{settings.data.data_dir}</code>
          </dd>
        </dl>
      )}
    </>
  )
}
