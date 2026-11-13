import { FC } from 'react'
import { AuditLogItem } from 'common/types/responses'
import Chip from 'components/base/Chip'
import {
  getAuditLogScopeLabel,
  isOrganisationEvent,
} from 'components/audit-log/auditLogScope'
import ProjectInitial from 'components/audit-log/ProjectInitial'

type AuditLogScopeChipProps = {
  item: AuditLogItem
  // The project's Projects page colour; shows its initial in the chip.
  projectColour?: string
}

const AuditLogScopeChip: FC<AuditLogScopeChipProps> = ({
  item,
  projectColour,
}) => {
  const scope = getAuditLogScopeLabel(item)
  if (!scope) return null
  return (
    <Chip
      size='sm'
      className='mw-100'
      variant={isOrganisationEvent(item) ? 'accent' : 'neutral'}
    >
      {item.project && projectColour && (
        <ProjectInitial name={item.project.name} colour={projectColour} />
      )}
      <span className='text-truncate'>{scope}</span>
    </Chip>
  )
}

export default AuditLogScopeChip
