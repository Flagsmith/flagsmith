import { useEffect, useState } from 'react'
import CreatePipelineStage, { DraftStageType } from './CreatePipelineStage'
import Breadcrumb from 'components/Breadcrumb'
import { Button } from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import {
  PipelineStatus,
  ReleasePipeline,
  StageActionType,
  StageTriggerType,
} from 'common/types/responses'
import Icon from 'components/Icon'
import {
  useCreatePipelineStagesMutation,
  useCreateReleasePipelineMutation,
} from 'common/services/useReleasePipelines'
import { withRouter, RouteComponentProps } from 'react-router'
import StageArrow from './StageArrow'

type CreateReleasePipelineType = {
  projectId: string
} & RouteComponentProps

type DraftPipelineType = Omit<
  ReleasePipeline,
  'id' | 'stages_count' | 'flags_count'
>

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

function CreateReleasePipeline({
  history,
  projectId,
}: CreateReleasePipelineType) {
  const [
    createReleasePipeline,
    {
      error: createPipelineError,
      isError: isCreatingPipelineError,
      isLoading: isCreatingPipeline,
      isSuccess: isCreatingPipelineSuccess,
    },
  ] = useCreateReleasePipelineMutation()

  const [createStages] = useCreatePipelineStagesMutation()

  const [pipelineData, setPipelineData] = useState<DraftPipelineType>({
    name: '',
    project: Number(projectId),
    status: PipelineStatus.DRAFT,
  })

  const [stages, setStages] = useState<DraftStageType[]>([blankStage])

  const [isEditingName, setIsEditingName] = useState(
    !pipelineData?.name?.length,
  )

  const [isStagesCreationSuccess, setStagesCreationSuccess] =
    useState<boolean>(false)

  const handleSuccess = () => {
    history.push(`/project/${projectId}/release-pipelines`)
    toast('Release pipeline created successfully')
  }

  const isPipelineSuccess = isCreatingPipelineSuccess && !stages.length
  const isStagesSuccess =
    isCreatingPipelineSuccess && stages.length && isStagesCreationSuccess

  useEffect(() => {
    if (isPipelineSuccess || isStagesSuccess) {
      return handleSuccess()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isPipelineSuccess, isStagesSuccess])

  useEffect(() => {
    if (isCreatingPipelineError) {
      toast(
        createPipelineError?.data?.detail ?? 'Error creating release pipeline',
        'error',
      )
    }
  }, [isCreatingPipelineError, createPipelineError])

  const handleOnChange = (newStageData: DraftStageType, index: number) => {
    const updatedStages = stages.map((stage, i) =>
      i === index ? newStageData : stage,
    )
    setStages(updatedStages)
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

    return stages.every(validateStage)
  }

  const handleSave = async () => {
    const response = await createReleasePipeline({
      name: pipelineData.name,
      projectId: Number(projectId),
      status: PipelineStatus.DRAFT,
    })

    if (!stages.length) {
      return
    }

    setStagesCreationSuccess(false)
    if (response && 'data' in response && response.data.id) {
      const pipelineId = response.data.id
      const stagesCreationPromises = stages.map((stage, index) => {
        return createStages({
          ...stage,
          order: index,
          pipeline: pipelineId,
          project: Number(projectId),
        })
      })

      setStagesCreationSuccess(false)
      try {
        await Promise.all(stagesCreationPromises)
        setStagesCreationSuccess(true)
      } catch (error) {
        toast('Error creating release stages', 'error')
      }
    }
  }

  const handleRemoveStage = (index: number) => {
    const newStages = stages.filter((_, i) => i !== index)
    setStages(newStages)
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
          {stages?.map((stageData, index) => (
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
                    showAddStageButton={index === stages.length - 1}
                    onAddStage={() =>
                      setStages((prev) => prev.concat(blankStage))
                    }
                  />
                  {index === stages.length - 1 && (
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

export default withRouter(CreateReleasePipeline)
