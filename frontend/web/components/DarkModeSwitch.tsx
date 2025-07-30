import React, { FC, useState } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Setting from './Setting'
import { getDarkMode, setDarkMode as persistDarkMode } from 'project/darkMode'

type DarkModeSwitchType = {}

const DarkModeSwitch: FC<DarkModeSwitchType> = ({}) => {
  const [darkModeLocal, setDarkModeLocal] = useState(getDarkMode())

  const toggleDarkMode = () => {
    const newDarkMode = !getDarkMode()
    setDarkModeLocal(newDarkMode)
    persistDarkMode(newDarkMode)
  }
  return (
    <Setting
      title='Dark Mode'
      description='Adjust the theme you see when using Flagsmith.'
      checked={darkModeLocal}
      onChange={toggleDarkMode}
    />
  )
}

export default ConfigProvider(DarkModeSwitch)
