import React from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import { useTheme } from 'project/darkMode'

// One-click light/dark flip (the icon shows what you switch to). With no
// stored choice the theme follows the OS; the first click pins an explicit
// preference. State is shared via useTheme, so the account-settings switch
// and other tabs stay in sync.
const ThemeToggle = () => {
  const { isDark, setDarkMode } = useTheme()

  return (
    <Button
      theme='icon'
      onClick={() => setDarkMode(!isDark)}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <Icon name={isDark ? 'sun' : 'moon'} width={18} />
    </Button>
  )
}

export default ThemeToggle
