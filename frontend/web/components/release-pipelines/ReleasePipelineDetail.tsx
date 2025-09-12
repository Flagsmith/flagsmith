import Breadcrumb from 'components/Breadcrumb'

import PageTitle from 'components/PageTitle'

import { useGetReleasePipelineQuery } from 'common/services/useReleasePipelines'
import { useParams } from 'react-router-dom'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import Icon from 'components/Icon'
import StageCard from './StageCard'
import StageInfo from './StageInfo'
import { PipelineDetailStage } from 'common/types/responses'
import { Environment } from 'common/types/responses'
import { useRouteContext } from 'components/providers/RouteContext'
import StageFeatureDetail from './StageFeatureDetail'
import Tag from 'components/tags/Tag'

const LaunchedCard = ({
  completedFeatures,
  projectId,
}: {
  completedFeatures: number[]
  projectId: number
}) => {
  return (
    <StageCard>
      <Row className=' gap-2 align-items-center mb-2'>
        <Icon name='checkmark-circle' width={30} fill='#27AB95' />
        <h5 className='mb-0'>Launched</h5>
      </Row>
      <p className='text-muted'>
        Features that completed this pipeline in the last 30 days
      </p>
      <StageFeatureDetail features={completedFeatures} projectId={projectId} />
    </StageCard>
  )
}

function ReleasePipelineDetail() {
  const { id } = useParams<{ projectId: string; id: string }>()
  const { projectId } = useRouteContext()
  const { data: pipelineData, isLoading: isLoadingPipeline } =
    useGetReleasePipelineQuery(
      {
        pipelineId: Number(id),
        projectId: Number(projectId),
      },
      {
        skip: !id || !projectId,
      },
    )

  const { data: environmentsData, isLoading: isLoadingEnvironments } =
    useGetEnvironmentsQuery(
      {
        projectId: projectId?.toString() || '',
      },
      {
        skip: !projectId,
      },
    )

  const HeaderWrapper = ({ children }: { children: React.ReactNode }) => (
    <div className='app-container container'>
      <Breadcrumb
        items={[
          {
            title: 'Release Pipelines',
            url: `/project/${projectId}/release-pipelines`,
          },
        ]}
        currentPage={pipelineData?.name ?? ''}
      />
      {children}
    </div>
  )

  if (isLoadingPipeline || isLoadingEnvironments) {
    return (
      <HeaderWrapper>
        <div className='text-center'>
          <Loader />
        </div>
      </HeaderWrapper>
    )
  }

  const getEnvironmentData = (
    environmentsData: Environment[] | undefined,
    stageData: PipelineDetailStage,
  ) => {
    return environmentsData?.find(
      (environment) => environment.id === stageData?.environment,
    )
  }

  return (
    <HeaderWrapper>
      <PageTitle
        title={
          <div className='d-flex'>
            {pipelineData?.name}
            <div className='ml-3 mt-auto' style={{ marginBottom: '5px' }}>
              <Tag
                className='chip--xs'
                tag={{
                  color: pipelineData?.published_at ? '#6837FC' : '#9DA4AE',
                  label: pipelineData?.published_at ? 'Published' : 'Draft',
                }}
              />
            </div>
          </div>
        }
      />
      {pipelineData?.stages?.length === 0 && (
        <Row>
          <span>This release pipeline has no stages.</span>
        </Row>
      )}
      <div className='px-2 pb-4 overflow-auto'>
        <Row className='no-wrap align-items-start'>
          {pipelineData?.stages?.map((stageData) => (
            <StageInfo
              key={stageData?.id}
              stageData={stageData}
              environmentData={getEnvironmentData(
                environmentsData?.results,
                stageData,
              )}
              projectId={Number(projectId)}
            />
          ))}
          {!!pipelineData?.stages?.length && (
            <LaunchedCard
              completedFeatures={pipelineData?.completed_features}
              projectId={Number(projectId)}
            />
          )}
        </Row>
      </div>
    </HeaderWrapper>
  )
}

export default ReleasePipelineDetail
