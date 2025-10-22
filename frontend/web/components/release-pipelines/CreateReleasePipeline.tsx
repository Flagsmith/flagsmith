import { useCallback, useEffect, useRef, useState } from 'react'
import CreatePipelineStage from './CreatePipelineStage'
import Breadcrumb from 'components/Breadcrumb'
import { Button } from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import Icon from 'components/Icon'
import {
  useCreateReleasePipelineMutation,
  useGetReleasePipelineQuery,
  usePublishReleasePipelineMutation,
  useUpdateReleasePipelineMutation,
} from 'common/services/useReleasePipelines'
import { useHistory, useParams } from 'react-router-dom'
import StageArrow from './StageArrow'
import {
  PipelineStageRequest,
  ReleasePipelineRequest,
} from 'common/types/requests'
import { useRouteContext } from 'components/providers/RouteContext'
import PlanBasedAccess from 'components/PlanBasedAccess'
import { NEW_PIPELINE_STAGE, NEW_PIPELINE_STAGE_ACTION_TYPE } from './constants'
import { StageActionBody, StageActionType } from 'common/types/responses'
import ButtonDropdown from 'components/base/forms/ButtonDropdown'

type CreateReleasePipelineParams = {
  id?: string
}

function CreateReleasePipeline() {
  const history = useHistory()
  const { projectId } = useRouteContext()

  const { id: pipelineId } = useParams<CreateReleasePipelineParams>()
  const { data: existingPipeline, isLoading: isLoadingExistingPipeline } =
    useGetReleasePipelineQuery(
      {
        pipelineId: Number(pipelineId),
        projectId: Number(projectId),
      },
      {
        skip: !pipelineId,
      },
    )

  const [
    createReleasePipeline,
    {
      error: createPipelineError,
      isError: isCreatingPipelineError,
      isLoading: isCreatingPipeline,
      isSuccess: isCreatingPipelineSuccess,
    },
  ] = useCreateReleasePipelineMutation()

  const [
    updateReleasePipeline,
    {
      error: updatePipelineError,
      isError: isUpdatingPipelineError,
      isLoading: isUpdatingPipeline,
      isSuccess: isUpdatingPipelineSuccess,
    },
  ] = useUpdateReleasePipelineMutation()

  const [publishReleasePipeline, { isLoading: isPublishingPipeline }] =
    usePublishReleasePipelineMutation()

  const [pipelineData, setPipelineData] = useState<ReleasePipelineRequest>({
    name: '',
    project: Number(projectId),
    stages: [NEW_PIPELINE_STAGE],
  })

  const [isEditingName, setIsEditingName] = useState(
    !pipelineData?.name?.length,
  )
  const skipNextCreateToast = useRef(false)

  const handleSuccess = useCallback(
    (updated = false, skipToast = false) => {
      history.push(`/project/${projectId}/release-pipelines`)
      if (!skipToast) {
        toast(
          `Release pipeline ${updated ? 'updated' : 'created'} successfully`,
        )
      }
    },
    [history, projectId],
  )

  useEffect(() => {
    if (skipNextCreateToast.current) {
      return
    }

    if (isCreatingPipelineSuccess) {
      return handleSuccess()
    }

    if (isUpdatingPipelineSuccess) {
      return handleSuccess(true)
    }
  }, [isCreatingPipelineSuccess, isUpdatingPipelineSuccess, handleSuccess])

  useEffect(() => {
    if (skipNextCreateToast.current) {
      return
    }

    if (isCreatingPipelineError) {
      toast('Error creating release pipeline', 'danger')
    }

    if (isUpdatingPipelineError) {
      toast(
        updatePipelineError?.data?.detail ?? 'Error updating release pipeline',
        'danger',
      )
    }
  }, [
    isCreatingPipelineError,
    createPipelineError,
    isUpdatingPipelineError,
    updatePipelineError,
  ])

  useEffect(() => {
    if (existingPipeline) {
      setPipelineData(existingPipeline)
    }
  }, [existingPipeline])

  const handleOnChange = (
    newStageData: PipelineStageRequest,
    index: number,
  ) => {
    const updatedStages = pipelineData.stages.map((stage, i) =>
      i === index ? newStageData : stage,
    )
    setPipelineData((prev) => ({ ...prev, stages: updatedStages }))
  }

  const checkFieldRange = (field: number, min: number, max: number) => {
    if (!field) {
      return false
    }

    return field >= min && field <= max
  }

  const validatePhasedRolloutAction = (actionBody: StageActionBody) => {
    if (
      !actionBody?.increase_by ||
      !actionBody?.initial_split ||
      !actionBody?.increase_every
    ) {
      return false
    }

    if (
      !checkFieldRange(actionBody.increase_by, 0, 100) ||
      !checkFieldRange(actionBody.initial_split, 0, 100)
    ) {
      return false
    }

    if (actionBody.increase_by + actionBody.initial_split > 100) {
      return false
    }

    return true
  }

  const validateStage = (stage: PipelineStageRequest) => {
    if (!stage.actions.length) {
      return false
    }

    // action in creation state
    if (
      stage.actions.some(
        (action) => action.action_type === NEW_PIPELINE_STAGE_ACTION_TYPE,
      )
    ) {
      return false
    }

    const segments = stage.actions.filter(
      (action) =>
        action.action_type === StageActionType.TOGGLE_FEATURE_FOR_SEGMENT,
    )
    const isSegmentsValid = segments.every(
      (segment) => !!segment.action_body.segment_id,
    )

    if (segments.length && !isSegmentsValid) {
      return false
    }

    const phasedRolloutActions = stage.actions.filter(
      (action) => action.action_type === StageActionType.PHASED_ROLLOUT,
    )
    const isPhasedRolloutValid = phasedRolloutActions.every((action) =>
      validatePhasedRolloutAction(action.action_body),
    )

    if (phasedRolloutActions.length && !isPhasedRolloutValid) {
      return false
    }

    return !!stage.name.length
  }

  const validatePipelineData = () => {
    if (!pipelineData?.name.length) {
      return false
    }

    return pipelineData.stages.every(validateStage)
  }

  const handleSubmit = async (id?: number) => {
    if (id) {
      return await updateReleasePipeline({
        id,
        name: pipelineData.name,
        project: Number(projectId),
        stages: pipelineData.stages.map((stage, index) => ({
          ...stage,
          order: index,
        })),
      }).unwrap()
    }

    return await createReleasePipeline({
      name: pipelineData.name,
      project: Number(projectId),
      stages: pipelineData.stages.map((stage, index) => ({
        ...stage,
        order: index,
      })),
    }).unwrap()
  }

  const handleSubmitAndPublish = async (id?: number) => {
    try {
      skipNextCreateToast.current = true
      const response = await handleSubmit(id)
      await publishReleasePipeline({
        pipelineId: response.id,
        projectId: Number(projectId),
      }).unwrap()
      toast('Release pipeline published successfully')
      handleSuccess(true, true)
      skipNextCreateToast.current = false
    } catch (error) {
      toast(
        `Error ${id ? 'updating' : 'creating'} and publishing pipeline`,
        'danger',
      )
    }
  }

  const handleRemoveStage = (index: number) => {
    const newStages = pipelineData.stages.filter((_, i) => i !== index)
    setPipelineData((prev) => ({ ...prev, stages: newStages }))
  }

  const isSaveDisabled =
    !validatePipelineData() ||
    isCreatingPipeline ||
    isUpdatingPipeline ||
    isPublishingPipeline

  const saveButtonText = existingPipeline?.id ? 'Update' : 'Save'

  if (isLoadingExistingPipeline) {
    return (
      <div className='app-container container'>
        <div className='text-center'>
          <Loader />
        </div>
      </div>
    )
  }

  return (
    <div className='app-container container pb-0'>
      <PlanBasedAccess feature={'RELEASE_PIPELINES'} theme={'page'}>
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
            <ButtonDropdown
              type='button'
              data-test='create-update-release-pipeline-btn'
              disabled={isSaveDisabled}
              dropdownItems={[
                {
                  label: `${saveButtonText} & Publish`,
                  onClick: () => handleSubmitAndPublish(existingPipeline?.id),
                },
              ]}
              onClick={() => handleSubmit(existingPipeline?.id)}
            >
              {saveButtonText} as Draft
            </ButtonDropdown>
          }
        />
        <div className='release-pipeline-container px-2 overflow-auto'>
          <Row className='no-wrap'>
            {pipelineData.stages.map((stageData, index) => (
              <Row key={index}>
                <Row className='align-items-start no-wrap'>
                  <CreatePipelineStage
                    stageData={stageData}
                    onChange={(stageData: PipelineStageRequest) =>
                      handleOnChange(stageData, index)
                    }
                    projectId={Number(projectId)}
                    showRemoveButton={pipelineData.stages.length > 1}
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
                          stages: prev.stages.concat([NEW_PIPELINE_STAGE]),
                        }))
                      }
                    />
                    {index === pipelineData.stages.length - 1 && (
                      <div className='m-auto p-2 border-1 rounded border-primary '>
                        <Icon
                          width={30}
                          name='checkmark-circle'
                          fill='#27AB95'
                        />
                        Launched
                      </div>
                    )}
                  </div>
                </Row>
              </Row>
            ))}
          </Row>
        </div>
      </PlanBasedAccess>
    </div>
  )
}

export default CreateReleasePipeline
