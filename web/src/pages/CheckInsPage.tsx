import { useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api/client'
import { DataView } from '../components/DataView'
import { useAction } from '../hooks/useAction'
import { useApi, useResource } from '../hooks/useApi'

const SCALE = [1, 2, 3, 4, 5]

function ScaleSelect({
  label,
  value,
  onChange,
}: {
  label: string
  value: string
  onChange: (value: string) => void
}) {
  return (
    <label className="field">
      <span>{label}</span>
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        <option value="">–</option>
        {SCALE.map((n) => (
          <option key={n} value={n}>
            {n}
          </option>
        ))}
      </select>
    </label>
  )
}

export function CheckInsPage() {
  const { state: checkins, reload } = useResource(api.checkins)
  const goals = useApi(api.goals)
  const action = useAction()
  const [note, setNote] = useState('')
  const [mood, setMood] = useState('')
  const [energy, setEnergy] = useState('')
  const [goalId, setGoalId] = useState('')

  const goalRows = goals.status === 'ready' ? goals.data : []
  const empty = note.trim() === '' && mood === '' && energy === ''

  async function addCheckin(event: FormEvent) {
    event.preventDefault()
    const added = await action.run(() =>
      api.createCheckin({
        note: note.trim(),
        mood: mood ? Number(mood) : null,
        energy: energy ? Number(energy) : null,
        goal_id: goalId ? Number(goalId) : null,
      }),
    )
    if (added) {
      setNote('')
      setMood('')
      setEnergy('')
    }
    reload()
  }

  return (
    <>
      <header className="page-header">
        <h1>Check-ins</h1>
        <p>How it’s been going lately. Coaches see your latest one.</p>
      </header>

      <form className="form-row" onSubmit={addCheckin}>
        <label className="field field--grow">
          <span>How’s it going?</span>
          <input
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Tired, but I shipped the migration"
          />
        </label>
        <ScaleSelect label="Mood" value={mood} onChange={setMood} />
        <ScaleSelect label="Energy" value={energy} onChange={setEnergy} />
        <label className="field">
          <span>Goal</span>
          <select value={goalId} onChange={(e) => setGoalId(e.target.value)}>
            <option value="">None</option>
            {goalRows.map((goal) => (
              <option key={goal.id} value={goal.id}>
                {goal.title}
              </option>
            ))}
          </select>
        </label>
        <button
          type="submit"
          className="button button--primary"
          disabled={action.busy || empty}
        >
          Log check-in
        </button>
      </form>

      {action.error && (
        <p className="notice notice--error" role="alert">
          {action.error}
        </p>
      )}

      <DataView
        state={checkins}
        empty="No check-ins yet. Log how today went above."
      >
        {(rows) => (
          <ul className="rows">
            {rows.map((checkin) => (
              <li key={checkin.id} className="row">
                <time className="muted" dateTime={checkin.created_at}>
                  {new Date(checkin.created_at).toLocaleDateString()}
                </time>
                <span className="row-title">{checkin.note || '(no note)'}</span>
                {checkin.mood !== null && (
                  <span className="muted">mood {checkin.mood}/5</span>
                )}
                {checkin.energy !== null && (
                  <span className="muted">energy {checkin.energy}/5</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </DataView>
    </>
  )
}
