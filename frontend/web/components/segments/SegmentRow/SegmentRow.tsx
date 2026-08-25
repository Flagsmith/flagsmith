import { FC } from 'react'
import classNames from 'classnames'
import { useHistory } from 'react-router-dom'

import { useHasPermission } from 'common/providers/Permission'

import { Segment } from 'common/types/responses'
import SegmentAction from './components/SegmentAction'
import { SegmentMembershipTotalBadge } from 'components/segments/SegmentMembershipBadge'
import Chip from 'components/base/Chip'
import ConfirmCloneSegment from 'components/modals/ConfirmCloneSegment'
import { useCloneSegmentMutation } from 'common/services/useSegment'
import { handleRemoveSegment } from 'components/modals/ConfirmRemoveSegment'
import { ProjectPermission } from 'common/types/permissions.types'

interface SegmentRowProps {
  segment: Segment
  index: number
  projectId: string
}

const SegmentRow: FC<SegmentRowProps> = ({ index, projectId, segment }) => {
  const history = useHistory()
  const { cohort, description, feature, id, name } = segment

  const isPendingDeletion = !!cohort?.deletion_requested_at

  const { permission: manageSegmentsPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: ProjectPermission.MANAGE_SEGMENTS,
  })

  const onRemoveSegmentClick = () => {
    handleRemoveSegment(projectId, segment)
  }

  const [cloneSegment, { isLoading: isCloning }] = useCloneSegmentMutation()

  const cloneSegmentCallback = async (name: string) => {
    try {
      await cloneSegment({ name, projectId, segmentId: segment.id }).unwrap()
      toast(
        <div>
          Cloned Segment: <strong>{segment.name}</strong> into{' '}
          <strong>{name}</strong>
        </div>,
      )
    } catch (error) {
      toast(
        <div>
          Error cloning segment: <strong>{segment.name}</strong>
        </div>,
        'danger',
      )
    }
  }

  const handleCloneSegment = () => {
    openModal(
      'Clone Segment',
      <ConfirmCloneSegment
        segment={segment}
        cb={cloneSegmentCallback}
        isLoading={isCloning}
      />,
      'p-0',
    )
  }

  return (
    <Row
      className={classNames('list-item', {
        'clickable': !isPendingDeletion,
        'opacity-50': isPendingDeletion,
      })}
      key={id}
      space
    >
      <Flex
        className='table-column px-3'
        onClick={
          manageSegmentsPermission && !isPendingDeletion
            ? () =>
                history.push(
                  `${document.location.pathname.replace(/\/$/, '')}/${id}`,
                )
            : undefined
        }
      >
        <Row data-test={`segment-${index}-name`} className='font-weight-medium'>
          {name}
          {feature && (
            <div className='chip chip--xs ml-2'>Feature-Specific</div>
          )}
          {!!cohort && (
            <Chip className='ml-2' size='xs' variant='accent'>
              {cohort.source_type.toUpperCase()}
            </Chip>
          )}
          {!!cohort && (
            <Chip className='ml-2' size='xs'>
              {cohort.environment_name}
            </Chip>
          )}
          {isPendingDeletion && (
            <Chip className='ml-2' size='xs'>
              Deleting
            </Chip>
          )}
          <SegmentMembershipTotalBadge
            memberships={segment.membership_counts}
          />
        </Row>
        <div className='list-item-subtitle mt-1'>
          {description || 'No description'}
        </div>
      </Flex>
      <div className='table-column'>
        {!isPendingDeletion && (
          <SegmentAction
            index={index}
            isRemoveDisabled={!manageSegmentsPermission}
            isCloneDisabled={!manageSegmentsPermission}
            onRemove={onRemoveSegmentClick}
            onClone={handleCloneSegment}
          />
        )}
      </div>
    </Row>
  )
}

export default SegmentRow
