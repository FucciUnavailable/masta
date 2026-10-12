import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router'
import { AppShell } from './components/AppShell'
import { ChatPage } from './pages/ChatPage'
import { CheckInsPage } from './pages/CheckInsPage'
import { CoachEditorPage } from './pages/CoachEditorPage'
import { CoachesPage } from './pages/CoachesPage'
import { GoalsPage } from './pages/GoalsPage'
import { SettingsPage } from './pages/SettingsPage'

function NotFound() {
  return (
    <header className="page-header">
      <h1>Not found</h1>
      <p>
        Nothing lives here. <Link to="/">Back to chat</Link>
      </p>
    </header>
  )
}

/** Remounts the editor per coach, so one coach's draft never shows under another. */
function CoachEditorRoute() {
  const { pathname, search } = useLocation()
  return <CoachEditorPage key={pathname + search} />
}

/** The route table, separate from the router so tests can mount it in memory. */
export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<ChatPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="check-ins" element={<CheckInsPage />} />
        <Route path="coaches" element={<CoachesPage />} />
        <Route path="coaches/new" element={<CoachEditorRoute />} />
        <Route path="coaches/:name" element={<CoachEditorRoute />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppRoutes />
    </BrowserRouter>
  )
}
