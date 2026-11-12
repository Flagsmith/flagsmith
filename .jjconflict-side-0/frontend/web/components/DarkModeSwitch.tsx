import React, { FC } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Setting from './Setting'
import { setDarkMode, useTheme } from 'project/darkMode'

type DarkModeSwitchType = {}

// Shares theme state with the nav ThemeToggle via useTheme, so neither
// control goes stale when the other flips the theme. Toggling here sets an
// explicit light/dark preference (leaving 'system' mode).
const DarkModeSwitch: FC<DarkModeSwitchType> = ({}) => {
  const { isDark } = useTheme()

  return (
    <Setting
      title='Dark Mode'
      description='Adjust the theme you see when using Flagsmith.'
      checked={isDark}
      onChange={() => setDarkMode(!isDark)}
    />
  )
}

export default ConfigProvider(DarkModeSwitch)
