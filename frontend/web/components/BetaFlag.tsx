import React, { FC } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
import Icon from './icons/Icon'
type BetaFlagType = {
  children: React.ReactNode
  flagName?: string
  title?: string
}

const BetaFlag: FC<BetaFlagType> = ({ children, flagName, title = 'Beta' }) => {
  const remoteConfig = flagName ? Utils.getFlagsmithJSONValue(flagName) : {}
  const show = flagName ? !!remoteConfig?.beta : true
  return (
    <div className='d-flex justify-content-center align-items-center gap-2'>
      {children}
      {show && (
        <div>
          <span className='chip chip--xs d-flex align-items-center fw-semibold text-white bg-primary900'>
            <Icon name='rocket' width={12} className='me-1' />
            {title}
          </span>
        </div>
      )}
    </div>
  )
}

export default ConfigProvider(BetaFlag)
