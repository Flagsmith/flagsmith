import { FC, ReactNode, useState } from 'react'
import { AuditLogItem } from 'common/types/responses'
import AuditLogRow from 'components/audit-log/AuditLogRow'
import { groupAuditLogsByDay } from 'components/audit-log/groupAuditLogsByDay'
import AuditLogDay from './AuditLogDay'
import AuditLogListEmpty from './AuditLogListEmpty'
import AuditLogListError from './AuditLogListError'
import LoadingRows from './LoadingRows'
import './AuditLogList.scss'

export type AuditLogListProps = {
  items: AuditLogItem[] | undefined
  isLoading: boolean
  error: unknown
  hasFilters: boolean
  onClearFilters: () => void
  onRetry: () => void
  // Fetched by the caller; the list never fetches.
  renderDetails: (item: AuditLogItem) => ReactNode
  projectColours?: Map<number, string>
}

const AuditLogList: FC<AuditLogListProps> = ({
  error,
  hasFilters,
  isLoading,
  items,
  onClearFilters,
  onRetry,
  projectColours,
  renderDetails,
}) => {
  const [expandedId, setExpandedId] = useState<number | null>(null)

  if (error) return <AuditLogListError error={error} onRetry={onRetry} />

  const isFirstLoad = isLoading && !items

  if (!isFirstLoad && !items?.length) {
    return (
      <AuditLogListEmpty
        hasFilters={hasFilters}
        onClearFilters={onClearFilters}
      />
    )
  }

  return (
    <div
      className='audit-log-list rounded-lg overflow-hidden'
      aria-busy={isLoading}
    >
      {!items && <LoadingRows />}
      {groupAuditLogsByDay(items ?? []).map((day) => (
        <AuditLogDay key={day.key} dayKey={day.key} label={day.label}>
          {day.items.map((item) => {
            const isExpanded = expandedId === item.id
            return (
              <AuditLogRow
                key={item.id}
                item={item}
                projectColour={
                  item.project
                    ? projectColours?.get(item.project.id)
                    : undefined
                }
                isExpanded={isExpanded}
                onToggle={() => setExpandedId(isExpanded ? null : item.id)}
              >
                {isExpanded && renderDetails(item)}
              </AuditLogRow>
            )
          })}
        </AuditLogDay>
      ))}
    </div>
  )
}

export default AuditLogList
