import React, { useEffect, useState } from 'react'
import AccountStore from 'common/stores/account-store'

import {
  useCreateMetaDataMutation,
  useGetMetaDataQuery,
  useUpdateMetaDataMutation,
} from 'common/services/useMetaData'

import {
  useGetMetadataModelFieldQuery,
  useCreateMetadataModelFieldMutation,
  useUpdateMetadataModelFieldMutation,
  useDeleteMetadataModelFieldMutation,
} from 'common/services/useMetadataModelField'

type CreateMetadataType = {
  id?: string
  isEdit?: boolean
  metadataModelFieldId?: string
}

type MetadataType = {
  id: int
  value: string
  label: string
  onComplete: () => void
}

const CreateMetadata: FC<CreateMetadataType> = ({
  id,
  isEdit,
  metadataModelFieldId,
}) => {
  const metadataTypes: MetadataType = [
    { id: 1, label: 'int', value: 'int' },
    { id: 2, label: 'string', value: 'str' },
    { id: 3, label: 'boolean', value: 'bool' },
    { id: 4, label: 'url', value: 'url' },
    { id: 5, label: 'multiline string', value: 'multiline_str' },
  ]
  const orgId = AccountStore.getOrganisation().id
  const { data, isLoading } = useGetMetaDataQuery({ id }, { skip: !id })
  const { data: metadataFields, isLoading: metadataIsLoading } =
    useGetMetadataModelFieldQuery(
      { id: metadataModelFieldId, organisation_id: orgId },
      { skip: !metadataModelFieldId },
    )

  const [createMetadata, { isLoading: creating, isSuccess: created }] =
    useCreateMetaDataMutation()
  const [updateMetaData, { isLoading: updating, isSuccess: updated }] =
    useUpdateMetaDataMutation()

  const [
    createMetadataField,
    { isLoading: creatingMetadataField, isSuccess: metadataFieldcreated },
  ] = useCreateMetadataModelFieldMutation()
  const [
    updateMetaDataField,
    { isLoading: updatingMetadataField, isSuccess: MetadataFieldUpdated },
  ] = useUpdateMetadataModelFieldMutation()

  const [
    deleteMetaDataField,
    { isLoading: deletingMetadataField, isSuccess: MetadataFieldDeleted },
  ] = useDeleteMetadataModelFieldMutation()

  useEffect(() => {
    if (!creatingMetadataField && metadataFieldcreated) {
      console.log('DEBUG: refetch:')
      // refetch()
    }
  }, [creatingMetadataField, metadataFieldcreated])

  useEffect(() => {
    if (data && !isLoading) {
      setName(data.name)
      setDescription(data.description)
      setTypeValue(metadataTypes.find((m) => m.value === data.type))
    }
  }, [data, isLoading])

  useEffect(() => {
    if (!updating && updated) {
      toast('Metadata updated')
    }
  }, [updating, updated])

  useEffect(() => {
    if (metadataFields && !metadataIsLoading) {
      onComplete?.()
    }
  }, [metadataFields, metadataIsLoading])

  const [typeValue, setTypeValue] = useState<string>('')
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [environmentEnabled, setEnvironmentEnable] = useState<boolean>(false)
  const [segmentEnabled, setSegmentsEnabled] = useState<boolean>(false)
  const [flagEnabled, setFlagsEnabled] = useState<boolean>(false)
  const [environmentRequired, setEnvironmentRequired] = useState<boolea>(false)
  const [segmentRequired, setSegmentRequired] = useState<boolea>(false)
  const [flagRequired, setFlagRequired] = useState<boolea>(false)
  const content_types = [
    { entity: 'environment', id: 30 },
    { entity: 'feature', id: 39 },
    { entity: 'segment', id: 55 },
  ]
  const [metadataFieldsArray, setMetadataFieldsArray] = useState<array>([])

  const handleMetadataModelField = (contentTypeId, enabled) => {
    console.log('DEBUG: contentTypeId:', contentTypeId, 'enabled:', enabled)
    if (enabled) {
      addMetadataField(contentTypeId)
    } else {
      removeMetadataField(contentTypeId)
    }
  }

  const addMetadataField = (newMetadataField) => {
    setMetadataFieldsArray([...metadataFieldsArray, newMetadataField])
  }

  const removeMetadataField = (metadataFieldToRemove) => {
    const updatedMetadataFields = metadataFieldsArray.filter(
      (m) => m !== metadataFieldToRemove,
    )
    setMetadataFieldsArray(updatedMetadataFields)
  }

  // DEBUG: environment_content_type.id: 31 || 30
  // DEBUG: feature_content_type.id: 40 || 39
  // DEBUG: segment_content_type.id: 57 || 55

  useEffect(() => {
    if (created && !creating) {
      onComplete?.()
    }
  }, [creating, created])

  return (
    <div className='create-feature-tab px-3'>
      <InputGroup
        title='Name'
        className='mb-4 mt-2'
        inputProps={{
          className: 'full-width',
          name: 'Name',
        }}
        value={name}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setName(Utils.safeParseEventValue(event))
        }}
        type='text'
        id='metadata-name'
        placeholder='FL-124'
      />
      <InputGroup
        value={description}
        data-test='metadata-desc'
        className='mb-4'
        inputProps={{
          className: 'full-width',
          name: 'metadata-desc',
        }}
        onChange={(event: React.ChangeEvent<HTMLInputElement>) => {
          setDescription(Utils.safeParseEventValue(event))
        }}
        type='text'
        title={'Description (optional)'}
        placeholder='This is a metadata description'
      />
      <Select
        value={typeValue}
        placeholder='Select a metadata type'
        options={metadataTypes}
        onChange={(label) => setTypeValue(label)}
        className='mb-4 react-select'
      />

      {isEdit && (
        <div className='entities-table mb-3'>
          <div className='entities-row'>
            <div className='entities-cell entities-header'>Entities</div>
            <div className='entities-cell entities-header'>Enabled</div>
            <div className='entities-cell entities-header'>Required</div>
          </div>
          <div className='entities-row'>
            <div className='entities-cell entities-header'>Environment</div>
            <div className='entities-cell'>
              <Switch
                checked={environmentEnabled}
                onChange={() => {
                  setEnvironmentEnable(!environmentEnabled)
                  handleMetadataModelField(30, !environmentEnabled)
                }}
                className='ml-0'
              />
            </div>
            <div className='entities-cell'>
              <Switch
                checked={environmentRequired}
                onChange={() => setEnvironmentRequired(!environmentRequired)}
                className='ml-0'
              />
            </div>
          </div>
          <div className='entities-row'>
            <div className='entities-cell entities-header'>Segment</div>
            <div className='entities-cell'>
              <Switch
                checked={segmentEnabled}
                onChange={() => {
                  setSegmentsEnabled(!segmentEnabled)
                  handleMetadataModelField(39, !segmentEnabled)
                }}
                className='ml-0'
              />
            </div>
            <div className='entities-cell'>
              <Switch
                checked={segmentRequired}
                onChange={() => setSegmentRequired(!segmentRequired)}
                className='ml-0'
              />
            </div>
          </div>
          <div className='entities-row'>
            <div className='entities-cell entities-header'>Flag</div>
            <div className='entities-cell'>
              <Switch
                checked={flagEnabled}
                onChange={() => {
                  setFlagsEnabled(!flagEnabled)
                  handleMetadataModelField(57, !flagEnabled)
                }}
                className='ml-0'
              />
            </div>
            <div className='entities-cell'>
              <Switch
                checked={flagRequired}
                onChange={() => setFlagRequired(!flagRequired)}
                className='ml-0'
              />
            </div>
          </div>
        </div>
      )}
      <Button
        onClick={() => {
          if (isEdit) {
            updateMetaData({
              body: {
                description,
                name,
                organisation: orgId,
                type: typeValue.value,
              },
              id,
            })
            if (!metadataFields && id) {
              console.log('DEBUG: metadataFields:', metadataFields, 'id:', id)
              metadataFieldsArray.map((m) => {
                createMetadataField({
                  body: { 'content_type': m, 'field': id },
                  id,
                  organisation_id: orgId,
                })
              })
            } else if (metadataFields && id && metadataModelFieldId) {
            }
            if (metadataFields && id && environmentEnabled) {
              console.log('DEBUG: metadataFields:', metadataFields, 'id:', id)
              // metadataFields.map((m) => {
              //   updateMetaDataField({
              //     body: { 'content_type': m, 'field': id },
              //     id,
              //     organisation_id: orgId,
              //   })
              // })
            }
          } else {
            createMetadata({
              body: {
                description,
                name,
                organisation: orgId,
                type: typeValue.value,
              },
            })
          }
        }}
        className='float-right'
      >
        {isEdit ? 'Update Metadata' : 'Create Metadata'}
      </Button>
    </div>
  )
}

export default CreateMetadata
