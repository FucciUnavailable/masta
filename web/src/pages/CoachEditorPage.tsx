import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router'
import { api } from '../api/client'
import type { CoachDetail, CoachUpdate } from '../api/types'
import { useAction } from '../hooks/useAction'
import { errorMessage, useApi } from '../hooks/useApi'

/** The form's view of a coach: lists are edited as text, one entry per line. */
interface Draft {
  name: string
  displayName: string
  description: string
  tags: string
  modelProfile: string
  persona: string
  bothSides: boolean
  socratic: boolean
  restReminders: boolean
  disclaimers: string
  refuseTopics: string
  escalate: string
  // Not editable here yet; carried through so saving doesn't drop them.
  tools: string[]
  safeRanges: Record<string, number[]>
}

const BLANK: Draft = {
  name: '',
  displayName: '',
  description: '',
  tags: '',
  modelProfile: '',
  persona: '',
  bothSides: true,
  socratic: false,
  restReminders: true,
  disclaimers: '',
  refuseTopics: '',
  escalate: '',
  tools: [],
  safeRanges: {},
}

function toDraft(coach: CoachDetail): Draft {
  return {
    name: coach.name,
    displayName: coach.display_name,
    description: coach.description,
    tags: coach.tags.join(', '),
    modelProfile: coach.model_profile ?? '',
    persona: coach.persona,
    bothSides: coach.style.both_sides,
    socratic: coach.style.socratic,
    restReminders: coach.style.rest_reminders,
    disclaimers: coach.guardrails.disclaimers.join('\n'),
    refuseTopics: coach.guardrails.refuse_topics.join('\n'),
    escalate: coach.guardrails.escalate_to_professional.join('\n'),
    tools: coach.tools,
    safeRanges: coach.guardrails.safe_ranges,
  }
}

function split(text: string, separator: string | RegExp): string[] {
  return text
    .split(separator)
    .map((part) => part.trim())
    .filter(Boolean)
}

function toUpdate(draft: Draft): CoachUpdate {
  return {
    display_name: draft.displayName.trim() || null,
    description: draft.description.trim(),
    tags: split(draft.tags, ','),
    model_profile: draft.modelProfile || null,
    tools: draft.tools,
    persona: draft.persona.trim(),
    style: {
      both_sides: draft.bothSides,
      socratic: draft.socratic,
      rest_reminders: draft.restReminders,
    },
    guardrails: {
      disclaimers: split(draft.disclaimers, '\n'),
      refuse_topics: split(draft.refuseTopics, '\n'),
      escalate_to_professional: split(draft.escalate, '\n'),
      safe_ranges: draft.safeRanges,
    },
  }
}

