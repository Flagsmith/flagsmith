import PageTitle from 'components/PageTitle'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import { Button } from 'components/base/forms/Button'
import { useHistory, useRouteMatch } from 'react-router-dom'
import ConfigProvider from 'common/providers/ConfigProvider'
import ReleasePipelinesList from 'components/release-pipelines/ReleasePipelinesList'
import { useState } from 'react'

interface RouteParams {
  projectId: string
}

const ReleasePipelinesPage = () => {
  const history = useHistory()
  const match = useRouteMatch<RouteParams>()
  const [page, setPage] = useState(1)
  const pageSize = 10
  const { projectId } = match.params
  const { data, isLoading } = useGetReleasePipelinesQuery({
    page,
    page_size: pageSize,
    projectId: Number(projectId),
  })

  const hasReleasePipelines = !!data?.results?.length

  return (
    <div className='app-container container'>
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
        projectId={projectId}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
      />
    </div>
  )
}

export default ConfigProvider(ReleasePipelinesPage)
