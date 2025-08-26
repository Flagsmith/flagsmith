import { FC } from 'react'
import { useHistory } from 'react-router-dom'

import { useHasPermission } from 'common/providers/Permission'

import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import ConfirmRemoveSegment from 'components/modals/ConfirmRemoveSegment'

import { Segment } from 'common/types/responses'
import { MutationDefinition } from '@reduxjs/toolkit/dist/query/endpointDefinitions'
import { MutationTrigger } from '@reduxjs/toolkit/dist/query/react/buildHooks'
import SegmentAction from './components/SegmentAction'
import ConfirmCloneSegment from 'components/modals/ConfirmCloneSegment'
import { useCloneSegmentMutation } from 'common/services/useSegment'
import { Req } from 'common/types/requests'
import Button from 'components/base/forms/Button'

interface SegmentRowProps {
  segment: Segment
  index: number
  projectId: string
  removeSegment: MutationTrigger<
    MutationDefinition<Req['deleteSegment'], any, 'Segment', Segment, 'service'>
  >
}
export const handleRemoveSegment = (
  projectId: string,
  segment: Segment,
  removeSegmentQuery: SegmentRowProps['removeSegment'],
  onComplete?: () => void,
) => {
  const removeSegmentCallback = async () => {
    try {
      await removeSegmentQuery({ id: segment.id, projectId })
      toast(
        <div>
          Removed Segment: <strong>{segment.name}</strong>
        </div>,
      )
      onComplete?.()
    } catch (error) {
      toast(
        <div>
          Error removing segment: <strong>{segment.name}</strong>
        </div>,
        'danger',
      )
    }
  }
  openModal(
    'Remove Segment',
    <ConfirmRemoveSegment segment={segment} cb={removeSegmentCallback} />,
    'p-0',
  )
}
export const SegmentRow: FC<SegmentRowProps> = ({
  index,
  projectId,
  removeSegment: removeSegmentCallback,
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
    handleRemoveSegment(projectId, segment, removeSegmentCallback)
  }

  const [cloneSegment, { isLoading: isCloning }] = useCloneSegmentMutation()

  const isCloningEnabled = Utils.getFlagsmithHasFeature('clone_segment')

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
        {isCloningEnabled ? (
          <SegmentAction
            index={index}
            isRemoveDisabled={!manageSegmentsPermission}
            isCloneDisabled={!manageSegmentsPermission}
            onRemove={onRemoveSegmentClick}
            onClone={handleCloneSegment}
          />
        ) : (
          <Button
            disabled={!manageSegmentsPermission}
            data-test={`remove-segment-btn-${index}`}
            onClick={onRemoveSegmentClick}
            className='btn btn-with-icon'
          >
            <Icon name='trash-2' width={20} fill='#656D7B' />
          </Button>
        )}
      </div>
    </Row>
  )
}

export type { SegmentRowProps }
export default SegmentRow
