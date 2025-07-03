import { storageGet, storageSet } from 'common/safeLocalStorage'

export const getDarkMode = () => {
  return storageGet('dark_mode') === 'true'
}
export const setDarkMode = (enabled: boolean) => {
  if (enabled) {
    storageSet('dark_mode', 'true')
    document.body.classList.add('dark')
    document.documentElement.setAttribute('data-bs-theme', 'dark')
  } else {
    storageSet('dark_mode', 'false')
    document.body.classList.remove('dark')
    document.documentElement.removeAttribute('data-bs-theme')
  }
}
