import {
  useDeleteReleasePipelineMutation,
  usePublishReleasePipelineMutation,
} from 'common/services/useReleasePipelines'
import { PagedResponse, ReleasePipeline } from 'common/types/responses'
import { useHistory } from 'react-router-dom'
import Button from 'components/base/forms/Button'
import Icon, { IconName } from 'components/Icon'
import DropdownMenu from 'components/base/DropdownMenu'
import PanelSearch from 'components/PanelSearch'
import Tag from 'components/tags/Tag'
import { useEffect } from 'react'

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
  const [
    publishReleasePipeline,
    {
      error: publishReleasePipelineError,
      isError: isPublishingError,
      isLoading: isPublishing,
      isSuccess: isPublishingSuccess,
    },
  ] = usePublishReleasePipelineMutation()
  const pipelinesList = data?.results

  useEffect(() => {
    if (isPublishingSuccess) {
      return toast('Release pipeline published successfully')
    }

    if (isPublishingError) {
      return toast(
        publishReleasePipelineError?.data?.detail ??
          'Something went wrong while publishing the release pipeline',
        'danger',
      )
    }
  }, [isPublishingSuccess, isPublishingError, publishReleasePipelineError])

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
        published_at,
        stages_count,
      }: ReleasePipeline) => {
        const isPublished = !!published_at

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
                <div className='fw-bold'>{features_count ?? 0}</div>
                <div>Features</div>
              </div>
              <DropdownMenu
                items={[
                  {
                    disabled: isDeleting,
                    icon: 'trash-2',
                    label: 'Remove Release Pipeline',
                    onClick: () => {
                      deleteReleasePipeline({
                        pipelineId: id,
                        projectId: Number(projectId),
                      })
                    },
                  },
                  ...(!isPublished
                    ? [
                        {
                          disabled: isPublishing,
                          icon: 'checkmark-circle' as IconName,
                          label: 'Publish Release Pipeline',
                          onClick: () => {
                            publishReleasePipeline({
                              pipelineId: id,
                              projectId: Number(projectId),
                            })
                          },
                        },
                      ]
                    : []),
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
