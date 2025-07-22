import { SyntheticEvent, useEffect, useMemo, useState } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import {
  StageActionType,
  StageTrigger,
  StageTriggerType,
} from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import {
  NEW_PIPELINE_STAGE,
  NEW_PIPELINE_STAGE_ACTION,
  TIME_UNIT_OPTIONS,
  TimeUnit,
  TRIGGER_OPTIONS,
} from './constants'
import moment from 'moment'
import Input from 'components/base/forms/Input'
import { PipelineStageRequest, StageActionRequest } from 'common/types/requests'
import PipelineStageActions from './PipelineStageActions'

type TimeUnitType = (typeof TimeUnit)[keyof typeof TimeUnit]

const CreatePipelineStage = ({
  onChange,
  onRemove,
  projectId,
  showRemoveButton,
  stageData,
}: {
  stageData: PipelineStageRequest
  onChange: (stageData: PipelineStageRequest) => void
  projectId: number
  showRemoveButton?: boolean
  onRemove?: () => void
}) => {
  const existingWaitForTime = Utils.getExistingWaitForTime(
    stageData?.trigger?.trigger_body?.wait_for,
  )

  const [searchInput, setSearchInput] = useState('')

  // These are not fetched directly from stageData because
  // it gives more flexibility to the user to set 24h or 1 day
  const [amountOfTime, setAmountOfTime] = useState(
    existingWaitForTime?.amountOfTime || 1,
  )
  const [selectedTimeUnit, setSelectedTimeUnit] = useState<TimeUnitType>(
    existingWaitForTime?.timeUnit || TimeUnit.DAY,
  )

  const { data: environmentsData, isLoading: isEnvironmentsLoading } =
    useGetEnvironmentsQuery(
      {
        projectId: `${projectId}`,
      },
      { skip: !projectId },
    )

  const selectedTrigger = useMemo(() => {
    return TRIGGER_OPTIONS.find(
      (trigger) => trigger.value === stageData.trigger.trigger_type,
    )
  }, [stageData.trigger.trigger_type])

  const environmentWithFeatureVersioningOptions = useMemo(() => {
    const environmentsWithV2FeatureVersioning =
      environmentsData?.results?.filter(
        (environment) => environment.use_v2_feature_versioning,
      )
    return environmentsWithV2FeatureVersioning?.map((environment) => ({
      label: environment.name,
      value: environment.id,
    }))
  }, [environmentsData])

  const handleOnChange = (
    fieldName: keyof PipelineStageRequest,
    value: string | number | StageTrigger | StageActionRequest[],
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
    if (
      environmentWithFeatureVersioningOptions?.length &&
      stageData.environment === -1
    ) {
      handleOnChange(
        'environment',
        environmentWithFeatureVersioningOptions?.[0]?.value,
      )
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [environmentWithFeatureVersioningOptions, stageData])

  const handleSegmentChange = (
    option: { value: number; label: string },
    actionIndex: number,
  ) => {
    if (!option?.value) {
      return
    }

    const actions = stageData.actions.map((action, idx) => {
      if (
        action.action_type === StageActionType.TOGGLE_FEATURE_FOR_SEGMENT &&
        idx === actionIndex
      ) {
        return {
          ...action,
          action_body: { ...action.action_body, segment_id: option?.value },
        }
      }
      return action
    })

    handleOnChange('actions', actions)
  }

  const handleActionChange = (
    option: { value: string; label: string },
    actionIndex: number,
  ) => {
    if (option.value === '') {
      return
    }

    const isSegment = option.value.includes('FOR_SEGMENT')
    const enabled = !option.value.includes('DISABLE')

    const action_type = isSegment
      ? StageActionType.TOGGLE_FEATURE_FOR_SEGMENT
      : StageActionType.TOGGLE_FEATURE

    const action_body = { enabled }

    const actions = stageData.actions.map((action, idx) => {
      if (idx === actionIndex) {
        return { action_body, action_type }
      }
      return action
    })
    handleOnChange('actions', actions)
  }

  const handleAddAction = () => {
    const defaultDraftAction = NEW_PIPELINE_STAGE_ACTION
    handleOnChange('actions', [...stageData.actions, defaultDraftAction])
  }

  const handleRemoveAction = (index: number) => {
    const actions = stageData.actions.filter((_, i) => i !== index)
    handleOnChange('actions', actions)
  }

  const setWaitForTrigger = (time: number, unit: TimeUnitType) => {
    setAmountOfTime(time)
    setSelectedTimeUnit(unit)

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
      const unit = TimeUnit.DAY

      setWaitForTrigger(time, unit)
      return
    }

    handleOnChange('trigger', {
      trigger_body: null,
      trigger_type: option.value,
    } as StageTrigger)
  }

  const hasNoFeatureVersioningEnvironments =
    !!environmentsData?.results?.length &&
    !environmentWithFeatureVersioningOptions?.length

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
          inputProps={{
            error: hasNoFeatureVersioningEnvironments
              ? 'No environments with feature versioning enabled'
              : undefined,
          }}
          component={
            <Select
              styles={{
                control: (base: any) => ({
                  ...base,
                  '&:hover': {
                    borderColor: hasNoFeatureVersioningEnvironments
                      ? '#ef4d56'
                      : base.borderColor,
                  },
                  borderColor: hasNoFeatureVersioningEnvironments
                    ? '#ef4d56'
                    : base.borderColor,
                  boxShadow: hasNoFeatureVersioningEnvironments
                    ? '0 0 0 1px #ef4d56'
                    : base.boxShadow,
                }),
              }}
              value={Utils.toSelectedValue(
                stageData.environment,
                environmentWithFeatureVersioningOptions,
              )}
              isDisabled={isEnvironmentsLoading}
              isLoading={isEnvironmentsLoading}
              inputValue={searchInput}
              onInputChange={setSearchInput}
              options={environmentWithFeatureVersioningOptions}
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
      <PipelineStageActions
        actions={stageData.actions}
        projectId={projectId}
        onActionChange={handleActionChange}
        onSegmentChange={handleSegmentChange}
        onAddAction={handleAddAction}
        onRemoveAction={handleRemoveAction}
      />
    </div>
  )
}

export default CreatePipelineStage
