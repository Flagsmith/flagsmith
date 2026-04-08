import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import SDKKeysPageLegacy from 'components/SDKKeysPage'
import SDKEnvironmentKeysSettings from './SDKEnvironmentKeysSettings'

const SDKKeysPage: FC = () => {
  if (Utils.getFlagsmithHasFeature('rtk_server_side_sdk_keys')) {
    return <SDKEnvironmentKeysSettings />
  }
  return <SDKKeysPageLegacy />
}

export default SDKKeysPage
