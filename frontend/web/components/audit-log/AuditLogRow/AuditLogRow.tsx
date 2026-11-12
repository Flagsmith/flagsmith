import { FC, ReactNode } from 'react'
import { AuditLogItem } from 'common/types/responses'
import Accordion from 'components/base/Accordion'
import AuditLogMessage from './AuditLogMessage'
import AuditLogScopeChip from './AuditLogScopeChip'
import AuditLogTypeIcon from './AuditLogTypeIcon'
import './AuditLogRow.scss'

export type AuditLogRowProps = {
  item: AuditLogItem
  isExpanded: boolean
  onToggle: () => void
  // Passed to the scope chip.
  projectColour?: string
  // The expanded content, e.g. AuditLogChanges. The row never fetches.
  children?: ReactNode
}

const AuditLogRow: FC<AuditLogRowProps> = ({
  children,
  isExpanded,
  item,
  onToggle,
  projectColour,
}) => (
  <Accordion
    variant='row'
    flush
    className='audit-log-row'
    open={isExpanded}
    onOpenChange={onToggle}
    title={
      <>
        <AuditLogTypeIcon item={item} />
        <span className='audit-log-row__summary d-flex align-items-center flex-fill overflow-hidden'>
          <AuditLogMessage item={item} />
          <AuditLogScopeChip item={item} projectColour={projectColour} />
        </span>
      </>
    }
  >
    {!!children && (
      <div className='audit-log-row__details pt-1 pb-3 pe-3'>{children}</div>
    )}
  </Accordion>
)

export default AuditLogRow
