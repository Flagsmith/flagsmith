import React, { FC, ReactNode } from 'react'
import Icon from './Icon'

type SettingsButtonType = {
  onClick: () => void
  children: ReactNode
}

const SettingsButton: FC<SettingsButtonType> = ({ children, onClick }) => {
  return (
    <Row>
      <Row className='cursor-pointer hover-color-primary' onClick={onClick}>
        <label className='cols-sm-2 control-label cursor-pointer'>
          {children} <Icon name='setting' width={20} fill={'#656D7B'} />
        </label>
      </Row>
    </Row>
  )
}

export default SettingsButton
