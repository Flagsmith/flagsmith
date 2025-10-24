import { TDiffSegmentOverride } from './diff-utils'
import React, { FC, useMemo } from 'react'
import DiffString from './DiffString'
import DiffEnabled from './DiffEnabled'
import { sortBy } from 'lodash'
import Tabs from 'components/navigation/TabMenu/Tabs'
import TabItem from 'components/navigation/TabMenu/TabItem'
import Icon from 'components/Icon'
import Tooltip from 'components/Tooltip'
import { Link, useHistory } from 'react-router-dom'
import DiffVariations from './DiffVariations'

type DiffSegmentOverride = {
  diff: TDiffSegmentOverride
  projectId: string
  environmentId: string
}

const widths = [200, 80, 105]
const DiffSegmentOverride: FC<DiffSegmentOverride> = ({
  diff,
  environmentId,
  projectId,
}) => {
  return (
    <div>
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
      <div className='px-3'>
        {!!diff.variationDiff?.diffs && (
          <DiffVariations diffs={diff.variationDiff.diffs} />
        )}
      </div>
    </div>
  )
}

type DiffSegmentOverridesType = {
  diffs: TDiffSegmentOverride[] | undefined
  projectId: string
  environmentId: string
}
const DiffSegmentOverrides: FC<DiffSegmentOverridesType> = ({
  diffs,
  environmentId,
  projectId,
}) => {
  const history = useHistory()
  const { created, deleted, modified, unChanged } = useMemo(() => {
    const created: TDiffSegmentOverride[] = []
    const deleted: TDiffSegmentOverride[] = []
    const modified: TDiffSegmentOverride[] = []
    const unChanged: TDiffSegmentOverride[] = []

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
    <Tabs className='mt-4' uncontrolled theme='pill' history={history}>
      {!!created.length && (
        <TabItem
          className='p-0'
          tabLabel={
            <div className='d-flex gap-2'>
              Created <div className='unread'>{created.length}</div>
            </div>
          }
        >
          {tableHeader}
          {created.map((diff, i) => (
            <DiffSegmentOverride
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
          className='p-0'
          tabLabel={
            <div className='d-flex align-items-center'>
              Deleted <div className='unread'>{deleted.length}</div>
            </div>
          }
        >
          {tableHeader}
          {deleted.map((diff, i) => (
            <DiffSegmentOverride
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
          className='p-0'
          tabLabel={
            <div className='d-flex align-items-center'>
              Modified <div className='unread'>{modified.length}</div>
            </div>
          }
        >
          {tableHeader}
          {modified.map((diff, i) => (
            <DiffSegmentOverride
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
          className='p-0'
          tabLabel={
            <div className='d-flex align-items-center'>
              Unchanged <div className='unread'>{unChanged.length}</div>
            </div>
          }
        >
          {tableHeader}
          {unChanged.map((diff, i) => (
            <DiffSegmentOverride
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

export default DiffSegmentOverrides
