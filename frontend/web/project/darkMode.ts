import API from './api'

export const getDarkMode = () => {
  return API.getCookie('dark_mode') === 'true'
}
export const setDarkMode = (enabled: boolean) => {
  if (enabled) {
    API.setCookie('dark_mode', true)
    document.body.classList.add('dark')
    document.documentElement.setAttribute('data-bs-theme', 'dark')
  } else {
    API.setCookie('dark_mode', null)
    document.body.classList.remove('dark')
    document.documentElement.removeAttribute('data-bs-theme')
  }
}

setDarkMode(getDarkMode())
