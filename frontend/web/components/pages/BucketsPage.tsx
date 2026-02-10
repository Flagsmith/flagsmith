import React, { FC, useState } from 'react'
import { useRouteMatch } from 'react-router-dom'
import { useHasPermission } from 'common/providers/Permission'
import { deleteBucket, useGetBucketsQuery } from 'common/services/useBucket'
import useDebouncedSearch from 'common/useDebouncedSearch'
import PanelSearch, { SortOption } from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import PageTitle from 'components/PageTitle'
import { Bucket } from 'common/types/responses'
import { getStore } from 'common/store'
import { useRouteContext } from 'components/providers/RouteContext'
import CreateBucketModal from 'components/modals/CreateBucket'
import BucketDetailsModal from 'components/modals/BucketDetails'
import Utils from 'common/utils/utils'
import { SortOrder } from 'common/types/requests'

interface RouteParams {
  projectId: string
}

const sortOptions: SortOption[] = [
  { default: true, label: 'Created Date', order: 'asc', value: 'created_date' },
  { label: 'Name', order: 'asc', value: 'name' },
]

export const removeBucket = (
  id: number,
  name: string,
  projectId: number,
  onYes?: () => void,
) => {
  openConfirm({
    body: (
      <div>
        <div className='mb-2'>
          {'Are you sure you want to delete '}
          <strong>{name}</strong>?
        </div>
        Deleting this bucket will not delete the features in it, but they will
        no longer be associated with this bucket.
      </div>
    ),
    destructive: true,
    onYes: () => {
      onYes?.()
      deleteBucket(getStore(), {
        id,
        projectId,
      }).then((res) => {
        // @ts-ignore
        if (res.error) {
          toast('Bucket could not be removed', 'danger')
        } else {
          toast('Bucket successfully removed')
        }
      })
    },
    title: 'Delete Bucket',
    yesText: 'Confirm',
  })
}

