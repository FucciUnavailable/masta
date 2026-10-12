import { useState } from 'react'
import type { FormEvent } from 'react'
import { api } from '../api/client'
import type { GoalStatus } from '../api/types'
import { DataView } from '../components/DataView'
import { useAction } from '../hooks/useAction'
import { useApi, useResource } from '../hooks/useApi'

const STATUSES: GoalStatus[] = ['active', 'paused', 'achieved', 'abandoned']

export function GoalsPage() {
  const { state: goals, reload } = useResource(api.goals)
  const coaches = useApi(api.coaches)
  const action = useAction()
  const [title, setTitle] = useState('')
  const [coach, setCoach] = useState('')

  async function addGoal(event: FormEvent) {
    event.preventDefault()
    const added = await action.run(() =>
      api.createGoal({ title: title.trim(), coach: coach || null }),
    )
    if (added) setTitle('')
    reload()
  }

  async function setStatus(id: number, status: GoalStatus) {
    await action.run(() => api.setGoalStatus(id, status))
    reload()
  }

  return (
    <>
      <header className="page-header">
        <h1>Goals</h1>
        <p>What you’re working toward. Coaches see your active goals.</p>
      </header>

      <form className="form-row" onSubmit={addGoal}>
        <label className="field field--grow">
          <span>New goal</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Learn Postgres internals"
          />
        </label>
        <label className="field">
          <span>Coach</span>
          <select value={coach} onChange={(e) => setCoach(e.target.value)}>
            <option value="">None</option>
            {coaches.status === 'ready' &&
              coaches.data.map((c) => (
                <option key={c.name} value={c.name}>
                  {c.display_name}
                </option>
              ))}
          </select>
        </label>
        <button
          type="submit"
          className="button button--primary"
          disabled={action.busy || title.trim() === ''}
        >
          Add goal
        </button>
      </form>

      {action.error && (
        <p className="notice notice--error" role="alert">
          {action.error}
        </p>
      )}

      <DataView state={goals} empty="No goals yet. Add your first one above.">
        {(rows) => (
          <ul className="rows">
            {rows.map((goal) => (
              <li key={goal.id} className="row">
                <span className="row-title">{goal.title}</span>
                {goal.coach && <span className="muted">{goal.coach}</span>}
                <select
                  className={`badge badge--${goal.status}`}
                  aria-label={`Status of ${goal.title}`}
                  value={goal.status}
                  onChange={(e) =>
                    setStatus(goal.id, e.target.value as GoalStatus)
                  }
                >
                  {STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {status}
                    </option>
                  ))}
                </select>
              </li>
            ))}
          </ul>
        )}
      </DataView>
    </>
  )
}
