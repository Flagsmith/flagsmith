import PageTitle from 'components/PageTitle'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import { Button } from 'components/base/forms/Button'
import { RouterChildContext } from 'react-router'
import ConfigProvider from 'common/providers/ConfigProvider'
import ReleasePipelinesList from 'components/release-pipelines/ReleasePipelinesList'
import { useState } from 'react'

type ReleasePipelinesPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const ReleasePipelinesPage = ({ match, router }: ReleasePipelinesPageType) => {
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
                router.history.push(
                  `/project/${projectId}/release-pipelines/create`,
                )
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
        router={router}
        page={page}
        pageSize={pageSize}
        onPageChange={setPage}
      />
    </div>
  )
}

export default ConfigProvider(ReleasePipelinesPage)
