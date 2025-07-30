import React, { FC } from 'react'
import ConfigProvider from 'common/providers/ConfigProvider'
import Utils from 'common/utils/utils'
import { IonIcon } from '@ionic/react'
import { rocket } from 'ionicons/icons'
type BetaFlagType = {
  children: React.ReactNode
  flagName: string
}

const BetaFlag: FC<BetaFlagType> = ({ children, flagName }) => {
  const remoteConfig = flagName ? Utils.getFlagsmithJSONValue(flagName) : {}
  const isBeta = remoteConfig?.beta
  return (
    <div className='d-flex justify-content-center align-items-center gap-2'>
      {children}
      {!!isBeta && (
        <div>
          <a className='chip cursor-pointer chip--xs d-flex align-items-center fw-semibold text-white bg-primary900'>
            {<IonIcon className='me-1' icon={rocket} />}
            beta
          </a>
        </div>
      )}
    </div>
  )
}

export default ConfigProvider(BetaFlag)
