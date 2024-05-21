import React, { FC, useState } from 'react'

import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import Switch from 'components/Switch'
import Icon from 'components/Icon'

import { MetadataModelField } from 'common/types/responses'
type selectedContentType = {
  label: string
  value: string
  isRequired?: boolean
}

type ContentTypesMetadataFieldTableType = {
  organisationId: string
  selectedContentTypes: selectedContentType[]
  onDelete: (removed: selectedContentType) => void
  isEdit: boolean
  changeMetadataRequired: (value: string, isRequired: boolean) => void
  metadataModelFieldList: MetadataModelField[]
}

type ContentTypesMetadataRowBase = Omit<
  Omit<ContentTypesMetadataFieldTableType, 'metadataModelFieldList'>,
  'selectedContentTypes'
>

type ContentTypesMetadataRowType = ContentTypesMetadataRowBase & {
  item: selectedContentType
  isEnabled: boolean
}

const ContentTypesMetadataRow: FC<ContentTypesMetadataRowType> = ({
  changeMetadataRequired,
  isEnabled,
  item,
  onDelete,
}) => {
  const [isMetadataRequired, setIsMetadataRequired] =
    useState<boolean>(isEnabled)

  const deleteRequied = (removed: selectedContentType) => {
    onDelete?.(removed)
  }
  const isRequired = (value: string, isRequired: boolean) => {
    changeMetadataRequired(value, isRequired)
    setIsMetadataRequired(!isMetadataRequired)
  }

  return (
    <Row className='list-item' key={item.value}>
      <Flex className='table-column px-3'>{item.label}</Flex>
      <div className='table-column text-center' style={{ width: '80px' }}>
        <Switch
          checked={isMetadataRequired}
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

const ContentTypesMetadataFieldTable: FC<
  ContentTypesMetadataFieldTableType
> = ({
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
          isEnabled={s.isRequired!}
        />
      )}
    />
  )
}

export default ContentTypesMetadataFieldTable
