import { useState } from 'react'
import PipelineStage from './PipelineStage'
import { StageData } from './PipelineStage'
import StageLine from './StageLine'
import Breadcrumb from 'components/Breadcrumb'
import { Button } from 'components/base/forms/Button'
import PageTitle from 'components/PageTitle'
import InputGroup from 'components/base/forms/InputGroup'
import Utils from 'common/utils/utils'

type PipelineData = {
  name: string
  stages: StageData[]
}

type CreateReleasePipelineType = {
  projectId: string
}

export default function CreateReleasePipeline({
  projectId,
}: CreateReleasePipelineType) {
  const [pipelineData, setPipelineData] = useState<PipelineData>({
    stages: [
      {
        name: '',
      },
    ],
  })

  const [pipelineName, setPipelineName] = useState('')

  const handleOnChange = (stageData: StageData, index: number) => {
    const newStageData = pipelineData.stages.map((stage, i) =>
      i === index ? stageData : stage,
    )
    setPipelineData({ ...pipelineData, stages: newStageData })
  }

  const validatePipelineData = () => {
    const hasName = pipelineData.stages.every((stage) => stage.name !== '')
    const hasSegments = pipelineData.stages.every((stage) => !!stage.segment)
    return hasName && hasSegments
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
          <InputGroup
            className='mb-0'
            value={''}
            onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
              console.log(event.target.value)
            }}
          />
        }
        cta={
          <Button disabled={!validatePipelineData()} onClick={() => {}}>
            Save Release Pipeline
          </Button>
        }
      />
      <div className='px-2 pb-4 overflow-auto'>
        <Row className='no-wrap'>
          {pipelineData.stages.map((stageData, index) => (
            <Row key={index}>
              <Row className='align-items-start no-wrap'>
                <PipelineStage
                  stageData={stageData}
                  onChange={(stageData) => handleOnChange(stageData, index)}
                  projectId={projectId}
                />
                <div className='flex-1'>
                  <StageLine
                    showAddStageButton={
                      index === pipelineData.stages.length - 1
                    }
                    onAddStage={() =>
                      setPipelineData((prev) => ({
                        ...prev,
                        stages: [...prev.stages, { name: '' }],
                      }))
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
