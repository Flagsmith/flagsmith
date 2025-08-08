import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import { StageActionRequest } from 'common/types/requests'
import { useState } from 'react'
import { StageActionBody, StageActionType } from 'common/types/responses'
import TimeIntervalInput from './TimeInput'
import Switch from 'components/Switch'

interface PhasedRolloutActionProps {
  action: StageActionRequest
  onActionChange: (
    actionType: StageActionType,
    actionBody: StageActionBody,
  ) => void
}

const PhasedRolloutAction = ({
  action,
  onActionChange,
}: PhasedRolloutActionProps) => {
  const [phasedRolloutState, setPhasedRolloutState] = useState({
    enabled: action.action_body?.enabled || true,
    increase_by: action.action_body?.increase_by,
    increase_every: action.action_body?.increase_every || '24:00:00',
    initial_split: action.action_body?.initial_split,
  })

  const handleFieldChange = (
    field: 'enabled' | 'initial_split' | 'increase_by' | 'increase_every',
    value: boolean | number | string | undefined,
  ) => {
    const updatedState = { ...phasedRolloutState, [field]: value }
    setPhasedRolloutState(updatedState)
    onActionChange?.(action.action_type as StageActionType, {
      ...action.action_body,
      ...updatedState,
    })
  }

  const handleInputChange = (
    field: 'initial_split' | 'increase_by',
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const value = Utils.safeParseEventValue(event)
    handleFieldChange(field, value)
  }

  return (
    <FormGroup className='pl-4'>
      <div className='mb-4 flex'>
        <label>Enable</label>
        <Switch
          checked={phasedRolloutState.enabled}
          onChange={(enabled: boolean) => {
            handleFieldChange('enabled', enabled)
          }}
          className='ml-0'
        />
      </div>
      <Row>
        <InputGroup
          title='Initial Split'
          inputProps={{
            error:
              !phasedRolloutState.initial_split ||
              Number(phasedRolloutState.initial_split) < 0 ||
              Number(phasedRolloutState.initial_split) > 100,
            name: 'initial_split',
          }}
          value={phasedRolloutState.initial_split}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            handleInputChange('initial_split', event)
          }
          isValid={
            phasedRolloutState.initial_split &&
            Number(phasedRolloutState.initial_split) > 0 &&
            Number(phasedRolloutState.initial_split) <= 100
          }
          type='number'
          name='initialSplit'
          id='initialSplit'
          placeholder='E.g. 10'
          className='w-50'
        />
        <span className='ml-2'>%</span>
      </Row>
      <Row className='mt-2 gap-2'>
        <InputGroup
          title='Increase by'
          inputProps={{
            error: false,
            name: 'increase_by',
          }}
          value={phasedRolloutState.increase_by}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            handleInputChange('increase_by', event)
          }
          isValid={
            phasedRolloutState.increase_by &&
            Number(phasedRolloutState.increase_by) > 0 &&
            Number(phasedRolloutState.increase_by) <= 100
          }
          type='number'
          name='initialSplit'
          id='initialSplit'
          placeholder='E.g. 10'
          className='w-50'
        />
        <span className='mr-2'>%</span>
      </Row>
      <TimeIntervalInput
        title='Every'
        interval={phasedRolloutState.increase_every}
        onIntervalChange={(interval) =>
          handleFieldChange('increase_every', interval)
        }
      />
    </FormGroup>
  )
}

export default PhasedRolloutAction
