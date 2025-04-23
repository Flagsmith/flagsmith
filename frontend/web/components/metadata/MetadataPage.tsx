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

const metadataWidth = [200, 150, 150, 90]
type MetadataPageType = {
  organisationId: string
  projectId: string
}

type MergeMetadata = {
  content_type_fields: MetadataModelField[]
  id: number
  name: string
  type: string
  description: string
  organisation: number
}

const MetadataPage: FC<MetadataPageType> = ({ organisationId, projectId }) => {
  const { data: metadataFieldList } = useGetMetadataFieldListQuery({
    organisation: organisationId,
  })

  const { data: MetadataModelFieldList } = useGetMetadataModelFieldListQuery({
    organisation_id: organisationId,
  })

  const [deleteMetadata] = useDeleteMetadataFieldMutation()

  const mergeMetadata = useMemo(() => {
    if (metadataFieldList && MetadataModelFieldList) {
      return metadataFieldList.results.map((item1) => {
        const matchingItems2 = MetadataModelFieldList.results.filter(
          (item2) => item2.field === item1.id,
        )
        return {
          ...item1,
          content_type_fields: matchingItems2,
        }
      })?.sort((a, b) => a.id - b.id)
    }
    return null
  }, [metadataFieldList, MetadataModelFieldList])

  const metadataCreatedToast = () => {
    toast('Custom Field Created')
    closeModal()
  }
  const createMetadataField = () => {
    openModal(
      `Create Custom Field`,
      <CreateMetadataField
        onComplete={metadataCreatedToast}
        organisationId={organisationId}
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

  return (
    <PlanBasedBanner className='mt-4' feature={'METADATA'} theme={'page'}>
      <Row space className='mb-2'>
        <Row>
          <h5>Custom Fields</h5>
        </Row>
        <Button className='mt-2' onClick={() => createMetadataField()}>
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
          header={
            <Row className='table-header'>
              <Flex className='table-column px-3'>Name</Flex>
              <div className='table-column' style={{ width: metadataWidth[3] }}>
                Remove
              </div>
            </Row>
          }
          renderRow={(metadata) => (
            <Row
              space
              className='list-item clickable cursor-pointer'
              key={metadata.id}
              onClick={() => {
                editMetadata(`${metadata.id}`, metadata.content_type_fields)
              }}
            >
              <Flex className='table-column px-3'>
                <div className='font-weight-medium mb-1'>{metadata.name}</div>
                <ContentTypesValues
                  contentTypes={metadata.content_type_fields}
                  organisationId={organisationId}
                />
              </Flex>
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
            </Row>
          )}
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
