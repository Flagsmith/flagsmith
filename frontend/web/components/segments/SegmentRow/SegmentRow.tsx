// TODO: Migrate to new router
import { FC } from 'react'
import { RouterChildContext } from 'react-router'

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

interface SegmentRowProps {
  segment: Segment
  index: number
  projectId: string
  router: RouterChildContext['router']
  removeSegment: MutationTrigger<
    MutationDefinition<Req['deleteSegment'], any, 'Segment', Segment, 'service'>
  >
}

export const SegmentRow: FC<SegmentRowProps> = ({
  index,
  projectId,
  removeSegment,
  router,
  segment,
}) => {
  const { description, feature, id, name } = segment

  const { permission: manageSegmentsPermission } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_SEGMENTS',
  })

  const [cloneSegment, { isLoading: isCloning }] = useCloneSegmentMutation()

  const isCloningEnabled = Utils.getFlagsmithHasFeature('clone_segment')

  const removeSegmentCallback = async () => {
    try {
      await removeSegment({ id, projectId })
      toast(
        <div>
          Removed Segment: <strong>{segment.name}</strong>
        </div>,
      )
    } catch (error) {
      toast(
        <div>
          Error removing segment: <strong>{segment.name}</strong>
        </div>,
        'danger',
      )
    }
  }

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

  const handleRemoveSegment = () => {
    openModal(
      'Remove Segment',
      <ConfirmRemoveSegment segment={segment} cb={removeSegmentCallback} />,
      'p-0',
    )
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
                router.history.push(
                  `${document.location.pathname}?${Utils.toParam({
                    ...Utils.fromParam(),
                    id,
                  })}`,
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
            onRemove={handleRemoveSegment}
            onClone={handleCloneSegment}
          />
        ) : (
          <Button
            disabled={!manageSegmentsPermission}
            data-test={`remove-segment-btn-${index}`}
            onClick={handleRemoveSegment}
            className='btn btn-with-icon'
          >
            <Icon name='trash-2' width={20} fill='#656D7B' />
          </Button>
        )}
      </div>
    </Row>
  )
}
