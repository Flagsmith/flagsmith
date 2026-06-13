import { storageGet, storageSet } from 'common/safeLocalStorage'

const DARK_MODE_KEY = 'dark_mode'
const THEME_PREFERENCE_KEY = 'theme_preference'
const THEME_PREFERENCE_EVENT = 'flagsmith-theme-preference-change'

export type ThemePreference = 'light' | 'dark' | 'system'

const themePreferences: ThemePreference[] = ['light', 'dark', 'system']

const isThemePreference = (value: string | null): value is ThemePreference =>
  !!value && themePreferences.includes(value as ThemePreference)

const getSystemDarkMode = () =>
  typeof window !== 'undefined' &&
  !!window.matchMedia?.('(prefers-color-scheme: dark)').matches

const canUseDOM = () =>
  typeof window !== 'undefined' && typeof document !== 'undefined'

const dispatchThemePreferenceChange = () => {
  if (!canUseDOM()) {
    return
  }

  if (typeof CustomEvent === 'function') {
    window.dispatchEvent(new CustomEvent(THEME_PREFERENCE_EVENT))
  } else {
    window.dispatchEvent(new Event(THEME_PREFERENCE_EVENT))
  }
}

export const getThemePreference = (): ThemePreference => {
  const storedPreference = storageGet(THEME_PREFERENCE_KEY)
  if (isThemePreference(storedPreference)) {
    return storedPreference
  }

  return storageGet(DARK_MODE_KEY) === 'true' ? 'dark' : 'light'
}

export const getResolvedDarkMode = (
  preference: ThemePreference = getThemePreference(),
) => {
  if (preference === 'system') {
    return getSystemDarkMode()
  }

  return preference === 'dark'
}

export const getDarkMode = () => {
  return getResolvedDarkMode()
}

const applyDarkMode = (enabled: boolean) => {
  if (!canUseDOM()) {
    return
  }

  if (enabled) {
    document.body.classList.add('dark')
    document.documentElement.setAttribute('data-bs-theme', 'dark')
  } else {
    document.body.classList.remove('dark')
    document.documentElement.removeAttribute('data-bs-theme')
  }
}

const applyThemePreference = (
  preference = getThemePreference(),
  { persistLegacy = false } = {},
) => {
  const enabled = getResolvedDarkMode(preference)
  if (persistLegacy) {
    storageSet(DARK_MODE_KEY, enabled ? 'true' : 'false')
  }
  applyDarkMode(enabled)
}

export const setThemePreference = (preference: ThemePreference) => {
  storageSet(THEME_PREFERENCE_KEY, preference)
  applyThemePreference(preference, { persistLegacy: true })
  dispatchThemePreferenceChange()
}

export const setDarkMode = (enabled: boolean) => {
  setThemePreference(enabled ? 'dark' : 'light')
}

export const listenToThemePreference = (callback: () => void) => {
  if (!canUseDOM()) {
    return () => {}
  }

  const handlePreferenceChange = () => {
    applyThemePreference()
    callback()
  }

  const handleStorage = (event: StorageEvent) => {
    if (
      event.key === THEME_PREFERENCE_KEY ||
      (event.key === DARK_MODE_KEY &&
        !isThemePreference(storageGet(THEME_PREFERENCE_KEY)))
    ) {
      handlePreferenceChange()
    }
  }

  window.addEventListener(THEME_PREFERENCE_EVENT, handlePreferenceChange)
  window.addEventListener('storage', handleStorage)

  return () => {
    window.removeEventListener(THEME_PREFERENCE_EVENT, handlePreferenceChange)
    window.removeEventListener('storage', handleStorage)
  }
}

const systemDarkMode = canUseDOM()
  ? window.matchMedia?.('(prefers-color-scheme: dark)')
  : undefined

const handleSystemDarkModeChange = () => {
  if (getThemePreference() === 'system') {
    applyThemePreference('system')
    dispatchThemePreferenceChange()
  }
}

if (systemDarkMode?.addEventListener) {
  systemDarkMode.addEventListener('change', handleSystemDarkModeChange)
} else {
  systemDarkMode?.addListener?.(handleSystemDarkModeChange)
}

if (storageGet(THEME_PREFERENCE_KEY) || storageGet(DARK_MODE_KEY)) {
  applyThemePreference()
}
