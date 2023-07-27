export const setDarkMode = (enabled: boolean) => {
  if (enabled) {
    document.body.classList.add('dark')
    document.documentElement.setAttribute('data-bs-theme', 'dark')
  } else {
    document.body.classList.remove('dark')
    document.documentElement.removeAttribute('data-bs-theme')
  }
}
