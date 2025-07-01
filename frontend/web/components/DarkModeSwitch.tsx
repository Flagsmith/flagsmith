import React, { FC, useState } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Setting from './Setting'
import { getDarkMode, setDarkMode } from 'project/darkMode'

type DarkModeSwitchType = {}

const DarkModeSwitch: FC<DarkModeSwitchType> = ({}) => {
  const [darkMode, _setDarkMode] = useState(getDarkMode())

  const toggleDarkMode = () => {
    _setDarkMode(!getDarkMode())
    setDarkMode(!getDarkMode())
  }
  return (
    <Setting
      title='Dark Mode'
      description='Adjust the theme you see when using Flagsmith.'
      checked={darkMode}
      onChange={toggleDarkMode}
    />
  )
}

export default ConfigProvider(DarkModeSwitch)
