import { Link } from 'react-router'
import { api } from '../api/client'
import { DataView } from '../components/DataView'
import { useApi } from '../hooks/useApi'

export function CoachesPage() {
  const coaches = useApi(api.coaches)

  return (
    <>
      <header className="page-header page-header--split">
        <div>
          <h1>Coaches</h1>
          <p>Your senseis. Each has its own voice, focus, and guardrails.</p>
        </div>
        <Link to="/coaches/new" className="button button--primary">
          New coach
        </Link>
      </header>

      <DataView state={coaches} empty="No coaches found.">
        {(rows) => (
          <ul className="cards">
            {rows.map((coach) => (
              <li key={coach.name} className="card">
                <h2>{coach.display_name}</h2>
                <p>{coach.description}</p>
                <p className="tags">
                  {!coach.editable && <span className="badge">built-in</span>}
                  {coach.tags.map((tag) => (
                    <span key={tag} className="tag">
                      {tag}
                    </span>
                  ))}
                </p>
                <p className="card-actions">
                  <Link to={`/?coach=${encodeURIComponent(coach.name)}`}>
                    Chat
                  </Link>
                  <Link to={`/coaches/${encodeURIComponent(coach.name)}`}>
                    {coach.editable ? 'Edit' : 'View'}
                  </Link>
                  <Link
                    to={`/coaches/new?from=${encodeURIComponent(coach.name)}`}
                  >
                    Duplicate
                  </Link>
                </p>
              </li>
            ))}
          </ul>
        )}
      </DataView>
    </>
  )
}
