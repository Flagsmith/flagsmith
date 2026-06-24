import React, { useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/icons/Icon'
import { getDarkMode, setDarkMode } from 'project/darkMode'

// Compact light/dark toggle for the chromeless onboarding flow (which has no
// app nav to reach the theme setting). setDarkMode flips the theme live - it
// toggles the body class + data-bs-theme and persists to storage - so the
// local state only exists to re-render this button's own icon. Uses the
// existing icon-button (Button theme='icon'); migrate to the dedicated
// icon-button primitive once that lands.
const ThemeToggle = () => {
  const [dark, setDark] = useState(getDarkMode())

  const toggle = () => {
    const next = !dark
    setDark(next)
    setDarkMode(next)
  }

  return (
    <Button
      theme='icon'
      onClick={toggle}
      aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <Icon name={dark ? 'sun' : 'moon'} width={18} />
    </Button>
  )
}

export default ThemeToggle
