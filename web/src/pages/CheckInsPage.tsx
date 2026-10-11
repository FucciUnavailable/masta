import { api } from '../api/client'
import { DataView } from '../components/DataView'
import { useApi } from '../hooks/useApi'

export function CheckInsPage() {
  const checkins = useApi(api.checkins)

  return (
    <>
      <header className="page-header">
        <h1>Check-ins</h1>
        <p>How it’s been going lately.</p>
      </header>

      <DataView
        state={checkins}
        empty={
          <>
            No check-ins yet. Log one with <code>masta checkin --note "…"</code>
            .
          </>
        }
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
