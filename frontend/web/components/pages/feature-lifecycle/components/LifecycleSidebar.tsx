import React, { FC } from 'react'
import classNames from 'classnames'
import SidebarLink from 'components/navigation/SidebarLink'
import { SECTIONS } from 'components/pages/feature-lifecycle/constants'
import type {
  Section,
  LifecycleCounts,
} from 'components/pages/feature-lifecycle/types'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'

type LifecycleSidebarProps = {
  projectId: number
  activeSection: Section
  counts: LifecycleCounts
  monitorCount: number | undefined
  removeCount: number | undefined
}

const LifecycleSidebar: FC<LifecycleSidebarProps> = ({
  activeSection,
  counts,
  monitorCount,
  projectId,
  removeCount,
}) => {
  return (
    <div className='border-md-right home-aside d-flex flex-column pe-0 me-0'>
      <div className='flex-1 flex-column ms-0 me-2'>
        <div className='d-flex px-2 pb-1 pt-2 justify-content-between align-items-center'>
          <div className='text-muted fs-captionXSmall'>LIFECYCLE STAGES</div>
          <Button size='xSmall' className='ps-2 pe-1'>
            <div className='d-flex align-items-center gap-1'>
              Add
              <Icon width={16} name='plus' />
            </div>
          </Button>
        </div>
        <hr className='mt-1 mb-2' />
        <div className='d-flex flex-column mx-0 py-1 py-md-0 gap-1'>
          {SECTIONS.map((s) => {
            let count: number | undefined
            if (s.key === 'monitor') {
              count = monitorCount
            } else if (s.key === 'remove') {
              count = removeCount
            } else {
              count = counts[s.key]
            }

            return (
              <SidebarLink
                key={s.key}
                icon={s.icon}
                className='lh-1'
                to={`/project/${projectId}/lifecycle/${s.key}`}
                isActive={() => activeSection === s.key}
              >
                <div className='d-flex align-items-center'>
                  {s.label}
                  {count !== undefined && (
                    <span
                      className={classNames(
                        'ms-1 px-2 unread rounded d-inline',
                        {
                          'bg-light300 text-muted': activeSection !== s.key,
                        },
                      )}
                    >
                      {count}
                    </span>
                  )}
                </div>
              </SidebarLink>
            )
          })}
        </div>
      </div>
    </div>
  )
}

export default LifecycleSidebar
