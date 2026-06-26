import { useLocation } from 'react-router-dom'

export type OnboardingConnectionStatus = 'listening' | 'connected'

// Connection status for the verify console. Reports the pre-connection state
// with a `?connected` query-param hatch to exercise the connected UI.
// TODO(#7767): replace with the real first-evaluation signal.
export const useOnboardingConnection = (): OnboardingConnectionStatus => {
  const { search } = useLocation()
  return new URLSearchParams(search).has('connected')
    ? 'connected'
    : 'listening'
}
