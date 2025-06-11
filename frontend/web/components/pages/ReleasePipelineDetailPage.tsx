import ReleasePipelineDetail from 'components/release-pipelines/ReleasePipelineDetail'

type ReleasePipelineDetailPageType = {
  match: {
    params: {
      projectId: string
      id: string
    }
  }
}

export default function ReleasePipelineDetailPage({
  match,
}: ReleasePipelineDetailPageType) {
  const { projectId } = match.params
  return <ReleasePipelineDetail projectId={projectId} id={match.params.id} />
}
