import PageTitle from 'components/PageTitle'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import { Button } from 'components/base/forms/Button'
import { useHistory } from 'react-router-dom'
import ConfigProvider from 'common/providers/ConfigProvider'
import ReleasePipelinesList from 'components/release-pipelines/ReleasePipelinesList'
import { useState } from 'react'
import PlanBasedAccess from 'components/PlanBasedAccess'
import { useRouteContext } from 'components/providers/RouteContext'

const ReleasePipelinesPage = () => {
  const history = useHistory()

  const { projectId } = useRouteContext()
  const [page, setPage] = useState(1)
  const pageSize = 10
  const { data, isLoading } = useGetReleasePipelinesQuery({
    order_by: 'created_at',
    page,
    page_size: pageSize,
    projectId: Number(projectId),
  })

  const hasReleasePipelines = !!data?.results?.length

  return (
    <div className='app-container container'>
      <PlanBasedAccess feature={'RELEASE_PIPELINES'} theme={'page'}>
        <PageTitle
          title={'Release Pipelines'}
          cta={
            hasReleasePipelines && (
              <Button
                onClick={() =>
                  history.push(`/project/${projectId}/release-pipelines/create`)
                }
              >
                Create Release Pipeline
              </Button>
            )
          }
        >
          {hasReleasePipelines &&
            'Define the stages your flags should go from development to launched. Learn more.'}
        </PageTitle>
        <ReleasePipelinesList
          data={data}
          isLoading={isLoading}
          projectId={projectId ?? NaN}
          page={page}
          pageSize={pageSize}
          onPageChange={setPage}
        />
      </PlanBasedAccess>
    </div>
  )
}

export default ConfigProvider(ReleasePipelinesPage)
