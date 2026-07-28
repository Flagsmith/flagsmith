import React, { FC, useState } from 'react'
import CalloutBar from 'components/CalloutBar'
import WarehouseSqlSnippet from './WarehouseSqlSnippet'
import { getClickHouseSetupSql } from './clickhouseSetupSql'

type WarehouseSetupSqlHelpProps = {
  database: string
  showInitially?: boolean
}

const WarehouseSetupSqlHelp: FC<WarehouseSetupSqlHelpProps> = ({
  database,
  showInitially,
}) => {
  // Visibility follows showInitially until the user toggles; their choice
  // then stays authoritative across re-renders.
  const [override, setOverride] = useState<boolean | null>(null)
  const visible = override ?? !!showInitially

  return (
    <div>
      <CalloutBar
        icon={<>{'<>'}</>}
        prefix='Database setup:'
        label='Run once against your ClickHouse instance to create the events table'
        expanded={visible}
        onClick={() => setOverride(!visible)}
      />
      {visible && <WarehouseSqlSnippet sql={getClickHouseSetupSql(database)} />}
    </div>
  )
}

WarehouseSetupSqlHelp.displayName = 'WarehouseSetupSqlHelp'
export default WarehouseSetupSqlHelp
