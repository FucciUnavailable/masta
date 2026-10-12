import { useCallback, useState } from 'react'
import { errorMessage } from './useApi'

/**
 * Run a change against the API, tracking whether it is in flight and how it failed.
 * `run` resolves to whether the change succeeded.
 */
export function useAction() {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const run = useCallback(async (change: () => Promise<unknown>) => {
    setBusy(true)
    setError(null)
    try {
      await change()
      return true
    } catch (err) {
      setError(errorMessage(err))
      return false
    } finally {
      setBusy(false)
    }
  }, [])

  return { busy, error, run }
}
