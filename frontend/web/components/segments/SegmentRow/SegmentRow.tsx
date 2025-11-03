import { FC } from 'react'
import { useHistory } from 'react-router-dom'

import { useHasPermission } from 'common/providers/Permission'

import Utils from 'common/utils/utils'
import Icon from 'components/Icon'

import { Segment } from 'common/types/responses'
import SegmentAction from './components/SegmentAction'
import ConfirmCloneSegment from 'components/modals/ConfirmCloneSegment'
import { useCloneSegmentMutation } from 'common/services/useSegment'
import Button from 'components/base/forms/Button'
import { handleRemoveSegment } from 'components/modals/ConfirmRemoveSegment'

interface SegmentRowProps {
  segment: Segment
  index: number
  projectId: string
}

export const SegmentRow: FC<SegmentRowProps> = ({
  index,
  projectId,
  segment,
}) => {
  const history = useHistory()
  const { description, feature, id, name } = segment

  const { permission: manageSegmentsPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_SEGMENTS',
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
    <Row className='list-item clickable' key={id} space>
      <Flex
        className='table-column px-3'
        onClick={
          manageSegmentsPermission
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
        </Row>
        <div className='list-item-subtitle mt-1'>
          {description || 'No description'}
        </div>
      </Flex>
      <div className='table-column'>
        <SegmentAction
          index={index}
          isRemoveDisabled={!manageSegmentsPermission}
          isCloneDisabled={!manageSegmentsPermission}
          onRemove={onRemoveSegmentClick}
          onClone={handleCloneSegment}
        />
      </div>
    </Row>
  )
}

export type { SegmentRowProps }
export default SegmentRow
