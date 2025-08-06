import { StageActionBody, StageActionRequest } from 'common/types/requests'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import { FLAG_ACTION_OPTIONS } from './constants'
import Icon from 'components/Icon'
import { StageActionType } from 'common/types/responses'
import PhasedRolloutAction from './PhasedRolloutAction'
import { useMemo } from 'react'

const getActionType = (action: StageActionRequest | undefined) => {
  if (!action) {
    return
  }

  if (action.action_type.includes('TOGGLE_FEATURE')) {
    return `${action.action_type}${
      action.action_body.enabled ? '' : '_DISABLE'
    }`
  }

  return action.action_type
}

const getSegment = (action: StageActionRequest | undefined) => {
  if (!action) {
    return
  }

  return action.action_body.segment_id
}

interface SinglePipelineStageActionProps {
  actionIndex?: number
  action?: StageActionRequest
  onRemoveAction?: (id: number) => void
  onActionChange: (
    stageIndex: number,
    actionType: StageActionType,
    actionBody: StageActionBody,
  ) => void
  onSegmentChange: (
    option: { value: number; label: string },
    id: number,
  ) => void
  isSegmentsLoading: boolean
  segmentOptions: { label: string; value: number }[] | undefined
}

const SinglePipelineStageAction = ({
  action,
  actionIndex = 0,
  isSegmentsLoading,
  onActionChange,
  onRemoveAction,
  onSegmentChange,
  segmentOptions,
}: SinglePipelineStageActionProps) => {
  const isPhasedRolloutEnabled = true //Utils.getFlagsmithHasFeature(
  //   'pipelines-phased-rollout',
  // )

  const actionOptions = useMemo(() => {
    return FLAG_ACTION_OPTIONS.filter((option) => {
      if (
        isPhasedRolloutEnabled &&
        option.value === StageActionType.PHASED_ROLLOUT
      ) {
        return true
      }
      return option.value !== StageActionType.PHASED_ROLLOUT
    })
  }, [isPhasedRolloutEnabled])

  return (
    <>
      <Row>
        <div className='flex-1 and-divider__line' />
        <div className='mx-2'>{actionIndex === 0 ? 'Then' : 'And'}</div>
        <div className='flex-1 and-divider__line' />
      </Row>
      <FormGroup className='mt-2'>
        <InputGroup
          title='Flag Action'
          component={
            <div className='d-flex align-items-center'>
              <div className='w-100'>
                <Select
                  maxMenuHeight={180}
                  value={Utils.toSelectedValue(
                    getActionType(action),
                    actionOptions,
                    { label: 'Select an action', value: '' },
                  )}
                  options={actionOptions}
                  onChange={(option: { value: string; label: string }) => {
                    if (option.value.includes('TOGGLE_FEATURE')) {
                      const isSegment = option.value.includes('FOR_SEGMENT')
                      const enabled = !option.value.includes('DISABLE')

                      const action_type = isSegment
                        ? StageActionType.TOGGLE_FEATURE_FOR_SEGMENT
                        : StageActionType.TOGGLE_FEATURE

                      const action_body = { enabled }

                      return onActionChange(
                        actionIndex,
                        action_type,
                        action_body,
                      )
                    }

                    return onActionChange(
                      actionIndex,
                      option.value as StageActionType,
                      { enabled: true },
                    )
                  }}
                />
              </div>
              {onRemoveAction && (
                <div
                  className='ml-2 clickable'
                  onClick={() => onRemoveAction(actionIndex)}
                >
                  <Icon name='trash-2' width={20} fill='#8F98A3' />
                </div>
              )}
            </div>
          }
        />
      </FormGroup>
      {action?.action_type.includes('FOR_SEGMENT') && (
        <FormGroup className='pl-4'>
          <InputGroup
            title='Segment'
            component={
              <Select
                maxMenuHeight={180}
                isDisabled={isSegmentsLoading}
                isLoading={isSegmentsLoading}
                value={Utils.toSelectedValue(
                  getSegment(action),
                  segmentOptions,
                  { label: 'Select a segment', value: '' },
                )}
                options={segmentOptions}
                onChange={(option: { value: number; label: string }) =>
                  onSegmentChange(option, actionIndex)
                }
              />
            }
          />
        </FormGroup>
      )}
      {isPhasedRolloutEnabled &&
        action?.action_type === StageActionType.PHASED_ROLLOUT && (
          <PhasedRolloutAction
            action={action}
            onActionChange={(actionType, actionBody) =>
              onActionChange(actionIndex, actionType, actionBody)
            }
          />
        )}
    </>
  )
}

export type { SinglePipelineStageActionProps }
export default SinglePipelineStageAction
