import React from 'react'
import IconButton from 'components/base/IconButton'
import Icon from 'components/icons/Icon'
import { useTheme } from 'project/darkMode'

// One-click light/dark flip (the icon shows what you switch to). With no
// stored choice the theme follows the OS; the first click pins an explicit
// preference. State is shared via useTheme, so the account-settings switch
// and other tabs stay in sync.
const ThemeToggle = () => {
  const { isDark, setDarkMode } = useTheme()

  return (
    <IconButton
      variant='ghost'
      size='small'
      onClick={() => setDarkMode(!isDark)}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <Icon width={16} name={isDark ? 'sun' : 'moon'} />
    </IconButton>
  )
}

export default ThemeToggle
