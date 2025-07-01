import { StageActionRequest } from 'common/types/requests'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import { FLAG_ACTION_OPTIONS } from './constants'

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
  action?: StageActionRequest
  onActionChange: (option: { value: string; label: string }) => void
  onSegmentChange: (option: { value: number; label: string }) => void
  isSegmentsLoading: boolean
  segmentOptions: { label: string; value: number }[] | undefined
}

const SinglePipelineStageAction = ({
  action,
  isSegmentsLoading,
  onActionChange,
  onSegmentChange,
  segmentOptions,
}: SinglePipelineStageActionProps) => {
  return (
    <>
      <Row>
        <div className='flex-1 and-divider__line' />
        <div className='mx-2'>Then</div>
        <div className='flex-1 and-divider__line' />
      </Row>
      <FormGroup>
        <InputGroup
          title='Flag Action'
          component={
            <Select
              menuPortalTarget={document.body}
              maxMenuHeight={120}
              value={Utils.toSelectedValue(
                getActionType(action),
                FLAG_ACTION_OPTIONS,
                { label: 'Select an action', value: '' },
              )}
              options={FLAG_ACTION_OPTIONS}
              onChange={onActionChange}
            />
          }
        />
      </FormGroup>
      {action?.action_type.includes('FOR_SEGMENT') && (
        <FormGroup className='pl-4'>
          <InputGroup
            title='Segment'
            component={
              <Select
                menuPortalTarget={document.body}
                maxMenuHeight={120}
                isDisabled={isSegmentsLoading}
                isLoading={isSegmentsLoading}
                value={Utils.toSelectedValue(
                  getSegment(action),
                  segmentOptions,
                  { label: 'Select a segment', value: '' },
                )}
                options={segmentOptions}
                onChange={onSegmentChange}
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
