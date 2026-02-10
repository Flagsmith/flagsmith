import React, { FC } from 'react'
import classNames from 'classnames'
import { ProjectFlag } from 'common/types/responses'
import FeatureName from './FeatureName'
import FeatureDescription from './FeatureDescription'
import TagValues from 'components/tags/TagValues'

export interface ProjectFeatureRowProps {
  projectFlag: ProjectFlag
  index: number
  isSelected?: boolean
  onSelect?: (projectFlag: ProjectFlag) => void
  className?: string
}

const ProjectFeatureRow: FC<ProjectFeatureRowProps> = ({
  className,
  index,
  isSelected,
  onSelect,
  projectFlag,
}) => {
  const { description } = projectFlag

  return (
    <>
      {/* Desktop */}
      <div
        className={classNames(
          'd-none d-lg-flex align-items-lg-center flex-lg-row list-item py-0 list-item-xs fs-small',
          className,
        )}
        data-test={`cleanup-feature-item-${index}`}
      >
        {onSelect && (
          <div
            className='table-column px-2 align-items-center'
            onClick={(e) => {
              e.stopPropagation()
            }}
          >
            <input
              type='checkbox'
              checked={!!isSelected}
              onChange={() => onSelect(projectFlag)}
            />
          </div>
        )}
        <div className='table-column ps-2 px-0 align-items-center flex-1'>
          <div className='mx-0 flex-1 flex-column'>
            <div className='d-flex align-items-center'>
              <FeatureName name={projectFlag.name} />
              <TagValues
                projectId={`${projectFlag.project}`}
                value={projectFlag.tags}
              />
            </div>
            <FeatureDescription description={description} />
          </div>
        </div>
      </div>

      {/* Mobile */}
      <div
        className={classNames(
          'd-flex flex-column justify-content-center px-2 list-item py-1 d-lg-none',
        )}
      >
        <div className='d-flex gap-2 align-items-center'>
          {onSelect && (
            <div
              onClick={(e) => {
                e.stopPropagation()
              }}
            >
              <input
                type='checkbox'
                checked={!!isSelected}
                onChange={() => onSelect(projectFlag)}
              />
            </div>
          )}
          <div className='flex-1 align-items-center flex-wrap'>
            <FeatureName name={projectFlag.name} />
            <TagValues
              projectId={`${projectFlag.project}`}
              value={projectFlag.tags}
            />
          </div>
        </div>
      </div>
    </>
  )
}

export default ProjectFeatureRow
