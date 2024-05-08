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
}

const ExternalResourcesTable: FC<ExternalResourcesTableType> = ({
  featureId,
  projectId,
}) => {
  const { data } = useGetExternalResourcesQuery({
    feature_id: featureId,
    project_id: projectId,
  })

  const [deleteExternalResource, { isSuccess: isDeleted }] =
    useDeleteExternalResourceMutation()

  useEffect(() => {
    if (isDeleted) {
      toast('External resources was deleted')
    }
  }, [isDeleted])

  return (
    <PanelSearch
      className='no-pad'
      title='Linked Issues and Pull Requests'
      items={data?.results}
      header={
        <Row className='table-header'>
          <Flex className='table-column px-3'>Type</Flex>
          <div className='table-column text-center' style={{ width: '80px' }}>
            Status
          </div>
          <div className='table-column text-center' style={{ width: '80px' }}>
            Remove
          </div>
        </Row>
      }
      renderRow={(v: ExternalResource) => (
        <Row className='list-item' key={v.id}>
          <Flex className='table-column px-3'>
            <div className='font-weight-medium mb-1'>
              {v.type === 'GITHUB_ISSUE'
                ? Constants.githubType.githubIssue
                : Constants.githubType.githubPR}
            </div>
          </Flex>
          <Flex className='table-column px-3'>
            <Button
              theme='text'
              href={`${v.url}`}
              target='_blank'
              className='fw-normal'
            >
              <Tooltip
                title={
                  <Row>
                    {`#${v.url.replace(/\D/g, '')}`}{' '}
                    <div className='ml-1 mb-1'>
                      <Icon
                        name='open-external-link'
                        width={14}
                        fill='#6837fc'
                      />
                    </div>
                  </Row>
                }
                place='right'
              >
                {`${v.url}`}
              </Tooltip>
            </Button>
          </Flex>
          <div className='table-column text-center' style={{ width: '80px' }}>
            <div className='font-weight-medium mb-1'>{v.metadata?.status}</div>
          </div>
          <div className='table-column text-center' style={{ width: '80px' }}>
            <Button
              onClick={() => {
                deleteExternalResource({
                  external_resource_id: `${v.id}`,
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
      )}
    />
  )
}

export default ExternalResourcesTable
