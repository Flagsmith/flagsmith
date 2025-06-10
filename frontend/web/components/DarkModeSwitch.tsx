import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import ConfigProvider from 'common/providers/ConfigProvider'
import flagsmith from 'flagsmith'
import Tooltip from './Tooltip'
import Setting from './Setting'

type DarkModeSwitchType = {}

const DarkModeSwitch: FC<DarkModeSwitchType> = ({}) => {
  const toggleDarkMode = () => {
    const newValue = !Utils.getFlagsmithHasFeature('dark_mode')
    flagsmith.setTrait('dark_mode', newValue)
    if (newValue) {
      document.body.classList.add('dark')
    } else {
      document.body.classList.remove('dark')
    }
  }
  return (
    <Setting
      title='Dark Mode'
      description='Adjust the theme you see when using Flagsmith.'
      checked={Utils.getFlagsmithHasFeature('dark_mode')}
      onChange={toggleDarkMode}
    />
  )
}

export default ConfigProvider(DarkModeSwitch)