/** Create a coach (`/coaches/new`, optionally `?from=` a copy) or edit one (`/coaches/:name`). */
export function CoachEditorPage() {
  const { name } = useParams()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const profiles = useApi(api.profiles)
  const action = useAction()

  const source = name ?? params.get('from')
  const [draft, setDraft] = useState<Draft>(BLANK)
  const [loaded, setLoaded] = useState<CoachDetail | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const loading = Boolean(source) && !loaded && !loadError

  useEffect(() => {
    if (!source) return
    let live = true
    api.coach(source).then(
      (coach) => {
        if (!live) return
        setLoaded(coach)
        // A copy starts from the original but needs its own name.
        setDraft(name ? toDraft(coach) : { ...toDraft(coach), name: '' })
      },
      (err: unknown) => {
        if (live) setLoadError(errorMessage(err))
      },
    )
    return () => {
      live = false
    }
  }, [source, name])

  const creating = !name
  const readOnly = !creating && loaded !== null && !loaded.editable

  function set<K extends keyof Draft>(key: K, value: Draft[K]) {
    setDraft((d) => ({ ...d, [key]: value }))
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    const saved = await action.run(() =>
      creating
        ? api.createCoach({ ...toUpdate(draft), name: draft.name.trim() })
        : api.updateCoach(name, toUpdate(draft)),
    )
    if (saved) navigate('/coaches')
  }

  async function remove() {
    if (!name || !window.confirm(`Delete the coach “${name}” and its files?`)) {
      return
    }
    if (await action.run(() => api.deleteCoach(name))) navigate('/coaches')
  }

  if (loadError) {
    return (
      <>
        <header className="page-header">
          <h1>Coach</h1>
        </header>
        <p className="notice notice--error" role="alert">
          {loadError}
        </p>
        <Link to="/coaches">Back to coaches</Link>
      </>
    )
  }

  return (
    <>
      <header className="page-header">
        <h1>{creating ? 'New coach' : (loaded?.display_name ?? name)}</h1>
        <p>
          A coach is a persona plus guardrails. Saved to your masta config
          folder.
        </p>
      </header>

      {readOnly && (
        <p className="notice">
          This coach ships with masta and can’t be changed.{' '}
          <Link to={`/coaches/new?from=${encodeURIComponent(name ?? '')}`}>
            Duplicate it
          </Link>{' '}
          to make your own version.
        </p>
      )}

      {loading ? (
        <p className="muted">Loading…</p>
      ) : (
        <form className="form" onSubmit={save}>
          <fieldset disabled={readOnly || action.busy}>
            <div className="form-row">
              <label className="field field--grow">
                <span>Name</span>
                <input
                  value={draft.name}
                  onChange={(e) => set('name', e.target.value)}
                  disabled={!creating}
                  required
                  pattern="[a-z0-9]+(-[a-z0-9]+)*"
                  placeholder="sleep-coach"
                />
                <small>Lowercase letters, digits, and hyphens.</small>
              </label>
              <label className="field field--grow">
                <span>Display name</span>
                <input
                  value={draft.displayName}
                  onChange={(e) => set('displayName', e.target.value)}
                  placeholder="Sleep Coach"
                />
              </label>
            </div>

            <label className="field">
              <span>Description</span>
              <input
                value={draft.description}
                onChange={(e) => set('description', e.target.value)}
              />
            </label>

            <div className="form-row">
              <label className="field field--grow">
                <span>Tags</span>
                <input
                  value={draft.tags}
                  onChange={(e) => set('tags', e.target.value)}
                  placeholder="health, sleep"
                />
                <small>Comma-separated.</small>
              </label>
              <label className="field">
                <span>Model</span>
                <select
                  value={draft.modelProfile}
                  onChange={(e) => set('modelProfile', e.target.value)}
                >
                  <option value="">Default profile</option>
                  {profiles.status === 'ready' &&
                    profiles.data.map((p) => (
                      <option key={p.name} value={p.name}>
                        {p.name}
                      </option>
                    ))}
                </select>
              </label>
            </div>

            <label className="field">
              <span>Persona</span>
              <textarea
                rows={10}
                value={draft.persona}
                onChange={(e) => set('persona', e.target.value)}
                required
                placeholder="Who this coach is, how it teaches, and where it defers to a professional."
              />
              <small>
                Markdown. Becomes the system prompt; the settings below are
                added to it.
              </small>
            </label>

            <h2>How it coaches</h2>
            <label className="check">
              <input
                type="checkbox"
                checked={draft.bothSides}
                onChange={(e) => set('bothSides', e.target.checked)}
              />
              Argue both sides of every recommendation
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={draft.socratic}
                onChange={(e) => set('socratic', e.target.checked)}
              />
              Ask before prescribing (Socratic)
            </label>
            <label className="check">
              <input
                type="checkbox"
                checked={draft.restReminders}
                onChange={(e) => set('restReminders', e.target.checked)}
              />
              Encourage breaks and rest
            </label>

            <h2>Guardrails</h2>
            <p className="muted">
              One per line. Fill these in for anything touching health, money,
              or wellbeing.
            </p>
            <label className="field">
              <span>Disclaimers</span>
              <textarea
                rows={2}
                value={draft.disclaimers}
                onChange={(e) => set('disclaimers', e.target.value)}
                placeholder="I’m a coach, not a doctor."
              />
            </label>
            <label className="field">
              <span>Topics to refuse</span>
              <textarea
                rows={2}
                value={draft.refuseTopics}
                onChange={(e) => set('refuseTopics', e.target.value)}
              />
            </label>
            <label className="field">
              <span>Refer to a professional when the user raises</span>
              <textarea
                rows={2}
                value={draft.escalate}
                onChange={(e) => set('escalate', e.target.value)}
              />
            </label>
          </fieldset>

          {action.error && (
            <p className="notice notice--error" role="alert">
              {action.error}
            </p>
          )}

          <div className="form-actions">
            {!readOnly && (
              <button
                type="submit"
                className="button button--primary"
                disabled={action.busy}
              >
                {creating ? 'Create coach' : 'Save changes'}
              </button>
            )}
            <Link to="/coaches">{readOnly ? 'Back' : 'Cancel'}</Link>
            {!creating && !readOnly && (
              <button
                type="button"
                className="button button--danger"
                disabled={action.busy}
                onClick={remove}
              >
                Delete coach
              </button>
            )}
          </div>
        </form>
      )}
    </>
  )
}
