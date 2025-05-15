import { useEffect, useState } from 'react'
import CreatePipelineStage, { DraftStageType } from './CreatePipelineStage'
import Breadcrumb from 'components/Breadcrumb'
import { Button } from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { StageActionType, StageTriggerType } from 'common/types/responses'
import Icon from 'components/Icon'
import { useCreateReleasePipelineMutation } from 'common/services/useReleasePipelines'
import { useHistory, useParams } from 'react-router'
import StageArrow from './StageArrow'
import { ReleasePipelineRequest } from 'common/types/requests'

const blankStage: DraftStageType = {
  actions: [],
  environment: -1,
  name: '',
  order: 0,
  trigger: {
    trigger_body: null,
    trigger_type: StageTriggerType.ON_ENTER,
  },
}

function CreateReleasePipeline() {
  const history = useHistory()
  const { projectId } = useParams<{ projectId: string }>()

  const [
    createReleasePipeline,
    {
      error: createPipelineError,
      isError: isCreatingPipelineError,
      isLoading: isCreatingPipeline,
      isSuccess: isCreatingPipelineSuccess,
    },
  ] = useCreateReleasePipelineMutation()

  const [pipelineData, setPipelineData] = useState<ReleasePipelineRequest>({
    name: '',
    project: Number(projectId),
    stages: [blankStage],
  })

  const [isEditingName, setIsEditingName] = useState(
    !pipelineData?.name?.length,
  )

  const handleSuccess = () => {
    history.push(`/project/${projectId}/release-pipelines`)
    toast('Release pipeline created successfully')
  }

  useEffect(() => {
    if (isCreatingPipelineSuccess) {
      return handleSuccess()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCreatingPipelineSuccess])

  useEffect(() => {
    if (isCreatingPipelineError) {
      toast(
        createPipelineError?.data?.detail ?? 'Error creating release pipeline',
        'error',
      )
    }
  }, [isCreatingPipelineError, createPipelineError])

  const handleOnChange = (newStageData: DraftStageType, index: number) => {
    const updatedStages = pipelineData.stages.map((stage, i) =>
      i === index ? newStageData : stage,
    )
    setPipelineData((prev) => ({ ...prev, stages: updatedStages }))
  }

  const validateStage = (stage: DraftStageType) => {
    if (!stage.actions.length) {
      return false
    }

    const segment = stage.actions.find(
      (action) =>
        action.action_type === StageActionType.TOGGLE_FEATURE_FOR_SEGMENT,
    )
    if (segment) {
      return !!segment.action_body.segment_id
    }

    return !!stage.name.length
  }

  const validatePipelineData = () => {
    if (!pipelineData?.name.length) {
      return false
    }

    return pipelineData.stages.every(validateStage)
  }

  const handleSave = () => {
    createReleasePipeline({
      name: pipelineData.name,
      project: Number(projectId),
      stages: pipelineData.stages.map((stage, index) => ({
        ...stage,
        order: index,
      })),
    })
  }

  const handleRemoveStage = (index: number) => {
    const newStages = pipelineData.stages.filter((_, i) => i !== index)
    setPipelineData((prev) => ({ ...prev, stages: newStages }))
  }

  return (
    <div className='app-container container'>
      <Breadcrumb
        items={[
          {
            title: 'Release Pipelines',
            url: `/project/${projectId}/release-pipelines`,
          },
        ]}
        currentPage='New Release Pipeline'
      />

      <PageTitle
        title={
          <Row>
            {!isEditingName && !!pipelineData?.name?.length ? (
              <div>{pipelineData?.name}</div>
            ) : (
              <InputGroup
                className='mb-0'
                value={pipelineData?.name}
                placeholder='Release Pipeline Name'
                onChange={(event: InputEvent) => {
                  setPipelineData({
                    ...pipelineData,
                    name: Utils.safeParseEventValue(event),
                  })
                }}
              />
            )}
            <Button
              theme='text'
              className='ml-2 clickable'
              onClick={() => setIsEditingName(!isEditingName)}
              disabled={!pipelineData?.name?.length}
            >
              {isEditingName ? (
                <Icon width={20} fill='#6837FC' name='close-circle' />
              ) : (
                <Icon width={20} fill='#6837FC' name='edit' />
              )}
            </Button>
          </Row>
        }
        cta={
          <Button
            disabled={!validatePipelineData() || isCreatingPipeline}
            onClick={() => handleSave()}
          >
            Save Release Pipeline
          </Button>
        }
      />
      <div className='px-2 pb-4 overflow-auto'>
        <Row className='no-wrap'>
          {pipelineData.stages.map((stageData, index) => (
            <Row key={index}>
              <Row className='align-items-start no-wrap'>
                <CreatePipelineStage
                  stageData={stageData}
                  onChange={(stageData: DraftStageType) =>
                    handleOnChange(stageData, index)
                  }
                  projectId={projectId}
                  showRemoveButton={index > 0}
                  onRemove={() => handleRemoveStage(index)}
                />
                <div className='flex-1'>
                  <StageArrow
                    showAddStageButton={
                      index === pipelineData.stages.length - 1
                    }
                    onAddStage={() =>
                      setPipelineData((prev) => ({
                        ...prev,
                        stages: prev.stages.concat([blankStage]),
                      }))
                    }
                  />
                  {index === pipelineData.stages.length - 1 && (
                    <div className='m-auto p-2 border-1 rounded border-primary '>
                      <Icon width={30} name='checkmark-circle' fill='#27AB95' />
                      Launched
                    </div>
                  )}
                </div>
              </Row>
            </Row>
          ))}
        </Row>
      </div>
    </div>
  )
}

export default CreateReleasePipeline
