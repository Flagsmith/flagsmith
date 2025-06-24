import { useDeleteReleasePipelineMutation } from 'common/services/useReleasePipelines'
import { PagedResponse, ReleasePipeline } from 'common/types/responses'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import DropdownMenu from 'components/base/DropdownMenu'
import PanelSearch from 'components/PanelSearch'

const NoReleasePipelines = ({ projectId }: { projectId: string }) => {
  const history = useHistory()

  return (
    <div style={{ marginTop: '8rem' }} className='text-center'>
      <div className='mb-3'>
        <Icon name='flash' width={36} fill='#6837FC' />
      </div>
      <p>
        Create release pipelines to automate and standardize your release
        process throughout your organization.
      </p>
      <Row className='align-items-center justify-content-center gap-3'>
        <Button
          onClick={() =>
            history.push(`/project/${projectId}/release-pipelines/create`)
          }
        >
          Create Release Pipeline
        </Button>
        <Button theme='outline'>Learn more</Button>
      </Row>
    </div>
  )
}

type ReleasePipelinesListProps = {
  data: PagedResponse<ReleasePipeline> | undefined
  isLoading: boolean
  projectId: string
  page: number
  pageSize: number
  onPageChange: (page: number) => void
}

const ReleasePipelinesList = ({
  data,
  isLoading,
  onPageChange,
  page,
  pageSize,
  projectId,
}: ReleasePipelinesListProps) => {
  const [deleteReleasePipeline] = useDeleteReleasePipelineMutation()
  const history = useHistory()
  const pipelinesList = data?.results

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (!pipelinesList?.length) {
    return <NoReleasePipelines projectId={projectId} />
  }

  return (
    <PanelSearch
      id='release-pipelines-list'
      isLoading={isLoading}
      items={pipelinesList}
      className='no-pad'
      title=' '
      filterRow={(item, search) => {
        return item.name.toLowerCase().includes(search.toLowerCase())
      }}
      paging={{
        ...(data || {}),
        currentPage: page,
        pageSize,
      }}
      nextPage={() => onPageChange(page + 1)}
      prevPage={() => onPageChange(page - 1)}
      goToPage={(page: number) => onPageChange(page)}
      renderRow={({
        features_count,
        id,
        name,
        stages_count,
      }: ReleasePipeline) => {
        return (
          <Row key={id} className='list-item'>
            <Row
              className='clickable flex-grow-1 p-3'
              onClick={() => {
                history.push(`/project/${projectId}/release-pipelines/${id}`)
              }}
            >
              <span className='fw-bold'>{name}</span>
            </Row>
            <Row className='gap-5 p-3'>
              <div className='text-center'>
                <div className='fw-bold'>{stages_count ?? 0}</div>
                <div>Stages</div>
              </div>
              <div className='text-center'>
                <div className='fw-bold'>{features_count ?? 0}</div>
                <div>Flags</div>
              </div>
              <DropdownMenu
                items={[
                  {
                    icon: 'trash-2',
                    label: 'Remove Release Pipeline',
                    onClick: () => {
                      deleteReleasePipeline({
                        pipelineId: id,
                        projectId: Number(projectId),
                      })
                    },
                  },
                ]}
              />
            </Row>
          </Row>
        )
      }}
    />
  )
}

export type { ReleasePipelinesListProps }
export default ReleasePipelinesList
