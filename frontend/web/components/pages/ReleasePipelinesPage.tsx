import PageTitle from 'components/PageTitle'
import {
  useDeleteReleasePipelineMutation,
  useGetReleasePipelinesQuery,
} from 'common/services/useReleasePipelines'
import { Button } from 'components/base/forms/Button'
import { RouterChildContext } from 'react-router'
import ConfigProvider from 'common/providers/ConfigProvider'
import { ReleasePipeline } from 'common/types/responses'
import Card from 'components/Card'
import DropdownMenu from 'components/base/DropdownMenu'

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
  data: ReleasePipeline[] | undefined
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
  const [deleteReleasePipeline] = useDeleteReleasePipelineMutation()

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (!data?.length) {
    return <NoReleasePipelines router={router} projectId={projectId} />
  }

  return (
    <>
      {data?.map((pipeline) => (
        <Card
          contentClassName='bg-light200 bg-white'
          className='rounded position-relative border-1 px-2'
          key={pipeline.id}
        >
          <Row className='align-items-center justify-content-between'>
            <span className='fw-bold'>{pipeline.name}</span>
            <Row className=' gap-3'>
              <div className='text-center'>
                <div className='fw-bold'>{pipeline.stages_count ?? 0}</div>
                <div>Stages</div>
              </div>
              <div className='text-center'>
                <div className='fw-bold'>{pipeline.flags_count ?? 0}</div>
                <div>Flags</div>
              </div>
              <DropdownMenu
                items={[
                  {
                    icon: 'trash-2',
                    label: 'Remove Release Pipeline',
                    onClick: () =>
                      deleteReleasePipeline({
                        pipelineId: pipeline.id,
                        projectId: Number(projectId),
                      }),
                  },
                ]}
              />
            </Row>
          </Row>
        </Card>
      ))}
    </>
  )
}

const ReleasePipelinesPage = ({ match, router }: ReleasePipelinesPageType) => {
  const { projectId } = match.params
  const { data, isLoading } = useGetReleasePipelinesQuery({
    projectId: Number(projectId),
  })
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
        data={data?.results}
        isLoading={isLoading}
        projectId={projectId}
        router={router}
      />
    </div>
  )
}

export default ConfigProvider(ReleasePipelinesPage)
