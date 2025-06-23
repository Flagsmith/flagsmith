import { SyntheticEvent, useEffect, useMemo, useState } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { useGetSegmentsQuery } from 'common/services/useSegment'
import {
  StageActionType,
  StageTrigger,
  StageTriggerType,
} from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import {
  FLAG_ACTION_OPTIONS,
  TIME_UNIT_OPTIONS,
  TRIGGER_OPTIONS,
} from './constants'
import { StageAction } from 'common/types/responses'
import moment from 'moment'
import Input from 'components/base/forms/Input'
import { PipelineStageRequest } from 'common/types/requests'

type DraftStageType = PipelineStageRequest

type TimeUnit = 'days' | 'hours' | 'minutes'

const CreatePipelineStage = ({
  onChange,
  onRemove,
  projectId,
  showRemoveButton,
  stageData,
}: {
  stageData: DraftStageType
  onChange: (stageData: DraftStageType) => void
  projectId: string
  showRemoveButton?: boolean
  onRemove?: () => void
}) => {
  const [searchInput, setSearchInput] = useState('')
  const [amountOfTime, setAmountOfTime] = useState(1)
  const [selectedTimeUnit, setSelectedTimeUnit] = useState<TimeUnit>('days')
  const [selectedAction, setSelectedAction] = useState<{
    label: string
    value: string
  }>({ label: 'Select an action', value: '' })
  const [selectedSegment, setSelectedSegment] = useState<
    | {
        label: string
        value: number | null
      }
    | undefined
  >()

  const { data: environmentsData, isLoading: isEnvironmentsLoading } =
    useGetEnvironmentsQuery(
      {
        projectId,
      },
      { skip: !projectId },
    )

  const { data: segments, isLoading: isSegmentsLoading } = useGetSegmentsQuery(
    {
      include_feature_specific: true,
      page_size: 1000,
      projectId,
    },
    { skip: !projectId },
  )

  const selectedTrigger = useMemo(() => {
    return TRIGGER_OPTIONS.find(
      (trigger) => trigger.value === stageData.trigger.trigger_type,
    )
  }, [stageData.trigger.trigger_type])

  const segmentOptions = useMemo(() => {
    return segments?.results?.map((segment) => ({
      label: segment.name,
      value: segment.id,
    }))
  }, [segments])

  const environmentOptions = useMemo(() => {
    return environmentsData?.results?.map((environment) => ({
      label: environment.name,
      value: environment.id,
    }))
  }, [environmentsData])

  const handleOnChange = (
    fieldName: keyof DraftStageType,
    value: string | number | StageTrigger | Omit<StageAction, 'id'>[],
  ) => {
    onChange({ ...stageData, [fieldName]: value })
  }

  function formatDurationToHHMMSS(duration: moment.Duration) {
    const totalSeconds = duration.asSeconds()

    const hours = Math.floor(totalSeconds / 3600)
    const minutes = Math.floor((totalSeconds % 3600) / 60)
    const seconds = Math.floor(totalSeconds % 60)

    return `${hours}:${String(minutes).padStart(2, '0')}:${String(
      seconds,
    ).padStart(2, '0')}`
  }

  useEffect(() => {
    if (environmentOptions?.length && stageData.environment === -1) {
      handleOnChange('environment', environmentOptions?.[0]?.value)
    }

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [environmentOptions, stageData])

  const handleSegmentChange = (option: { value: number; label: string }) => {
    setSelectedSegment(option)

    if (option?.value) {
      const actions = stageData.actions.map((action) => {
        if (action.action_type === StageActionType.TOGGLE_FEATURE_FOR_SEGMENT) {
          return {
            ...action,
            action_body: { enabled: true, segment_id: option?.value },
          }
        }
        return action
      })

      handleOnChange('actions', actions)
    }
  }

  const handleActionChange = (option: { value: string; label: string }) => {
    setSelectedAction(option)
    setSelectedSegment(undefined)

    if (option.value === '') {
      return handleOnChange('actions', [])
    }

    const isSegment = option.value.includes('FOR_SEGMENT')
    const enabled = !option.value.includes('DISABLE')

    const action_type = isSegment
      ? StageActionType.TOGGLE_FEATURE_FOR_SEGMENT
      : StageActionType.TOGGLE_FEATURE

    const action_body = { enabled }

    handleOnChange('actions', [{ action_body, action_type }])
  }

  const setWaitForTrigger = (time: number, unit: TimeUnit) => {
    const duration = moment.duration(time, unit)
    const formatted = formatDurationToHHMMSS(duration)

    handleOnChange('trigger', {
      trigger_body: { wait_for: formatted },
      trigger_type: StageTriggerType.WAIT_FOR,
    } as StageTrigger)
  }

  const handleTriggerChange = (option: { value: string; label: string }) => {
    if (option.value === StageTriggerType.WAIT_FOR) {
      const time = 1
      const unit = 'days'

      setAmountOfTime(time)
      setSelectedTimeUnit(unit)

      setWaitForTrigger(time, unit)

      return
    }

    handleOnChange('trigger', {
      trigger_body: null,
      trigger_type: option.value,
    } as StageTrigger)
  }

  return (
    <div
      className='p-3 border-1 rounded position-relative'
      style={{ minWidth: '360px' }}
    >
      {showRemoveButton && (
        <div className='position-absolute top-0 end-0 p-2'>
          <Button theme='text' onClick={() => onRemove?.()}>
            <Icon fill='#8F98A3' name='trash-2' width={16} />
          </Button>
        </div>
      )}
      <FormGroup>
        <InputGroup
          title='Stage Name'
          inputProps={{ className: 'full-width' }}
          value={stageData.name}
          isValid={!!stageData.name.length}
          onChange={(e: SyntheticEvent<HTMLInputElement>) => {
            handleOnChange('name', e.currentTarget.value)
          }}
        />
      </FormGroup>
      <FormGroup>
        <InputGroup
          title='Environment'
          component={
            <Select
              value={Utils.toSelectedValue(
                stageData.environment,
                environmentOptions,
              )}
              isDisabled={isEnvironmentsLoading}
              isLoading={isEnvironmentsLoading}
              inputValue={searchInput}
              onInputChange={setSearchInput}
              options={environmentOptions}
              onChange={(option: { value: number; label: string }) =>
                handleOnChange('environment', option.value)
              }
            />
          }
        />
      </FormGroup>
      <FormGroup>
        <InputGroup
          title='Trigger'
          component={
            <Select
              isDisabled={isEnvironmentsLoading}
              isLoading={isEnvironmentsLoading}
              value={selectedTrigger}
              options={TRIGGER_OPTIONS}
              onChange={handleTriggerChange}
            />
          }
        />
      </FormGroup>
      {selectedTrigger?.value === StageTriggerType.WAIT_FOR && (
        <FormGroup className='pl-4 d-flex align-items-center'>
          <div className='flex-1 mr-3'>
            <Input
              value={`${amountOfTime}`}
              inputClassName='input flex-1'
              name='amount-of-time'
              isValid={amountOfTime > 0}
              min={1}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => {
                const value = Utils.safeParseEventValue(e)
                setWaitForTrigger(Number(value) || 1, selectedTimeUnit)
              }}
              type='number'
              placeholder='Amount of time'
            />
          </div>
          <div className='w-50'>
            <Select
              value={Utils.toSelectedValue(selectedTimeUnit, TIME_UNIT_OPTIONS)}
              options={TIME_UNIT_OPTIONS}
              onChange={(option: { value: string; label: string }) =>
                setWaitForTrigger(amountOfTime, option.value as TimeUnit)
              }
            />
          </div>
        </FormGroup>
      )}
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
              value={selectedAction}
              options={FLAG_ACTION_OPTIONS}
              onChange={handleActionChange}
            />
          }
        />
      </FormGroup>
      {selectedAction.value.includes('FOR_SEGMENT') && (
        <FormGroup className='pl-4'>
          <InputGroup
            title='Segment'
            component={
              <Select
                menuPortalTarget={document.body}
                maxMenuHeight={120}
                isDisabled={isSegmentsLoading}
                isLoading={isSegmentsLoading}
                value={Utils.toSelectedValue(selectedSegment, segmentOptions)}
                options={segmentOptions}
                onChange={handleSegmentChange}
              />
            }
          />
        </FormGroup>
      )}
    </div>
  )
}

export type { DraftStageType }
export default CreatePipelineStage
