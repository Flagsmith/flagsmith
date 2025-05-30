import CreateReleasePipeline from 'components/release-pipelines/CreateReleasePipeline'

type CreateReleasePipelinePageType = {
  match: {
    params: {
      projectId: string
    }
  }
}

export default function CreateReleasePipelinePage({
  match,
}: CreateReleasePipelinePageType) {
  const { projectId } = match.params
  return <CreateReleasePipeline projectId={projectId} />
}
