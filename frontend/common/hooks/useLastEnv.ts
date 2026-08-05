import { useEffect, useState } from 'react'

// `lastEnv` is written by usePageTracking as you browse, and read by App and Nav
// to restore where you were. environmentId is the api_key, since routes use it.
export type LastEnv = {
  orgId?: number | string
  projectId?: number | string
  environmentId?: string
}

export const parseLastEnv = (raw: string | null): LastEnv | null => {
  if (!raw) return null
  try {
    return JSON.parse(raw)
  } catch {
    return null
  }
}

export const useLastEnv = (): LastEnv | null => {
  const [lastEnv, setLastEnv] = useState<LastEnv | null>(null)

  useEffect(() => {
    if (typeof AsyncStorage === 'undefined') return
    Promise.resolve(AsyncStorage.getItem('lastEnv')).then((raw) =>
      setLastEnv(parseLastEnv(raw)),
    )
  }, [])

  return lastEnv
}