const BucketsPage: FC = () => {
  const { projectId } = useRouteContext()
  const match = useRouteMatch<RouteParams>()
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState<string>('created_date')
  const [sortOrder, setSortOrder] = useState<SortOrder>('asc')

  const { search, searchInput, setSearchInput } = useDebouncedSearch('')

  const { data: buckets, isLoading } = useGetBucketsQuery({
    page,
    page_size: 10,
    projectId: parseInt(projectId),
    search: search || undefined,
    sort_direction: sortOrder === 'asc' ? 'ASC' : 'DESC',
    sort_field: sortBy as 'created_date' | 'name',
  })

  const { permission: canView } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'VIEW_BUCKET',
  })

  const { permission: canManage } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_BUCKETS',
  })

  const openCreateBucket = () => {
    openModal(
      'Create Bucket',
      <CreateBucketModal projectId={parseInt(projectId)} />,
      'side-modal',
    )
  }

  const openBucketDetails = (bucket: Bucket) => {
    openModal(
      'Bucket Details',
      <BucketDetailsModal
        projectId={parseInt(projectId)}
        bucketId={bucket.id}
        onEditBucket={() => {
          closeModal()
          openEditBucket(bucket)
        }}
      />,
      'side-modal',
    )
  }

  const openEditBucket = (bucket: Bucket) => {
    openModal(
      'Edit Bucket',
      <CreateBucketModal projectId={parseInt(projectId)} bucket={bucket} />,
      'side-modal',
    )
  }

  const handleSortChange = (args: {
    sortBy: string | null
    sortOrder: SortOrder | null
  }) => {
    if (args.sortBy && args.sortOrder) {
      setSortBy(args.sortBy)
      setSortOrder(args.sortOrder)
      setPage(1) // Reset to first page on sort
    }
  }

  return (
    <div className='app-container container'>
      <PageTitle
        cta={
          <>
            {canManage ? (
              <FormGroup className='float-right'>
                <Button
                  className='float-right'
                  data-test='show-create-bucket-btn'
                  id='show-create-bucket-btn'
                  onClick={openCreateBucket}
                >
                  Create Bucket
                </Button>
              </FormGroup>
            ) : (
              <Tooltip
                title={
                  <Button
                    disabled
                    data-test='show-create-bucket-btn'
                    id='show-create-bucket-btn'
                  >
                    Create Bucket
                  </Button>
                }
                place='right'
              >
                You need the MANAGE_BUCKETS permission to create buckets
              </Tooltip>
            )}
          </>
        }
        title={'Buckets'}
      >
        Organize your features into logical groups using buckets. This helps
        you manage and navigate large numbers of features more effectively.{' '}
        <Button
          theme='text'
          target='_blank'
          href='https://docs.flagsmith.com'
          className='fw-normal'
        >
          Learn more.
        </Button>
      </PageTitle>
      <div>
        <FormGroup>
          <PanelSearch
            renderSearchWithNoResults
            header={
              canView && (
                <Row className='table-header'>
                  <Flex className='table-column px-3'>Name</Flex>
                  <Flex className='table-column px-3'>Description</Flex>
                  <div
                    className='table-column text-center'
                    style={{ width: 120 }}
                  >
                    Features
                  </div>
                  <div className='table-column' style={{ width: 80 }}></div>
                </Row>
              )
            }
            id='buckets-list'
            title='Buckets'
            className='no-pad'
            isLoading={isLoading}
            items={buckets?.results}
            paging={buckets}
            sorting={sortOptions}
            onSortChange={handleSortChange}
            nextPage={() => setPage(page + 1)}
            prevPage={() => setPage(page - 1)}
            goToPage={(newPage: number) => setPage(newPage)}
            renderRow={(bucket: Bucket, index: number) =>
              canView ? (
                <Row
                  space
                  className='list-item clickable list-item-sm'
                  key={bucket.id}
                  data-test={`bucket-item-${index}`}
                  onClick={() => openBucketDetails(bucket)}
                >
                  <Flex className='table-column px-3'>
                    <div>
                      <div className='font-weight-medium'>{bucket.name}</div>
                    </div>
                  </Flex>
                  <Flex className='table-column px-3'>
                    <div className='list-item-subtitle'>
                      {bucket.description || '-'}
                    </div>
                  </Flex>
                  <div
                    className='table-column text-center'
                    style={{ width: 120 }}
                  >
                    <span className='badge badge-pill badge-primary'>
                      {bucket.feature_count}
                    </span>
                  </div>
                  <div className='table-column' style={{ width: 80 }}>
                    {canManage && (
                      <div className='d-flex gap-2'>
                        <Button
                          className='btn btn-with-icon'
                          type='button'
                          onClick={(e) => {
                            e.stopPropagation()
                            openEditBucket(bucket)
                          }}
                        >
                          <Icon name='edit' width={20} fill='#656D7B' />
                        </Button>
                        <Button
                          className='btn btn-with-icon'
                          type='button'
                          onClick={(e) => {
                            e.stopPropagation()
                            removeBucket(
                              bucket.id,
                              bucket.name,
                              parseInt(projectId),
                            )
                          }}
                        >
                          <Icon name='trash-2' width={20} fill='#656D7B' />
                        </Button>
                      </div>
                    )}
                  </div>
                </Row>
              ) : (
                <Row
                  space
                  className='list-item'
                  key={bucket.id}
                  data-test={`bucket-item-${index}`}
                >
                  {bucket.name}
                </Row>
              )
            }
            renderNoResults={
              !canView ? (
                <div
                  className='list-item p-3 text-center'
                  data-test={`missing-view-bucket`}
                >
                  To view buckets you need the <i>VIEW_BUCKET</i> permission
                  for this project.
                  <br />
                  Please contact a project administrator.
                </div>
              ) : (
                <Row className='list-item p-3'>
                  <>
                    You have no buckets in this project
                    {search ? (
                      <span>
                        {' '}
                        for <strong>"{search}"</strong>
                      </span>
                    ) : (
                      ''
                    )}
                    .
                  </>
                </Row>
              )
            }
            filterRow={() => true}
            search={searchInput}
            onChange={(e) => {
              setSearchInput(Utils.safeParseEventValue(e))
            }}
          />
        </FormGroup>
      </div>
    </div>
  )
}

export default BucketsPage
