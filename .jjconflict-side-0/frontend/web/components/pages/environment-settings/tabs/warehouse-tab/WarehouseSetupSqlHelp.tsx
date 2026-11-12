import React, { FC, useState } from 'react'
import CalloutBar from 'components/CalloutBar'
import WarehouseSqlSnippet from './WarehouseSqlSnippet'

type WarehouseSetupSqlHelpProps = {
  sql: string
  label: string
  showInitially?: boolean
}

const WarehouseSetupSqlHelp: FC<WarehouseSetupSqlHelpProps> = ({
  label,
  showInitially,
  sql,
}) => {
  // Visibility follows showInitially until the user toggles; their choice
  // then stays authoritative across re-renders.
  const [override, setOverride] = useState<boolean | null>(null)
  const visible = override ?? !!showInitially

  return (
    <div>
      <CalloutBar
        prefix='Database setup:'
        label={label}
        expanded={visible}
        onClick={() => setOverride(!visible)}
      />
      {visible && <WarehouseSqlSnippet sql={sql} />}
    </div>
  )
}

WarehouseSetupSqlHelp.displayName = 'WarehouseSetupSqlHelp'
export default WarehouseSetupSqlHelp
