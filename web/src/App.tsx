import { BrowserRouter, Link, Route, Routes } from 'react-router'
import { AppShell } from './components/AppShell'
import { ChatPage } from './pages/ChatPage'
import { CheckInsPage } from './pages/CheckInsPage'
import { GoalsPage } from './pages/GoalsPage'

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

/** The route table, separate from the router so tests can mount it in memory. */
export function AppRoutes() {
  return (
    <Routes>
      <Route element={<AppShell />}>
        <Route index element={<ChatPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="check-ins" element={<CheckInsPage />} />
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
