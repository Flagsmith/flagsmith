import { TDiffSegment } from './diff-utils'
import React, { FC, useMemo } from 'react'
import DiffString from './DiffString'
import DiffEnabled from './DiffEnabled'
import { sortBy } from 'lodash'
import Tabs from 'components/base/forms/Tabs'
import TabItem from 'components/base/forms/TabItem'
import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import Tooltip from 'components/Tooltip'
import { Link } from 'react-router-dom'

type DiffSegment = {
  diff: TDiffSegment
  projectId: string
  environmentId: string
}

const widths = [200, 80, 105]
const DiffSegment: FC<DiffSegment> = ({ diff, environmentId, projectId }) => {
  return (
    <div className={'flex-row list-item list-item-sm'}>
      <div style={{ width: widths[0] }} className='table-column'>
        <div>
          <Tooltip
            title={
              <>
                <div className='d-flex fw-semibold gap-2 align-items-center'>
                  {!!diff.conflict && <Icon name='warning' width={16} />}
                  {diff.segment?.name}
                </div>
                {!!diff.conflict && (
                  <Link
                    to={`/project/${projectId}/environment/${environmentId}/change-requests/${diff.conflict.original_cr_id}`}
                  >
                    View Change Request
                  </Link>
                )}
              </>
            }
          >
            {diff.conflict
              ? 'A change request was published since the creation of this one that also modified the value for this segment.'
              : null}
          </Tooltip>
        </div>
      </div>
      <div style={{ width: widths[1] }} className='table-column text-center'>
        <DiffString
          oldValue={diff.created ? diff.newPriority : diff.oldPriority}
          newValue={diff.deleted ? diff.oldPriority : diff.newPriority}
        />
      </div>
      <div className='table-column flex-1 overflow-hidden'>
        <DiffString
          oldValue={diff.created ? diff.newValue : diff.oldValue}
          newValue={diff.deleted ? diff.oldValue : diff.newValue}
        />
      </div>
      <div style={{ width: widths[2] }} className='table-column'>
        <DiffEnabled
          oldValue={diff.created ? diff.newEnabled : diff.oldEnabled}
          newValue={diff.deleted ? diff.oldEnabled : diff.newEnabled}
        />
      </div>
    </div>
  )
}

type DiffSegmentsType = {
  diffs: TDiffSegment[] | undefined
  projectId: string
  environmentId: string
}
const DiffSegments: FC<DiffSegmentsType> = ({
  diffs,
  environmentId,
  projectId,
}) => {
  const { created, deleted, modified, unChanged } = useMemo(() => {
    const created: TDiffSegment[] = []
    const deleted: TDiffSegment[] = []
    const modified: TDiffSegment[] = []
    const unChanged: TDiffSegment[] = []

    sortBy(diffs || [], (diff) => diff.newPriority)?.forEach((diff) => {
      if (diff.created) {
        created.push(diff)
      } else if (diff.deleted) {
        deleted.push(diff)
      } else if (diff.totalChanges) {
        modified.push(diff)
      } else {
        unChanged.push(diff)
      }
    })
    return { created, deleted, modified, unChanged }
  }, [diffs])

  const tableHeader = (
    <Row className='table-header mt-4'>
      <div style={{ width: widths[0] }} className='table-column'>
        Segment
      </div>
      <div style={{ width: widths[1] }} className='table-column'>
        Priority
      </div>
      <div className='table-column flex-fill'>Value</div>
      <div style={{ width: widths[2] }} className='table-column'>
        Enabled
      </div>
    </Row>
  )

  return diffs ? (
    <Tabs className='mt-4' uncontrolled theme='pill'>
      {!!created.length && (
        <TabItem
          tabLabel={
            <div>
              Created <div className='unread'>{created.length}</div>
            </div>
          }
        >
          {tableHeader}
          {created.map((diff, i) => (
            <DiffSegment
              environmentId={environmentId}
              projectId={projectId}
              key={i}
              diff={diff}
            />
          ))}
        </TabItem>
      )}
      {!!deleted.length && (
        <TabItem
          tabLabel={
            <div>
              Deleted <div className='unread'>{deleted.length}</div>
            </div>
          }
        >
          {tableHeader}
          {deleted.map((diff, i) => (
            <DiffSegment
              environmentId={environmentId}
              projectId={projectId}
              key={i}
              diff={diff}
            />
          ))}
        </TabItem>
      )}
      {!!modified.length && (
        <TabItem
          tabLabel={
            <div>
              Modified <div className='unread'>{modified.length}</div>
            </div>
          }
        >
          {tableHeader}
          {modified.map((diff, i) => (
            <DiffSegment
              environmentId={environmentId}
              projectId={projectId}
              key={i}
              diff={diff}
            />
          ))}
        </TabItem>
      )}
      {!!unChanged.length && (
        <TabItem
          tabLabel={
            <div>
              Unchanged <div className='unread'>{unChanged.length}</div>
            </div>
          }
        >
          {tableHeader}
          {unChanged.map((diff, i) => (
            <DiffSegment
              environmentId={environmentId}
              projectId={projectId}
              key={i}
              diff={diff}
            />
          ))}
        </TabItem>
      )}
    </Tabs>
  ) : (
    <div className={'text-center'}>
      <Loader />
    </div>
  )
}

export default DiffSegments
