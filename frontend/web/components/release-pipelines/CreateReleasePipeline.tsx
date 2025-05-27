import { useEffect, useState } from 'react'
import PipelineStage, { DraftStageType } from './PipelineStage'
import StageLine from './StageLine'
import Breadcrumb from 'components/Breadcrumb'
import { Button } from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'
import { PipelineStatus, ReleasePipeline } from 'common/types/responses'
import Icon from 'components/Icon'
import { useCreateReleasePipelineMutation } from 'common/services/useReleasePipelines'
import { withRouter, RouteComponentProps } from 'react-router'

type CreateReleasePipelineType = {
  projectId: string
} & RouteComponentProps

type DraftPipelineType = Omit<
  ReleasePipeline,
  'id' | 'stages_count' | 'flags_count'
>

const blankStage: DraftStageType = {
  actions: [],
  environment: 0,
  name: '',
  order: 0,
  triggers: [],
}

function CreateReleasePipeline({
  history,
  projectId,
}: CreateReleasePipelineType) {
  const [
    createReleasePipeline,
    {
      error: createPipelineError,
      isLoading: isCreatingPipeline,
      isSuccess: isCreatingPipelineSuccess,
    },
  ] = useCreateReleasePipelineMutation()

  const [pipelineData, setPipelineData] = useState<DraftPipelineType>({
    name: '',
    project: Number(projectId),
    status: PipelineStatus.DRAFT,
  })

  const [stages, setStages] = useState<DraftStageType[]>([
    {
      actions: [],
      environment: 0,
      name: '',
      order: 0,
      triggers: [],
    },
  ])

  const [isEditingName, setIsEditingName] = useState(
    !pipelineData?.name?.length,
  )

  useEffect(() => {
    if (isCreatingPipelineSuccess) {
      history.push(`/project/${projectId}/release-pipelines`)
    }
  }, [isCreatingPipelineSuccess, createPipelineError, history, projectId])

  const handleOnChange = (stageData: DraftStageType, index: number) => {
    const newStageData = stages.map((stage, i) =>
      i === index ? stageData : stage,
    )
    setStages(newStageData)
  }

  const validatePipelineData = () => {
    return pipelineData?.name !== ''
  }

  const handleSave = () => {
    createReleasePipeline({
      name: pipelineData.name,
      projectId: Number(projectId),
    })
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
        currentPage={'New Release Pipeline'}
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
                <PipelineStage
                  stageData={stageData}
                  onChange={(stageData: DraftStageType) =>
                    handleOnChange(stageData, index)
                  }
                  projectId={projectId}
                />
                <div className='flex-1'>
                  <StageLine
                    showAddStageButton={index === stages.length - 1}
                    onAddStage={() =>
                      setStages((prev) => prev.concat(blankStage))
                    }
                  />
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
