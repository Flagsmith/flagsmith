import React, { FC, useMemo } from 'react'
import Button from 'components/base/forms/Button'
import PanelSearch from 'components/PanelSearch'
import Icon from 'components/Icon'
import Panel from 'components/base/grid/Panel'
import CreateMetadataField from 'components/modals/CreateMetadataField'
import ContentTypesValues from './ContentTypesValues'
import { MetadataModelField } from 'common/types/responses'
import {
  useGetMetadataFieldListQuery,
  useDeleteMetadataFieldMutation,
} from 'common/services/useMetadataField'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'
import PlanBasedBanner from 'components/PlanBasedAccess'
import RedirectCreateCustomFields from './RedirectCreateCustomFields'

const metadataWidth = [200, 150, 150, 90]
type MetadataPageType = {
  organisationId: string
  projectId?: string
}

type MergeMetadata = {
  content_type_fields: MetadataModelField[]
  id: number
  name: string
  type: string
  description: string
  organisation: number
  project: number | null
}

const MetadataPage: FC<MetadataPageType> = ({ organisationId, projectId }) => {
  const { data: metadataFieldList } = useGetMetadataFieldListQuery({
    organisation: organisationId,
    ...(projectId ? { project: parseInt(projectId) } : {}),
  })

  const { data: MetadataModelFieldList } = useGetMetadataModelFieldListQuery({
    organisation_id: organisationId,
  })

  const [deleteMetadata] = useDeleteMetadataFieldMutation()

  const mergeMetadata = useMemo(() => {
    if (metadataFieldList && MetadataModelFieldList) {
      return metadataFieldList.results
        .map((item1) => {
          const matchingItems2 = MetadataModelFieldList.results.filter(
            (item2) => item2.field === item1.id,
          )
          return {
            ...item1,
            content_type_fields: matchingItems2,
          }
        })
        ?.sort((a, b) => a.id - b.id)
    }
    return null
  }, [metadataFieldList, MetadataModelFieldList])

  const orgFields = useMemo(() => {
    if (!projectId || !mergeMetadata) return null
    return mergeMetadata.filter((item) => item.project === null)
  }, [mergeMetadata, projectId])

  const projectFields = useMemo(() => {
    if (!projectId || !mergeMetadata) return null
    return mergeMetadata.filter((item) => item.project !== null)
  }, [mergeMetadata, projectId])

  const metadataCreatedToast = () => {
    toast('Custom Field Created')
    closeModal()
  }
  const openCreateMetadataField = () => {
    openModal(
      `Create Custom Field`,
      <CreateMetadataField
        onComplete={metadataCreatedToast}
        organisationId={organisationId}
        projectId={projectId}
        isEdit={false}
      />,
      'side-modal create-feature-modal',
    )
  }

  const editMetadata = (id: string, contentTypeList: MetadataModelField[]) => {
    openModal(
      `Edit Custom Field`,
      <CreateMetadataField
        isEdit={true}
        metadataModelFieldList={contentTypeList}
        id={id}
        onComplete={() => {
          toast('Custom Field Updated')
        }}
        organisationId={organisationId}
        projectId={projectId}
      />,
      'side-modal create-feature-modal',
    )
  }

  const _deleteMetadata = (id: string, name: string) => {
    openConfirm({
      body: (
        <div>
          {'Are you sure you want to delete '}
          <strong>{name}</strong>
          {' custom field?'}
        </div>
      ),
      destructive: true,
      onYes: () =>
        deleteMetadata({ id }).then(() => toast('Custom Field Deleted')),
      title: 'Delete Custom Field',
      yesText: 'Confirm',
    })
  }

  const renderFieldRow = (
    metadata: MergeMetadata,
    { readOnly }: { readOnly: boolean },
  ) => (
    <Row
      space
      className={`list-item${readOnly ? '' : ' clickable cursor-pointer'}`}
      key={metadata.id}
      onClick={
        readOnly
          ? undefined
          : () => {
              editMetadata(`${metadata.id}`, metadata.content_type_fields)
            }
      }
    >
      <Flex className='table-column px-3'>
        <div className='d-flex align-items-center gap-x-2 mb-1'>
          <span className='font-weight-medium'>{metadata.name}</span>
          {readOnly && <span className='chip chip--xs'>Inherited</span>}
        </div>
        <ContentTypesValues
          contentTypes={metadata.content_type_fields}
          organisationId={organisationId}
        />
      </Flex>
      {!readOnly && (
        <div className='table-column' style={{ width: '86px' }}>
          <Button
            id='delete-invite'
            type='button'
            onClick={(e) => {
              e.stopPropagation()
              _deleteMetadata(`${metadata.id}`, metadata.name)
            }}
            className='btn btn-with-icon'
          >
            <Icon name='trash-2' width={20} fill='#656D7B' />
          </Button>
        </div>
      )}
    </Row>
  )

  const renderTableHeader = ({ showRemove }: { showRemove: boolean }) => (
    <Row className='table-header'>
      <Flex className='table-column px-3'>Name</Flex>
      {showRemove && (
        <div className='table-column' style={{ width: metadataWidth[3] }}>
          Remove
        </div>
      )}
    </Row>
  )

  if (projectId) {
    return (
      <PlanBasedBanner className='mt-4' feature={'METADATA'} theme={'page'}>
        <Row space className='mb-2'>
          <Row>
            <h5>Custom Fields</h5>
          </Row>
          <Button className='mt-2' onClick={() => openCreateMetadataField()}>
            {'Create Custom Field'}
          </Button>
        </Row>
        <p className='fs-small lh-sm'>
          Manage project-level custom fields and view inherited organisation
          fields.{' '}
          <Button
            theme='text'
            target='_blank'
            href='https://docs.flagsmith.com/advanced-use/custom-fields/'
            className='fw-normal'
          >
            Learn more
          </Button>
        </p>

        <FormGroup className='mt-4'>
          <h6 className='mb-2'>Organisation Fields</h6>
          <PanelSearch
            id='org-fields-list'
            items={orgFields}
            header={renderTableHeader({ showRemove: false })}
            renderRow={(metadata: MergeMetadata) =>
              renderFieldRow(metadata, { readOnly: true })
            }
            renderNoResults={
              <div className='search-list'>
                <Row className='list-item p-3 text-muted'>
                  <RedirectCreateCustomFields
                    organisationId={parseInt(organisationId)}
                    organisationOnly
                  />
                </Row>
              </div>
            }
          />
        </FormGroup>

        <FormGroup className='mt-4'>
          <h6 className='mb-2'>Project Fields</h6>
          <PanelSearch
            id='project-fields-list'
            items={projectFields}
            header={renderTableHeader({ showRemove: true })}
            renderRow={(metadata: MergeMetadata) =>
              renderFieldRow(metadata, { readOnly: false })
            }
            renderNoResults={
              <div className='search-list'>
                <Row className='list-item p-3 text-muted'>
                  No project-level custom fields configured.
                </Row>
              </div>
            }
          />
        </FormGroup>
      </PlanBasedBanner>
    )
  }

  return (
    <PlanBasedBanner className='mt-4' feature={'METADATA'} theme={'page'}>
      <Row space className='mb-2'>
        <Row>
          <h5>Custom Fields</h5>
        </Row>
        <Button className='mt-2' onClick={() => openCreateMetadataField()}>
          {'Create Custom Field'}
        </Button>
      </Row>
      <p className='fs-small lh-sm'>
        Add custom fields to features, segments, environments and projects.{' '}
        <Button
          theme='text'
          target='_blank'
          href='https://docs.flagsmith.com/advanced-use/custom-fields/'
          className='fw-normal'
        >
          Learn more
        </Button>
      </p>
      <FormGroup className='mt-4'>
        <PanelSearch
          id='webhook-list'
          items={mergeMetadata}
          header={renderTableHeader({ showRemove: true })}
          renderRow={(metadata: MergeMetadata) =>
            renderFieldRow(metadata, { readOnly: false })
          }
          renderNoResults={
            <Panel className='no-pad' title={'Custom Fields'}>
              <div className='search-list'>
                <Row className='list-item p-3 text-muted'>
                  You currently have no custom fields configured.
                </Row>
              </div>
            </Panel>
          }
        />
      </FormGroup>
    </PlanBasedBanner>
  )
}

export default MetadataPage
