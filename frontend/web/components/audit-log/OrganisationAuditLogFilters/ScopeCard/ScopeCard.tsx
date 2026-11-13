import { FC, useState } from 'react'
import SegmentedControl from 'components/base/SegmentedControl'
import { AuditLogScopeFilter } from 'components/audit-log/auditLogScopeFilter'
import { ScopeList } from './ListMessage'
import ScopeEnvironmentChips, {
  ScopeCardEnvironment,
} from './ScopeEnvironmentChips'
import ScopeProjectList, { ScopeCardProject } from './ScopeProjectList'
import ScopeSection from './ScopeSection'
import './ScopeCard.scss'

type ScopeMode = AuditLogScopeFilter['type']

export type ScopeCardProps = {
  scope: AuditLogScopeFilter
  projects: ScopeList<ScopeCardProject>
  environments: ScopeList<ScopeCardEnvironment>
  onChange: (scope: AuditLogScopeFilter) => void
}

const MODES: { label: string; value: ScopeMode }[] = [
  { label: 'Everything', value: 'all' },
  { label: 'Organisation', value: 'organisation' },
  { label: 'Project', value: 'project' },
]

const ScopeCard: FC<ScopeCardProps> = ({
  environments,
  onChange,
  projects,
  scope,
}) => {
  // "Project" can be picked before a project is, so the mode lives here.
  const [mode, setMode] = useState<ScopeMode>(scope.type)
  const projectId = scope.type === 'project' ? scope.projectId : undefined

  const changeMode = (next: ScopeMode) => {
    setMode(next)
    if (next !== 'project') onChange({ type: next })
  }
  const toggleEnvironment = (id: number, checked: boolean) => {
    if (scope.type !== 'project') return
    onChange({
      ...scope,
      environmentIds: checked
        ? [...scope.environmentIds, id]
        : scope.environmentIds.filter((e) => e !== id),
    })
  }

  return (
    <div className='scope-card d-flex flex-column p-2'>
      <SegmentedControl
        aria-label='Scope'
        options={MODES}
        value={mode}
        onChange={changeMode}
      />
      <ScopeSection open={mode === 'project'}>
        <ScopeProjectList
          projects={projects}
          selectedId={projectId}
          onSelect={(id) =>
            onChange({ environmentIds: [], projectId: id, type: 'project' })
          }
        />
      </ScopeSection>
      <ScopeSection open={mode === 'project' && !!projectId}>
        <ScopeEnvironmentChips
          environments={environments}
          selectedIds={scope.type === 'project' ? scope.environmentIds : []}
          onToggle={toggleEnvironment}
        />
      </ScopeSection>
      <ScopeSection open={mode === 'organisation'}>
        <p className='mb-0 p-2 rounded-lg bg-surface-subtle fs-caption text-secondary'>
          Members, roles and groups. Organisation events can't be filtered by
          project or environment.
        </p>
      </ScopeSection>
    </div>
  )
}

export default ScopeCard
