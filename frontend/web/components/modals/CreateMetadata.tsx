import React, { useEffect, useState } from 'react'
import AccountStore from 'common/stores/account-store'

import {
  useCreateMetadataMutation,
  useGetMetadataQuery,
  useUpdateMetadataMutation,
} from 'common/services/useMetadata'

import {
  useCreateMetadataModelFieldMutation,
  useUpdateMetadataModelFieldMutation,
  useDeleteMetadataModelFieldMutation,
} from 'common/services/useMetadataModelField'

import Constants from 'common/constants'

type CreateMetadataType = {
  id?: string
  isEdit?: boolean
  metadataModelFieldList?: Array
}

type MetadataType = {
  id: int
  value: string
  label: string
  onComplete?: () => void
}

const CreateMetadata: FC<CreateMetadataType> = ({
  id,
  isEdit,
  metadataModelFieldList,
  onComplete,
}) => {
  const metadataTypes: MetadataType = [
    { id: 1, label: 'int', value: 'int' },
    { id: 2, label: 'string', value: 'str' },
    { id: 3, label: 'boolean', value: 'bool' },
    { id: 4, label: 'url', value: 'url' },
    { id: 5, label: 'multiline string', value: 'multiline_str' },
  ]
  const orgId = AccountStore.getOrganisation().id
  const { data, isLoading } = useGetMetadataQuery({ id }, { skip: !id })

  const [createMetadata, { isLoading: creating, isSuccess: created }] =
    useCreateMetadataMutation()
  const [updateMetadata, { isLoading: updating, isSuccess: updated }] =
    useUpdateMetadataMutation()

  const [
    createMetadataField,
    { isLoading: creatingMetadataField, isSuccess: metadataFieldcreated },
  ] = useCreateMetadataModelFieldMutation()
  const [
    updateMetadataField,
    { isLoading: updatingMetadataField, isSuccess: MetadataFieldUpdated },
  ] = useUpdateMetadataModelFieldMutation()

  const [
    deleteMetadataModelField,
    { isLoading: deletingMetadataField, isSuccess: MetadataFieldDeleted },
  ] = useDeleteMetadataModelFieldMutation()

  useEffect(() => {
    if (data && !isLoading) {
      setName(data.name)
      setDescription(data.description)
      setTypeValue(metadataTypes.find((m) => m.value === data.type))
      setMetadataFieldsArray(metadataModelFieldList.map((m) => m.content_type))
      setFlagsEnabled(
        !!metadataModelFieldList.find(
          (i) => i.content_type == Constants.contentTypes.flag,
        ),
      )
      setSegmentsEnabled(
        !!metadataModelFieldList.find(
          (i) => i.content_type == Constants.contentTypes.segment,
        ),
      )
      setEnvironmentEnabled(
        !!metadataModelFieldList.find(
          (i) => i.content_type == Constants.contentTypes.environment,
        ),
      )
    }
  }, [data, isLoading])

  useEffect(() => {
    if (!updating && updated) {
      toast('Metadata updated')
      closeModal()
    }
  }, [updating, updated])

  const [typeValue, setTypeValue] = useState<string>('')
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [environmentEnabled, setEnvironmentEnabled] = useState<boolean>(false)
  const [segmentEnabled, setSegmentsEnabled] = useState<boolean>(false)
  const [flagEnabled, setFlagsEnabled] = useState<boolean>(false)
  const [environmentRequired, setEnvironmentRequired] = useState<boolea>(false)
  const [segmentRequired, setSegmentRequired] = useState<boolean>(false)
  const [flagRequired, setFlagRequired] = useState<booleaan>(false)
  const [metadataFieldsArray, setMetadataFieldsArray] = useState<array>([])

  const handleMetadataModelField = (contentTypeId, enabled) => {
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
                  setEnvironmentEnabled(!environmentEnabled)
                  handleMetadataModelField(
                    Constants.contentTypes.environment,
                    !environmentEnabled,
                  )
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
                  handleMetadataModelField(
                    Constants.contentTypes.segment,
                    !segmentEnabled,
                  )
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
                  handleMetadataModelField(
                    Constants.contentTypes.flag,
                    !flagEnabled,
                  )
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
            updateMetadata({
              body: {
                description,
                name,
                organisation: orgId,
                type: typeValue.value,
              },
              id,
            })
            if (!metadataModelFieldList.length && id) {
              metadataFieldsArray.map((m) => {
                createMetadataField({
                  body: { 'content_type': m, 'field': id },
                  id,
                  organisation_id: orgId,
                })
              })
            } else if (metadataModelFieldList.length && id) {
              const metadataToDelete = metadataModelFieldList.filter(
                (m) => !metadataFieldsArray.includes(m.content_type),
              )
              const metadataToCreate = metadataFieldsArray.filter(
                (id) =>
                  !metadataModelFieldList.some((m) => m.content_type === id),
              )
              if (metadataToDelete.length) {
                metadataToDelete.map((m) => {
                  deleteMetadataModelField({
                    id: m.id,
                    organisation_id: orgId,
                  })
                })
              }
              if (metadataToCreate.length) {
                metadataToCreate.map((m) => {
                  createMetadataField({
                    body: { 'content_type': m, 'field': id },
                    id,
                    organisation_id: orgId,
                  })
                })
              }
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
