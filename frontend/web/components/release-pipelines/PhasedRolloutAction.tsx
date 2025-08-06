import Checkbox from 'components/base/forms/Checkbox'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import { StageActionBody, StageActionRequest } from 'common/types/requests'
import { useState } from 'react'
import { StageActionType } from 'common/types/responses'
import TimeIntervalInput from './TimeInput'

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
  const [enabled, setEnabled] = useState(action.action_body.enabled)
  const [initialSplit, setInitialSplit] = useState(
    action.action_body.initial_split || 0,
  )
  const [increaseBy, setIncreaseBy] = useState(
    action.action_body.increase_by || 0,
  )
  const [increaseEvery, setIncreaseEvery] = useState(
    action.action_body.increase_every,
  )

  const handleFieldChange = (
    field: 'enabled' | 'initial_split' | 'increase_by' | 'increase_every',
    value: boolean | number | string,
  ) => {
    switch (field) {
      case 'enabled':
        setEnabled(value as boolean)
        break
      case 'initial_split':
        setInitialSplit(value as number)
        break
      case 'increase_by':
        setIncreaseBy(value as number)
        break
      case 'increase_every':
        setIncreaseEvery(value as string)
        break
      default:
        break
    }

    onActionChange?.(action.action_type as StageActionType, {
      ...action.action_body,
      enabled: enabled,
      increase_by: increaseBy,
      increase_every: increaseEvery,
      initial_split: initialSplit,
      // eslint-disable-next-line sort-keys-fix/sort-keys-fix
      [field]: value,
    })
  }

  const handleInputChange = (
    field: 'initial_split' | 'increase_by',
    event: React.ChangeEvent<HTMLInputElement>,
  ) => {
    const value = Utils.safeParseEventValue(event)
    handleFieldChange(field, Number(value))
  }

  return (
    <FormGroup className='pl-4'>
      <div className='mb-4'>
        <Checkbox
          label='Enable'
          checked={enabled}
          onChange={(value) => handleFieldChange('enabled', value)}
        />
      </div>
      <Row>
        <InputGroup
          title='Initial Split'
          inputProps={{
            error: !initialSplit || initialSplit < 0 || initialSplit > 100,
            name: 'initial_split',
          }}
          value={initialSplit}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            handleInputChange('initial_split', event)
          }
          isValid={initialSplit && initialSplit > 0 && initialSplit <= 100}
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
          value={increaseBy}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) =>
            handleInputChange('increase_by', event)
          }
          isValid={increaseBy && increaseBy > 0 && increaseBy <= 100}
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
        interval={increaseEvery}
        onIntervalChange={(interval) =>
          handleFieldChange('increase_every', interval)
        }
      />
    </FormGroup>
  )
}

export default PhasedRolloutAction
