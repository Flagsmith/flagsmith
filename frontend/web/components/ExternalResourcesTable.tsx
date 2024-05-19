import React, { FC, useEffect } from 'react'
import PanelSearch from './PanelSearch'
import Button from './base/forms/Button'
import Icon from './Icon'
import {
  useGetExternalResourcesQuery,
  useDeleteExternalResourceMutation,
} from 'common/services/useExternalResource'
import { ExternalResource } from 'common/types/responses'
import Constants from 'common/constants'
import Tooltip from './Tooltip'

export type ExternalResourcesTableType = {
  featureId: string
  projectId: string
  organisationId: string
  repoName: string
  repoOwner: string
  setSelectedResources: (r: ExternalResource[]) => void
}

type ExternalResourceRowType = {
  featureId: string
  projectId: string
  externalResource: ExternalResource
}

const ExternalResourceRow: FC<ExternalResourceRowType> = ({
  externalResource,
  featureId,
  projectId,
}) => {
  const [deleteExternalResource, { isSuccess: isDeleted }] =
    useDeleteExternalResourceMutation()

  useEffect(() => {
    if (isDeleted) {
      toast('External resources was deleted')
    }
  }, [isDeleted])
  return (
    <Row className='list-item' key={externalResource?.id}>
      <div className='table-column text-left' style={{ width: '100px' }}>
        <div className='font-weight-medium mb-1'>
          {Constants.resourceTypes[externalResource?.type].label}
        </div>
      </div>
      <Flex className='table-column'>
        <Row className='font-weight-medium'>
          <Button
            theme='text'
            href={`${externalResource?.url}`}
            target='_blank'
            className='fw-normal ml-1 mt-1'
          >
            <Tooltip
              title={
                <Row>
                  {`${
                    externalResource?.metadata?.name
                  } (#${externalResource?.url.replace(/\D/g, '')})`}{' '}
                  <div className='ml-1 mb-1'>
                    <Icon name='open-external-link' width={14} fill='#6837fc' />
                  </div>
                </Row>
              }
              place='right'
            >
              {`${externalResource?.url}`}
            </Tooltip>
          </Button>
        </Row>
      </Flex>
      <div className='table-column text-center' style={{ width: '80px' }}>
        <div className='font-weight-medium mb-1'>
          {externalResource?.metadata?.status}
        </div>
      </div>
      <div className='table-column text-center' style={{ width: '80px' }}>
        <Button
          onClick={() => {
            deleteExternalResource({
              external_resource_id: `${externalResource?.id}`,
              feature_id: featureId,
              project_id: projectId,
            })
          }}
          className='btn btn-with-icon'
        >
          <Icon name='trash-2' width={20} fill='#656D7B' />
        </Button>
      </div>
    </Row>
  )
}

const ExternalResourcesTable: FC<ExternalResourcesTableType> = ({
  featureId,
  projectId,
  setSelectedResources,
}) => {
  const { data } = useGetExternalResourcesQuery({
    feature_id: featureId,
    project_id: projectId,
  })

  useEffect(() => {
    if (data?.results) {
      setSelectedResources(data.results)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data])

  return (
    <>
      <PanelSearch
        className='no-pad overflow-visible'
        items={data?.results}
        header={
          <Row className='table-header'>
            <div className='table-column' style={{ width: '240px' }}>
              Type
            </div>
            <Flex className='table-column px-3'>Name</Flex>
            <div
              className='table-column text-center'
              style={{ width: '240px' }}
            >
              Status
            </div>
          </Row>
        }
        renderRow={(v: ExternalResource) => (
          <ExternalResourceRow
            key={v.id}
            featureId={featureId}
            projectId={projectId}
            externalResource={v}
          />
        )}
        renderNoResults={
          <FormGroup className='text-center'>
            You have no external resouces linked for this feature.
          </FormGroup>
        }
      />
    </>
  )
}

export default ExternalResourcesTable
