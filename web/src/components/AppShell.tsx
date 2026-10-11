import { NavLink, Outlet } from 'react-router'
import { api } from '../api/client'
import { useApi } from '../hooks/useApi'

const NAV = [
  { to: '/', label: 'Chat' },
  { to: '/goals', label: 'Goals' },
  { to: '/check-ins', label: 'Check-ins' },
]

function ApiStatus() {
  const health = useApi(api.health)
  if (health.status === 'loading') {
    return <p className="api-status">Connecting…</p>
  }
  if (health.status === 'error') {
    return (
      <p className="api-status api-status--down">
        API unreachable — run <code>masta serve</code>
      </p>
    )
  }
  return <p className="api-status api-status--up">API v{health.data.version}</p>
}

export function AppShell() {
  return (
    <div className="shell">
      <aside className="sidebar">
        <p className="brand">
          <span aria-hidden="true">🥋</span> masta
        </p>
        <nav aria-label="Main">
          {NAV.map(({ to, label }) => (
            <NavLink key={to} to={to} end={to === '/'} className="nav-link">
              {label}
            </NavLink>
          ))}
        </nav>
        <ApiStatus />
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
