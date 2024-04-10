import React, { FC, useEffect, useState } from 'react'
import Button from 'components/base/forms/Button'
import PanelSearch from 'components/PanelSearch'
import Icon from 'components/Icon'
import Panel from 'components/base/grid/Panel'
import CreateMetadata from 'components/modals/CreateMetadata'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import Utils from 'common/utils/utils'
import { ContentType, MetadataModelField } from 'common/types/responses'
import {
  useGetMetadataListQuery,
  useDeleteMetadataMutation,
} from 'common/services/useMetadata'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'

import { IonIcon } from '@ionic/react'
import { informationCircle } from 'ionicons/icons'

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
  const [mergeMetadata, setMergeMetadata] = useState<MergeMetadata[]>([])
  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: `${organisationId}`,
  })

  const { data: metadataList } = useGetMetadataListQuery({
    organisation: organisationId,
  })

  const { data: MetadataModelFieldList } = useGetMetadataModelFieldListQuery({
    organisation_id: organisationId,
  })

  const [deleteMetadata] = useDeleteMetadataMutation()

  let featureContentType: ContentType,
    segmentContentType: ContentType,
    environmentContentType: ContentType

  if (supportedContentTypes) {
    featureContentType = Utils.getContentType(
      supportedContentTypes,
      'model',
      'feature',
    )
    segmentContentType = Utils.getContentType(
      supportedContentTypes,
      'model',
      'segment',
    )
    environmentContentType = Utils.getContentType(
      supportedContentTypes,
      'model',
      'environment',
    )
  }

  useEffect(() => {
    if (metadataList && MetadataModelFieldList) {
      const mergeMetadataResult = metadataList?.results.map((item1) => {
        const matchingItems2 = MetadataModelFieldList?.results.filter(
          (item2) => item2.field === item1.id,
        )
        return {
          ...item1,
          content_type_fields: matchingItems2,
        }
      })

      setMergeMetadata(mergeMetadataResult)
    }
  }, [metadataList, MetadataModelFieldList])

  const metadataCreatedToast = () => {
    toast('Metadata created')
    closeModal()
  }
  const createMetadata = () => {
    openModal(
      `Create Metadata`,
      <CreateMetadata
        onComplete={metadataCreatedToast}
        organisationId={organisationId}
        isEdit={false}
      />,
      'side-modal create-feature-modal',
    )
  }

  const editMetadata = (id: string, contentTypeList: MetadataModelField[]) => {
    openModal(
      `Edit Metadata`,
      <CreateMetadata
        isEdit={true}
        metadataModelFieldList={contentTypeList}
        id={id}
        onComplete={() => {
          toast('Metadata Updated')
        }}
        projectId={projectId}
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
          {' metadata?'}
        </div>
      ),
      destructive: true,
      onYes: () => deleteMetadata({ id }),
      title: 'Delete Metadata',
      yesText: 'Confirm',
    })
  }

  return (
    <div>
      <Row space className='mt-4'>
        <Tooltip
          title={
            <Row>
              <h5>Metadata</h5>
              <div>
                <IonIcon icon={informationCircle} />
              </div>
            </Row>
          }
        >
          {'Create or Update the Metadata Project'}
        </Tooltip>
        <Button onClick={() => createMetadata()}>{'Create Metadata'}</Button>
      </Row>
      <p className='fs-small lh-sm'>
        Add metadata to your chore entities{' '}
        <Button
          theme='text'
          target='_blank'
          href='https://docs.flagsmith.com/system-administration/metadata/'
          className='fw-normal'
        >
          Learn more.
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
          renderRow={(metadata: MergeMetadata) => (
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
            <Panel className='no-pad' title={'Metadata'}>
              <div className='search-list'>
                <Row className='list-item p-3 text-muted'>
                  You currently have no metadata configured.
                </Row>
              </div>
            </Panel>
          }
        />
      </FormGroup>
    </div>
  )
}

export default MetadataPage
