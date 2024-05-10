import React, { FC, useEffect, useState } from 'react'
import PanelSearch from './PanelSearch'
import Button from './base/forms/Button'
import Icon from './Icon'
import {
  useCreateExternalResourceMutation,
  useGetExternalResourcesQuery,
  useDeleteExternalResourceMutation,
} from 'common/services/useExternalResource'
import { ExternalResource } from 'common/types/responses'
import Constants from 'common/constants'
import Tooltip from './Tooltip'
import MyIssuesSelect from './MyIssuesSelect'
import MyPullRequestsSelect from './MyPullRequestsSelect'

export type ExternalResourcesTableType = {
  featureId: string
  projectId: string
  organisationId: string
  repoName: string
  repoOwner: string
}

type ExternalResourceRowType = {
  featureId: string
  projectId: string
  externalResource: ExternalResource
}

type AddExternalResourceRowType = ExternalResourcesTableType & {
  linkedExternalResources?: ExternalResource[]
}

type GitHubStatusType = {
  value: number
  label: string
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
      <Flex className='table-column'>
        <Row className='font-weight-medium'>
          {Constants.resourceTypes[externalResource?.type].label}
          <Button
            theme='text'
            href={`${externalResource?.url}`}
            target='_blank'
            className='fw-normal ml-1 mt-1'
          >
            <Tooltip
              title={
                <Row>
                  {`#${externalResource?.url.replace(/\D/g, '')}`}{' '}
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

const AddExternalResourceRow: FC<AddExternalResourceRowType> = ({
  featureId,
  linkedExternalResources,
  organisationId,
  projectId,
  repoName,
  repoOwner,
}) => {
  const [externalResourceType, setExternalResourceType] = useState<string>('')
  const [featureExternalResource, setFeatureExternalResource] =
    useState<string>('')

  const [createExternalResource] = useCreateExternalResourceMutation()
  const githubTypes = Object.values(Constants.resourceTypes).filter(
    (v) => v.type === 'GITHUB',
  )
  return (
    <Row className='list-item'>
      <Flex className='table-column' style={{ maxWidth: '170px' }}>
        <Select
          size='select-md'
          placeholder={'Select Type'}
          onChange={(v: GitHubStatusType) => setExternalResourceType(v.label)}
          options={githubTypes.map((e) => {
            return { label: e.label, value: e.id }
          })}
        />
      </Flex>
      <Flex className='table-column px-3'>
        <Flex className='ml-4'>
          {externalResourceType ==
          Constants.resourceTypes.GITHUB_ISSUE.label ? (
            <MyIssuesSelect
              orgId={organisationId}
              onChange={(v) => setFeatureExternalResource(v)}
              repoOwner={repoOwner}
              repoName={repoName}
              linkedExternalResources={linkedExternalResources!}
            />
          ) : externalResourceType ==
            Constants.resourceTypes.GITHUB_PR.label ? (
            <MyPullRequestsSelect
              orgId={organisationId}
              onChange={(v) => setFeatureExternalResource(v)}
              repoOwner={repoOwner}
              repoName={repoName}
              linkedExternalResources={linkedExternalResources!}
            />
          ) : (
            <></>
          )}
        </Flex>
      </Flex>
      <div className='table-column text-center' style={{ width: '80px' }}>
        <Button
          className='text-right btn-with-icon'
          theme='primary'
          disabled={!externalResourceType || !featureExternalResource}
          onClick={() => {
            createExternalResource({
              body: {
                feature: parseInt(featureId),
                metadata: { status: 'open' },
                type: externalResourceType.toUpperCase().replace(/\s+/g, '_'),
                url: featureExternalResource,
              },
              feature_id: featureId,
              project_id: projectId,
            }).then(() => {
              toast('External Resource Added')
              setExternalResourceType('')
              setFeatureExternalResource('')
            })
          }}
        >
          <Icon name='plus' width={20} fill='#656D7B' />
        </Button>
      </div>
    </Row>
  )
}

const ExternalResourcesTable: FC<ExternalResourcesTableType> = ({
  featureId,
  organisationId,
  projectId,
  repoName,
  repoOwner,
}) => {
  const { data } = useGetExternalResourcesQuery({
    feature_id: featureId,
    project_id: projectId,
  })
  const renderRowWithPermanentRow = (v: ExternalResource, index: number) => {
    if (index === (data?.results.length || 0) - 1) {
      return (
        <>
          <ExternalResourceRow
            key={v.id}
            featureId={featureId}
            projectId={projectId}
            externalResource={v}
          />
          <AddExternalResourceRow
            key='add-external-key'
            featureId={featureId}
            projectId={projectId}
            organisationId={organisationId}
            repoName={repoName}
            repoOwner={repoOwner}
            linkedExternalResources={data?.results}
          />
        </>
      )
    } else if (v.type !== 'permanent') {
      return (
        <ExternalResourceRow
          key={v.id}
          featureId={featureId}
          projectId={projectId}
          externalResource={v}
        />
      )
    } else if (v.type === 'permanent') {
      return (
        <AddExternalResourceRow
          key='add-external-key'
          featureId={featureId}
          projectId={projectId}
          organisationId={organisationId}
          repoName={repoName}
          repoOwner={repoOwner}
        />
      )
    }
  }

  return (
    <>
      <PanelSearch
        className='no-pad overflow-visible'
        title='Linked Issues and Pull Requests'
        items={
          data?.results.length
            ? data?.results
            : [{ id: 'add-external-key', type: 'permanent' }]
        }
        header={
          <Row className='table-header'>
            <Flex className='table-column px-3'>Type</Flex>
            <div
              className='table-column text-center'
              style={{ width: '240px' }}
            >
              Status
            </div>
          </Row>
        }
        renderRow={renderRowWithPermanentRow}
      />
    </>
  )
}

export default ExternalResourcesTable
