import PageTitle from 'components/PageTitle'
import { useGetReleasePipelinesQuery } from 'common/services/useReleasePipelines'
import { Button } from 'components/base/forms/Button'
import { RouterChildContext } from 'react-router'
import ConfigProvider from 'common/providers/ConfigProvider'

type ReleasePipelinesPageType = {
  router: RouterChildContext['router']
  match: {
    params: {
      environmentId: string
      projectId: string
    }
  }
}

const NoReleasePipelines = ({
  projectId,
  router,
}: {
  router: RouterChildContext['router']
  projectId: string
}) => {
  return (
    <div className='mt-5 text-center'>
      <p>
        Create release pipelines to automate and standardize your release
        process throughout your organization.
      </p>
      <Row className='align-items-center justify-content-center gap-3'>
        <Button
          onClick={() =>
            router.history.push(
              `/project/${projectId}/release-pipelines/create`,
            )
          }
        >
          Create release pipeline
        </Button>
        <Button theme='outline'>Learn more</Button>
      </Row>
    </div>
  )
}

type ReleasePipelinesPageContentProps = {
  data: any // TODO: type ReleasePipeline[]
  isLoading: boolean
  projectId: string
  router: RouterChildContext['router']
}

const ReleasePipelinesPageContent = ({
  data,
  isLoading,
  projectId,
  router,
}: ReleasePipelinesPageContentProps) => {
  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (!data?.results?.length) {
    return <NoReleasePipelines router={router} projectId={projectId} />
  }

  return <div>Release Pipelines List</div>
}

const ReleasePipelinesPage = ({ match, router }: ReleasePipelinesPageType) => {
  const { projectId } = match.params
  const { data, isLoading } = useGetReleasePipelinesQuery({})
  const hasReleasePipelines = !!data?.results?.length

  return (
    <div className='app-container container'>
      <PageTitle
        title={'Release Pipelines'}
        cta={hasReleasePipelines && <Button>Create release pipeline</Button>}
      >
        {hasReleasePipelines &&
          'Define the stages your flags should go from development to launched. Learn more.'}
      </PageTitle>
      <ReleasePipelinesPageContent
        data={data}
        isLoading={isLoading}
        projectId={projectId}
        router={router}
      />
    </div>
  )
}

export default ConfigProvider(ReleasePipelinesPage)
