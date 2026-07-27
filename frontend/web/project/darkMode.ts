import { useSyncExternalStore } from 'react'
import { storageGet, storageSet } from 'common/safeLocalStorage'

export type ThemeSetting = 'light' | 'dark' | 'system'

const THEME_KEY = 'theme'
// Pre-theme-setting storage: 'true' | 'false' under 'dark_mode'.
const LEGACY_KEY = 'dark_mode'

const media =
  typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-color-scheme: dark)')
    : null

export const getThemeSetting = (): ThemeSetting => {
  const stored = storageGet(THEME_KEY)
  if (stored === 'light' || stored === 'dark' || stored === 'system') {
    return stored
  }
  const legacy = storageGet(LEGACY_KEY)
  if (legacy === 'true') return 'dark'
  // No stored preference defaults to light, matching the previous behaviour;
  // 'system' is opt-in so existing users' themes do not flip on deploy.
  return 'light'
}

export const getDarkMode = (): boolean => {
  const setting = getThemeSetting()
  return setting === 'system' ? !!media?.matches : setting === 'dark'
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

export const setThemeSetting = (setting: ThemeSetting) => {
  storageSet(THEME_KEY, setting)
  apply()
}

// Back-compat boolean setter (account settings switch, legacy callers).
export const setDarkMode = (enabled: boolean) => {
  setThemeSetting(enabled ? 'dark' : 'light')
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
  const setting = useSyncExternalStore(subscribe, getThemeSetting)
  const isDark = useSyncExternalStore(subscribe, getDarkMode)
  return { isDark, setThemeSetting, setting }
}

// Follow OS appearance changes while in system mode.
media?.addEventListener?.('change', () => {
  if (getThemeSetting() === 'system') {
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
