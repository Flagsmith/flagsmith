import { SyntheticEvent, useEffect, useMemo, useState } from 'react'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import {
  StageActionBody,
  StageActionType,
  StageTrigger,
  StageTriggerType,
} from 'common/types/responses'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import { NEW_PIPELINE_STAGE_ACTION, TRIGGER_OPTIONS } from './constants'
import { PipelineStageRequest, StageActionRequest } from 'common/types/requests'
import PipelineStageActions from './PipelineStageActions'
import TimeIntervalInput from './TimeInput'

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
    actionIndex: number,
    actionType: StageActionType,
    actionBody: StageActionBody,
  ) => {
    const actions = stageData.actions.map((action, idx) => {
      if (idx === actionIndex) {
        return { action_body: actionBody, action_type: actionType }
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

  const handleTriggerChange = (option: { value: string; label: string }) => {
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
          <TimeIntervalInput
            interval={existingWaitForTime?.trigger_body?.wait_for}
            onIntervalChange={(interval) => {
              handleOnChange('trigger', {
                trigger_body: { wait_for: interval },
                trigger_type: StageTriggerType.WAIT_FOR,
              })
            }}
          />
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
