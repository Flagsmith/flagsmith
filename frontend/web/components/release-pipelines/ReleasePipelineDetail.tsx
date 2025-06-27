import Breadcrumb from 'components/Breadcrumb'

import PageTitle from 'components/PageTitle'

import { useGetReleasePipelineQuery } from 'common/services/useReleasePipelines'
import { useParams } from 'react-router-dom'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import Icon from 'components/Icon'
import StageCard from './StageCard'
import StageInfo from './StageInfo'
import { PipelineStage } from 'common/types/responses'
import { Environment } from 'common/types/responses'
import { useRouteContext } from 'components/providers/RouteContext'

const LaunchedCard = () => {
  // TODO: Add the logic to get the features that completed this pipeline in the last 30 days
  return (
    <StageCard>
      <Row className=' gap-2 align-items-center mb-2'>
        <Icon name='checkmark-circle' width={30} fill='#27AB95' />
        <h5 className='mb-0'>Launched</h5>
      </Row>
      <p className='text-muted'>
        Features that completed this pipeline in the last 30 days
      </p>
      <h6>Features (1)</h6>
      <p className='text-muted'>
        Finished 3h ago by <b>John Doe</b>
      </p>
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
        projectId,
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

  const getEnvironmentName = (
    environmentsData: Environment[] | undefined,
    stageData: PipelineStage,
  ) => {
    return (
      environmentsData?.find(
        (environment) => environment.id === stageData?.environment,
      )?.name ?? ''
    )
  }

  return (
    <HeaderWrapper>
      <PageTitle title={pipelineData?.name ?? ''} />
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
              environmentName={getEnvironmentName(
                environmentsData?.results,
                stageData,
              )}
              projectId={Number(projectId)}
            />
          ))}
          {!!pipelineData?.stages?.length && <LaunchedCard />}
        </Row>
      </div>
    </HeaderWrapper>
  )
}

export default ReleasePipelineDetail
