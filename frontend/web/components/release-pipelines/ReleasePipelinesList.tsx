import { useDeleteReleasePipelineMutation } from 'common/services/useReleasePipelines'
import { PagedResponse, ReleasePipeline } from 'common/types/responses'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import Icon, { IconName } from 'components/Icon'
import DropdownMenu from 'components/base/DropdownMenu'
import PanelSearch from 'components/PanelSearch'
import Tag from 'components/tags/Tag'
import { useEffect } from 'react'
import ChangeReleasePipelineStatusModal from './ChangeReleasePipelineStatusModal'
import CloneReleasePipelineModal from './CloneReleasePipelineModal'
import DeleteReleasePipelineModal from './DeleteReleasePipelineModal'

const NoReleasePipelines = ({ projectId }: { projectId: number }) => {
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
        <Button
          theme='outline'
          onClick={() => {
            window.open(
              'https://docs.flagsmith.com/advanced-use/release-pipelines/',
              '_blank',
            )
          }}
        >
          Learn more
        </Button>
      </Row>
    </div>
  )
}

type ReleasePipelinesListProps = {
  data: PagedResponse<ReleasePipeline> | undefined
  isLoading: boolean
  projectId: number
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
  const history = useHistory()
  const [
    deleteReleasePipeline,
    {
      error: deleteReleasePipelineError,
      isError: isDeletingError,
      isLoading: isDeleting,
      isSuccess: isDeletingSuccess,
    },
  ] = useDeleteReleasePipelineMutation()

  const pipelinesList = data?.results

  useEffect(() => {
    if (isDeletingSuccess) {
      return toast('Release pipeline deleted successfully')
    }

    if (isDeletingError) {
      return toast(
        deleteReleasePipelineError?.data?.detail ??
          'Something went wrong while deleting the release pipeline',
        'danger',
      )
    }
  }, [isDeletingSuccess, isDeletingError, deleteReleasePipelineError])

  const openChangeReleasePipelineStatusModal = (
    projectId: number,
    pipelineId: number,
    isPublished: boolean,
  ) => {
    openModal2(
      isPublished ? 'Unpublish Release Pipeline' : 'Publish Release Pipeline',
      <ChangeReleasePipelineStatusModal
        isPublished={isPublished}
        pipelineId={pipelineId}
        projectId={projectId}
      />,
    )
  }

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
        features,
        id,
        name,
        published_at,
        stages_count,
      }: ReleasePipeline) => {
        const isPublished = !!published_at
        const canUnpublish = isPublished && !features?.length
        const canDelete = !features?.length

        const getTooltip = (action: string) => {
          if (isPublished) {
            return `Cannot ${action} a published release pipeline`
          }
          return undefined
        }

        return (
          <Row key={id} className='list-item'>
            <Row
              className='clickable flex-grow-1 p-3'
              onClick={() => {
                history.push(`/project/${projectId}/release-pipelines/${id}`)
              }}
            >
              <span className='fw-bold'>{name}</span>
              <div className='ml-3'>
                <Tag
                  className='chip--xs'
                  tag={{
                    color: isPublished ? '#6837FC' : '#9DA4AE',
                    label: isPublished ? 'Published' : 'Draft',
                  }}
                />
              </div>
            </Row>
            <Row className='gap-5 p-3'>
              <div className='text-center'>
                <div className='fw-bold'>{stages_count ?? 0}</div>
                <div>Stages</div>
              </div>
              <div className='text-center'>
                <div className='fw-bold'>{features?.length ?? 0}</div>
                <div>Features</div>
              </div>
              <DropdownMenu
                items={[
                  {
                    disabled: isPublished,
                    icon: 'edit' as IconName,
                    label: 'Edit',
                    onClick: () => {
                      history.push(
                        `/project/${projectId}/release-pipelines/${id}/edit`,
                      )
                    },
                    tooltip: getTooltip('edit'),
                  },
                  {
                    disabled: isPublished && !canUnpublish,
                    icon: isPublished
                      ? 'minus-circle'
                      : ('checkmark-circle' as IconName),
                    label: isPublished ? 'Unpublish' : 'Publish',
                    onClick: () =>
                      openChangeReleasePipelineStatusModal(
                        projectId,
                        id,
                        isPublished,
                      ),
                    tooltip:
                      isPublished && !canUnpublish
                        ? 'Cannot unpublish a release pipeline with in-flight features'
                        : undefined,
                  },
                  {
                    icon: 'copy' as IconName,
                    label: 'Clone',
                    onClick: () =>
                      openModal2(
                        'Clone Release Pipeline',
                        <CloneReleasePipelineModal
                          pipelineId={id}
                          projectId={projectId}
                        />,
                      ),
                  },
                  {
                    disabled: !canDelete,
                    icon: 'trash-2',
                    label: 'Remove',
                    onClick: () => {
                      openModal2(
                        'Remove Release Pipeline',
                        <DeleteReleasePipelineModal
                          pipelineId={id}
                          projectId={projectId}
                        />,
                      )
                    },
                    tooltip: canDelete
                      ? undefined
                      : 'Cannot remove a release pipeline with in-flight features',
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
