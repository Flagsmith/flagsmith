import Breadcrumb from 'components/Breadcrumb'

import PageTitle from 'components/PageTitle'

import {
  useGetPipelineStagesQuery,
  useGetReleasePipelineQuery,
} from 'common/services/useReleasePipelines'
import { withRouter, RouteComponentProps } from 'react-router'
import { useGetEnvironmentsQuery } from 'common/services/useEnvironment'
import Icon from 'components/Icon'
import StageCard from './StageCard'
import StageInfo from './StageInfo'

type ReleasePipelineDetailType = {
  projectId: string
  id: string
} & RouteComponentProps

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

function ReleasePipelineDetail({ id, projectId }: ReleasePipelineDetailType) {
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

  const { data: stagesData, isLoading: isLoadingStages } =
    useGetPipelineStagesQuery(
      {
        page: 1,
        page_size: 100,
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
        currentPage={id}
      />
      {children}
    </div>
  )

  if (isLoadingPipeline || isLoadingStages || isLoadingEnvironments) {
    return (
      <HeaderWrapper>
        <div className='text-center'>
          <Loader />
        </div>
      </HeaderWrapper>
    )
  }

  return (
    <HeaderWrapper>
      <PageTitle title={pipelineData?.name ?? ''} />
      {stagesData?.results?.length === 0 && (
        <Row>
          <span>This release pipeline has no stages.</span>
        </Row>
      )}
      <div className='px-2 pb-4 overflow-auto'>
        <Row className='no-wrap align-items-start'>
          {stagesData?.results?.map((stageData) => (
            <StageInfo
              key={stageData?.id}
              stageData={stageData}
              environmentsData={environmentsData?.results}
            />
          ))}
          {!!stagesData?.results?.length && <LaunchedCard />}
        </Row>
      </div>
    </HeaderWrapper>
  )
}

export default withRouter(ReleasePipelineDetail)
