import { api } from '../api/client'
import { DataView } from '../components/DataView'
import { useApi } from '../hooks/useApi'

export function GoalsPage() {
  const goals = useApi(api.goals)

  return (
    <>
      <header className="page-header">
        <h1>Goals</h1>
        <p>What you’re working toward.</p>
      </header>

      <DataView
        state={goals}
        empty={
          <>
            No goals yet. Add one with <code>masta goals --add "Learn X"</code>.
          </>
        }
      >
        {(rows) => (
          <ul className="rows">
            {rows.map((goal) => (
              <li key={goal.id} className="row">
                <span className="row-title">{goal.title}</span>
                {goal.coach && <span className="muted">{goal.coach}</span>}
                <span className={`badge badge--${goal.status}`}>
                  {goal.status}
                </span>
              </li>
            ))}
          </ul>
        )}
      </DataView>
    </>
  )
}
