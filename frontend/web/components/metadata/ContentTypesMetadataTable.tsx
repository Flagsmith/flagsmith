import React, { FC } from 'react'

import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import Switch from 'components/Switch'
import Icon from 'components/Icon'

import { useDeleteMetadataModelFieldMutation } from 'common/services/useMetadataModelField'
type selectedContentType = { label: string; value: string }

type ContentTypesMetadataTableType = {
  organisationId: string
  selectedContentTypes: selectedContentType[]
  onDelete: (removed: selectedContentType) => void
  isEdit: boolean
}

const ContentTypesMetadataTable: FC<ContentTypesMetadataTableType> = ({
  isEdit,
  onDelete,
  organisationId,
  selectedContentTypes,
}) => {
  const deleteRequied = (removed: selectedContentType) => {
    if (isEdit) {
      onDelete?.(removed)
    } else {
      deleteMetadataModelField({
        id: '',
        organisation_id: organisationId,
      })
    }
  }
  const isRequired = () => {
    if (isEdit) {
      console.log('DEBUG:')
    }
  }
  const [deleteMetadataModelField] = useDeleteMetadataModelFieldMutation()
  return (
    <PanelSearch
      id='content-types-list'
      className='mt-4 no-pad'
      header={
        <Row className='table-header'>
          <Flex className='table-column px-3' style={{ 'minWidth': '310px' }}>
            Entity
          </Flex>
          <div className='table-column text-center' style={{ width: '80px' }}>
            Requeried
          </div>
          <div className='table-column text-center' style={{ width: '80px' }}>
            Remove
          </div>
        </Row>
      }
      items={selectedContentTypes}
      renderRow={(s: selectedContentType) => (
        <Row className='list-item' key={s.value}>
          <Flex className='table-column px-3'>{s.label}</Flex>
          <div className='table-column text-center' style={{ width: '80px' }}>
            <Switch
              // checked={environmentEnabled}
              // onChange={() => {
              //   setEnvironmentEnabled(!environmentEnabled)
              //   handleMetadataModelField(
              //     environmentContentType,
              //     !environmentEnabled,
              //   )
              // }}
              className='ml-0'
            />
          </div>
          <div className='table-column text-center' style={{ width: '80px' }}>
            <Button
              onClick={() => {
                if (isEdit) {
                  deleteRequied(s)
                } else {
                  deleteMetadataModelField({
                    id: '',
                    organisation_id: organisationId,
                  })
                }
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

export default ContentTypesMetadataTable
