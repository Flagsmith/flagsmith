import React from 'react'
import IconButton from 'components/base/IconButton'
import { useTheme } from 'project/darkMode'
import { MoonIcon, SunIcon } from 'components/icons'

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
      {isDark ? <SunIcon width={16} /> : <MoonIcon width={16} />}
    </IconButton>
  )
}

export default ThemeToggle
