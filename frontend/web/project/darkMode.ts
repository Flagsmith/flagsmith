import { useSyncExternalStore } from 'react'
import { storageGet, storageSet } from 'common/safeLocalStorage'

// 'light' | 'dark' once the user has explicitly chosen.
const THEME_KEY = 'theme'
// Pre-theme storage: 'true' | 'false' under 'dark_mode'.
const LEGACY_KEY = 'dark_mode'

const media =
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null

const getStoredChoice = (): 'light' | 'dark' | null => {
  const stored = storageGet(THEME_KEY)
  if (stored === 'light' || stored === 'dark') return stored
  const legacy = storageGet(LEGACY_KEY)
  if (legacy === 'true') return 'dark'
  if (legacy === 'false') return 'light'
  return null
}

// An explicit choice wins; without one the OS preference decides.
export const getDarkMode = (): boolean => {
  const choice = getStoredChoice()
  return choice ? choice === 'dark' : !!media?.matches
}

const listeners = new Set<() => void>()

const apply = () => {
  const dark = getDarkMode()
  document.body.classList.toggle('dark', dark)
  if (dark) {
    document.documentElement.setAttribute('data-bs-theme', 'dark')
  } else {
    document.documentElement.removeAttribute('data-bs-theme')
  }
  listeners.forEach((listener) => listener())
}

export const setDarkMode = (enabled: boolean) => {
  storageSet(THEME_KEY, enabled ? 'dark' : 'light')
  apply()
}

const subscribe = (listener: () => void) => {
  listeners.add(listener)
  return () => {
    listeners.delete(listener)
  }
}

// Reactive theme state; all theme UI (nav toggle, settings switch) shares it
// so no control goes stale when another one changes the theme.
export const useTheme = () => {
  const isDark = useSyncExternalStore(subscribe, getDarkMode)
  return { isDark, setDarkMode }
}

// Follow OS appearance changes until the user makes an explicit choice.
media?.addEventListener?.('change', () => {
  if (!getStoredChoice()) {
    apply()
  }
})

// Reflect theme changes made in other browser tabs immediately.
if (typeof window !== 'undefined') {
  window.addEventListener('storage', (e) => {
    if (e.key === THEME_KEY || e.key === LEGACY_KEY) {
      apply()
    }
  })
}

apply()
