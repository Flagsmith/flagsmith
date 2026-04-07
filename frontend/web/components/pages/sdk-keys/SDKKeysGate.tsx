import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import SDKKeysPageLegacy from 'components/SDKKeysPage'
import SDKKeysPage from './SDKKeysPage'

const SDKKeysGate: FC = () => {
  if (Utils.getFlagsmithHasFeature('rtk_server_side_sdk_keys')) {
    return <SDKKeysPage />
  }
  return <SDKKeysPageLegacy />
}

export default SDKKeysGate
