import React, { FC, useState } from 'react'

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
  changeMetadataRequired: (value: string, isRequired: boolean) => void
}

type ContentTypesMetadataRowBase = Omit<
  ContentTypesMetadataTableType,
  'selectedContentTypes'
>

type ContentTypesMetadataRowType = ContentTypesMetadataRowBase & {
  item: selectedContentType
}

const ContentTypesMetadataRow: FC<ContentTypesMetadataRowType> = ({
  changeMetadataRequired,
  isEdit,
  item,
  onDelete,
  organisationId,
}) => {
  const [deleteMetadataModelField] = useDeleteMetadataModelFieldMutation()
  const [isMetadataRequired, setIsMetadataRequired] = useState<boolean>(false)

  const deleteRequied = (removed: selectedContentType) => {
    if (!isEdit) {
      onDelete?.(removed)
    } else {
      deleteMetadataModelField({
        id: '',
        organisation_id: organisationId,
      })
    }
  }
  const isRequired = (value: string, isRequired: boolean) => {
    if (!isEdit) {
      changeMetadataRequired(value, isRequired)
      setIsMetadataRequired(!isMetadataRequired)
    }
  }

  return (
    <Row className='list-item' key={item.value}>
      <Flex className='table-column px-3'>{item.label}</Flex>
      <div className='table-column text-center' style={{ width: '80px' }}>
        <Switch
          onChange={() => {
            isRequired(item.value, !isMetadataRequired)
          }}
          className='ml-0'
        />
      </div>
      <div className='table-column text-center' style={{ width: '80px' }}>
        <Button
          onClick={() => {
            deleteRequied(item)
          }}
          className='btn btn-with-icon'
        >
          <Icon name='trash-2' width={20} fill='#656D7B' />
        </Button>
      </div>
    </Row>
  )
}

const ContentTypesMetadataTable: FC<ContentTypesMetadataTableType> = ({
  changeMetadataRequired,
  isEdit,
  onDelete,
  organisationId,
  selectedContentTypes,
}) => {
  return (
    <PanelSearch
      id='content-types-list'
      className='mt-4 no-pad mb-2'
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
        <ContentTypesMetadataRow
          item={s}
          isEdit={isEdit}
          organisationId={organisationId}
          onDelete={onDelete}
          changeMetadataRequired={changeMetadataRequired}
        />
      )}
    />
  )
}

export default ContentTypesMetadataTable
