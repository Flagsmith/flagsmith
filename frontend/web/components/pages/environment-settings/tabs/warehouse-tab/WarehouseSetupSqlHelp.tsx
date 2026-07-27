import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import CalloutBar from 'components/CalloutBar'
import Highlight from 'components/Highlight'
import Icon from 'components/icons/Icon'
import Utils from 'common/utils/utils'
import { CLICKHOUSE_SETUP_SQL } from './clickhouseSetupSql'

type WarehouseSetupSqlHelpProps = {
  showInitially?: boolean
}

const WarehouseSetupSqlHelp: FC<WarehouseSetupSqlHelpProps> = ({
  showInitially,
}) => {
  const [visible, setVisible] = useState(!!showInitially)

  return (
    <div>
      <CalloutBar
        icon={<>{'<>'}</>}
        prefix='Database setup:'
        label='Run once against your ClickHouse instance to create the events table'
        expanded={visible}
        onClick={() => setVisible(!visible)}
      />
      {visible && (
        <div className='hljs-container mt-2 mb-2'>
          <Highlight forceExpanded preventEscape className='sql'>
            {CLICKHOUSE_SETUP_SQL}
          </Highlight>
          <div className='flex-column hljs-docs'>
            <Button
              onClick={() => Utils.copyToClipboard(CLICKHOUSE_SETUP_SQL)}
              theme='primary'
              size='xSmall'
            >
              <Icon name='copy' width={16} fill='white' />
              Copy Code
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

WarehouseSetupSqlHelp.displayName = 'WarehouseSetupSqlHelp'
export default WarehouseSetupSqlHelp
