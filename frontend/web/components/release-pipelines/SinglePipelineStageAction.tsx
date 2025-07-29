import { StageActionRequest } from 'common/types/requests'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import { FLAG_ACTION_OPTIONS } from './constants'
import Icon from 'components/Icon'

const getActionType = (action: StageActionRequest | undefined) => {
  if (!action) {
    return
  }

  if (action.action_body.enabled) {
    return action.action_type
  }

  return `${action.action_type}_DISABLE`
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
  onActionChange: (option: { value: string; label: string }, id: number) => void
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
                    FLAG_ACTION_OPTIONS,
                    { label: 'Select an action', value: '' },
                  )}
                  options={FLAG_ACTION_OPTIONS}
                  onChange={(option: { value: string; label: string }) =>
                    onActionChange(option, actionIndex)
                  }
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
    </>
  )
}

export type { SinglePipelineStageActionProps }
export default SinglePipelineStageAction
