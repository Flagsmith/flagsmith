import { FC } from 'react'
import classNames from 'classnames'
import BareButton from 'components/base/forms/BareButton'
import Popover from 'components/base/Popover'
import Icon from 'components/icons/Icon'
import { getScopeDisplayLabel } from 'components/audit-log/auditLogScopeFilter'
import ScopeCard, {
  ScopeCardProps,
} from 'components/audit-log/OrganisationAuditLogFilters/ScopeCard'
import './ScopeFilter.scss'

export type ScopeFilterProps = ScopeCardProps

const ScopeFilter: FC<ScopeFilterProps> = (props) => {
  const { onChange, projects, scope } = props
  const isFiltered = scope.type !== 'all'
  const projectName =
    scope.type === 'project'
      ? projects.items.find((p) => p.id === scope.projectId)?.name
      : undefined
  const label = getScopeDisplayLabel(scope, projectName)

  return (
    <Popover
      aria-label='Scope'
      renderTrigger={(triggerProps) => (
        <div
          className={classNames(
            'scope-filter__control d-inline-flex align-items-stretch flex-grow-1 flex-sm-grow-0 rounded',
            isFiltered
              ? 'scope-filter__control--active bg-surface-action-subtle text-action'
              : 'bg-surface-default text-default',
          )}
        >
          <BareButton
            {...triggerProps}
            title={label}
            className='scope-filter__trigger d-inline-flex flex-grow-1 align-items-center gap-1 px-3'
          >
            <span className='text-secondary flex-shrink-0'>Scope:</span>
            <span className='fw-semibold text-truncate'>{label}</span>
            <Icon
              name='chevron-down'
              width={16}
              className='flex-shrink-0 ms-auto'
            />
          </BareButton>
          {isFiltered && (
            <BareButton
              className='scope-filter__clear d-inline-flex flex-shrink-0 align-items-center px-2'
              aria-label='Show everything'
              onClick={() => onChange({ type: 'all' })}
            >
              <Icon name='close' width={14} />
            </BareButton>
          )}
        </div>
      )}
    >
      <ScopeCard {...props} />
    </Popover>
  )
}

export default ScopeFilter
