import { api } from '../api/client'
import { DataView } from '../components/DataView'
import { useApi } from '../hooks/useApi'

export function ChatPage() {
  const coaches = useApi(api.coaches)

  return (
    <>
      <header className="page-header">
        <h1>Chat</h1>
        <p>Pick a coach to start a session.</p>
      </header>

      <p className="notice">
        The chat view isn’t built yet. For now, talk to a coach from the
        terminal: <code>masta chat --coach &lt;name&gt;</code>
      </p>

      <DataView state={coaches} empty="No coaches found.">
        {(rows) => (
          <ul className="cards">
            {rows.map((coach) => (
              <li key={coach.name} className="card">
                <h2>{coach.display_name}</h2>
                <p>{coach.description}</p>
                <p className="tags">
                  {coach.tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </p>
              </li>
            ))}
          </ul>
        )}
      </DataView>
    </>
  )
}
