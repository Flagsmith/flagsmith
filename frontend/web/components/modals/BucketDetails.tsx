import React, { FC, useState } from 'react'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import PanelSearch from 'components/PanelSearch'
import { useGetBucketQuery } from 'common/services/useBucket'
import {
  useGetProjectFlagsQuery,
  useUpdateProjectFlagMutation,
} from 'common/services/useProjectFlag'
import { useHasPermission } from 'common/providers/Permission'
import { Bucket, ProjectFlag } from 'common/types/responses'
import useDebouncedSearch from 'common/useDebouncedSearch'
import Utils from 'common/utils/utils'

type BucketDetailsType = {
  projectId: number
  bucketId: number
  onEditBucket: () => void
}

const BucketDetails: FC<BucketDetailsType> = ({
  bucketId,
  onEditBucket,
  projectId,
}) => {
  const { search, searchInput, setSearchInput } = useDebouncedSearch('')
  const [isAddingFeatures, setIsAddingFeatures] = useState(false)

  const { data: bucket, isLoading: bucketLoading } = useGetBucketQuery({
    id: bucketId,
    projectId,
  })

  const { data: allFeaturesData, isLoading: allFeaturesLoading } =
    useGetProjectFlagsQuery(
      { project: projectId },
      { skip: !isAddingFeatures },
    )

  const { data: bucketFeaturesData, isLoading: bucketFeaturesLoading } =
    useGetProjectFlagsQuery({
      project: projectId,
    })

  const [updateFeature] = useUpdateProjectFlagMutation()

  const { permission: canManage } = useHasPermission({
    id: projectId,
    level: 'project',
    permission: 'MANAGE_BUCKETS',
  })

  const allFeatures = allFeaturesData?.results || []
  const bucketFeatures =
    bucketFeaturesData?.results?.filter((f) => f.bucket?.id === bucketId) || []
  const availableFeatures = allFeatures.filter(
    (f) => !f.bucket || f.bucket.id === bucketId,
  )

  const removeFeatureFromBucket = (feature: ProjectFlag) => {
    openConfirm({
      body: `Are you sure you want to remove "${feature.name}" from this bucket?`,
      onYes: () => {
        updateFeature({
          body: { bucket_id: null },
          feature_id: feature.id,
          project_id: projectId,
        }).then((res) => {
          // @ts-ignore
          if (res.error) {
            toast('Failed to remove feature from bucket', 'danger')
          } else {
            toast('Feature removed from bucket')
          }
        })
      },
      title: 'Remove Feature from Bucket',
      yesText: 'Remove',
    })
  }

  const addFeatureToBucket = (feature: ProjectFlag) => {
    updateFeature({
      body: { bucket_id: bucketId },
      feature_id: feature.id,
      project_id: projectId,
    }).then((res) => {
      // @ts-ignore
      if (res.error) {
        toast('Failed to add feature to bucket', 'danger')
      } else {
        toast('Feature added to bucket')
      }
    })
  }

  const filteredFeatures = isAddingFeatures
    ? availableFeatures?.filter((f) =>
        f.name.toLowerCase().includes(search.toLowerCase()),
      )
    : bucketFeatures.filter((f) =>
        f.name.toLowerCase().includes(search.toLowerCase()),
      )

  return (
    <div>
      <div className='modal-body px-4'>
        <div className='d-flex justify-content-between align-items-start mb-4'>
          <div>
            <h4 className='mb-2'>{bucket?.name}</h4>
            {bucket?.description && (
              <p className='text-muted mb-0'>{bucket.description}</p>
            )}
            <div className='text-muted mt-2'>
              {bucket?.feature_count || 0} feature
              {bucket?.feature_count !== 1 ? 's' : ''}
            </div>
          </div>
          {canManage && (
            <Button theme='text' onClick={onEditBucket}>
              <Icon name='edit' width={16} /> Edit
            </Button>
          )}
        </div>

        <div className='mb-3'>
          {canManage && !isAddingFeatures && (
            <Button
              onClick={() => setIsAddingFeatures(true)}
              theme='secondary'
              className='mb-3'
            >
              <Icon name='plus' width={16} /> Add Features
            </Button>
          )}
          {isAddingFeatures && (
            <div className='alert alert-info d-flex justify-content-between align-items-center'>
              <span>Select features to add to this bucket</span>
              <Button theme='text' onClick={() => setIsAddingFeatures(false)}>
                Done
              </Button>
            </div>
          )}
        </div>

        <PanelSearch
          id='bucket-features-list'
          title={isAddingFeatures ? 'Available Features' : 'Features in Bucket'}
          isLoading={
            bucketLoading ||
            bucketFeaturesLoading ||
            (isAddingFeatures && allFeaturesLoading)
          }
          items={filteredFeatures}
          renderRow={(feature: ProjectFlag, index: number) => (
            <Row
              space
              className='list-item list-item-sm clickable'
              key={feature.id}
              data-test={`feature-item-${index}`}
            >
              <div className='flex-row flex flex-1 px-3'>
                <div>
                  <div className='font-weight-medium'>{feature.name}</div>
                  {feature.description && (
                    <div className='list-item-subtitle mt-1'>
                      {feature.description}
                    </div>
                  )}
                </div>
              </div>
              {canManage && (
                <div className='px-3'>
                  {isAddingFeatures ? (
                    <Button
                      theme='secondary'
                      size='small'
                      onClick={() => addFeatureToBucket(feature)}
                      disabled={feature.bucket?.id === bucketId}
                    >
                      {feature.bucket?.id === bucketId ? 'In Bucket' : 'Add'}
                    </Button>
                  ) : (
                    <Button
                      className='btn btn-with-icon'
                      type='button'
                      onClick={() => removeFeatureFromBucket(feature)}
                    >
                      <Icon name='trash-2' width={20} fill='#656D7B' />
                    </Button>
                  )}
                </div>
              )}
            </Row>
          )}
          renderNoResults={
            <div className='text-center p-4'>
              {isAddingFeatures
                ? 'No available features found'
                : 'No features in this bucket'}
              {search && (
                <span>
                  {' '}
                  for <strong>"{search}"</strong>
                </span>
              )}
            </div>
          }
          search={searchInput}
          onChange={(e) => setSearchInput(Utils.safeParseEventValue(e))}
          filterRow={() => true}
        />

        <div className='text-right mt-4'>
          <Button onClick={closeModal}>Close</Button>
        </div>
      </div>
    </div>
  )
}

export default BucketDetails

module.exports = BucketDetails
