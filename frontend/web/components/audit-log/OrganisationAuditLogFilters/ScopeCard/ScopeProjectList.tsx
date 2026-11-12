import { FC, useId, useRef } from 'react'
import classNames from 'classnames'
import Radio from 'components/base/forms/Radio'
import ProjectInitial from 'components/audit-log/ProjectInitial'
import ListMessage, { ScopeList } from './ListMessage'
import useScrollSelectedIntoView from './useScrollSelectedIntoView'
import './ScopeCard.scss'

export type ScopeCardProject = { id: number; name: string; colour?: string }

type ScopeProjectListProps = {
  projects: ScopeList<ScopeCardProject>
  selectedId: number | undefined
  onSelect: (projectId: number) => void
}

const ScopeProjectList: FC<ScopeProjectListProps> = ({
  onSelect,
  projects,
  selectedId,
}) => {
  const name = useId()
  const listRef = useRef<HTMLDivElement>(null)
  useScrollSelectedIntoView(listRef)

  return (
    <div
      ref={listRef}
      role='radiogroup'
      aria-label='Project'
      className='scope-card__projects position-relative d-flex flex-column gap-1 p-1 rounded-lg bg-surface-subtle'
    >
      <ListMessage
        list={projects}
        noun='projects'
        emptyText='No projects yet'
      />
      {projects.items.map((project) => {
        const isSelected = project.id === selectedId
        return (
          <Radio
            key={project.id}
            name={name}
            value={`${project.id}`}
            checked={isSelected}
            indicatorPosition='end'
            onChange={() => onSelect(project.id)}
            className={classNames(
              'scope-card__project px-2 py-2 rounded-md text-default',
              { 'bg-surface-action-subtle': isSelected },
            )}
          >
            {project.colour && (
              <ProjectInitial
                name={project.name}
                colour={project.colour}
                size='md'
              />
            )}
            <span className='flex-fill fw-semibold text-truncate'>
              {project.name}
            </span>
          </Radio>
        )
      })}
    </div>
  )
}

export default ScopeProjectList
