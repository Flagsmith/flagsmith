import React, { FC, useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import Switch from 'components/Switch'
import Button from 'components/base/forms/Button'

import {
  useCreateMetadataMutation,
  useGetMetadataQuery,
  useUpdateMetadataMutation,
} from 'common/services/useMetadata'

import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'

import {
  useCreateMetadataModelFieldMutation,
  useUpdateMetadataModelFieldMutation,
  useDeleteMetadataModelFieldMutation,
} from 'common/services/useMetadataModelField'
import { ContentType, MetadataModelField } from 'common/types/responses'

type CreateMetadataType = {
  id: string
  isEdit?: boolean
  metadataModelFieldList?: MetadataModelField[]
  onComplete?: () => void
  organisationId: string
  projectId?: string
}

type MetadataType = {
  id: number
  value: string
  label: string
}

type QueryBody = {
  content_type: number
  field: number
  is_required_for: {
    content_type: number
    object_id: number
  }[]
}

const CreateMetadata: FC<CreateMetadataType> = ({
  id,
  isEdit,
  metadataModelFieldList,
  onComplete,
  organisationId,
  projectId,
}) => {
  const metadataTypes: MetadataType[] = [
    { id: 1, label: 'int', value: 'int' },
    { id: 2, label: 'string', value: 'str' },
    { id: 3, label: 'boolean', value: 'bool' },
    { id: 4, label: 'url', value: 'url' },
    { id: 5, label: 'multiline string', value: 'multiline_str' },
  ]
  const { data, isLoading } = useGetMetadataQuery(
    { organisation_id: id },
    { skip: !id },
  )

  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: `${organisationId}`,
  })
  const [createMetadata, { isLoading: creating, isSuccess: created }] =
    useCreateMetadataMutation()
  const [updateMetadata, { isLoading: updating, isSuccess: updated }] =
    useUpdateMetadataMutation()

  const [createMetadataField] = useCreateMetadataModelFieldMutation()
  const [updateMetadataField] = useUpdateMetadataModelFieldMutation()

  const [deleteMetadataModelField] = useDeleteMetadataModelFieldMutation()
  const featureContentType =
    isEdit &&
    supportedContentTypes &&
    Utils.getContentType(supportedContentTypes, 'model', 'feature')
  const segmentContentType =
    isEdit &&
    supportedContentTypes &&
    Utils.getContentType(supportedContentTypes, 'model', 'segment')
  const environmentContentType =
    isEdit &&
    supportedContentTypes &&
    Utils.getContentType(supportedContentTypes, 'model', 'environment')
  const projectContentType =
    isEdit &&
    supportedContentTypes &&
    Utils.getContentType(supportedContentTypes, 'model', 'project')
  useEffect(() => {
    if (data && !isLoading) {
      setName(data.name)
      setDescription(data.description)
      const _metadataType = metadataTypes.find(
        (m: MetadataType) => m.value === data.type,
      )
      if (_metadataType) {
        setTypeValue(_metadataType)
      }
      setMetadataFieldsArray(
        metadataModelFieldList?.map((m: MetadataModelField) => m.content_type),
      )
      setRequiredMetadataModelFields(
        metadataModelFieldList
          ?.filter((m: MetadataModelField) => m.is_required_for.length > 0)
          .map((m: MetadataModelField) => m.content_type),
      )
      setFlagsEnabled(
        !!metadataModelFieldList?.find(
          (i: MetadataModelField) => i.content_type == featureContentType,
        ),
      )
      setSegmentsEnabled(
        !!metadataModelFieldList?.find(
          (i: MetadataModelField) => i.content_type == segmentContentType,
        ),
      )
      setEnvironmentEnabled(
        !!metadataModelFieldList?.find(
          (i: MetadataModelField) => i.content_type == environmentContentType,
        ),
      )
      setFlagRequired(
        !!metadataModelFieldList?.find(
          (i: MetadataModelField) =>
            i.content_type == featureContentType &&
            i?.is_required_for.length > 0,
        ),
      )
      setSegmentRequired(
        !!metadataModelFieldList?.find(
          (i: MetadataModelField) =>
            i.content_type == segmentContentType &&
            i?.is_required_for.length > 0,
        ),
      )
      setEnvironmentRequired(
        !!metadataModelFieldList?.find(
          (i: MetadataModelField) =>
            i.content_type == environmentContentType &&
            i?.is_required_for.length > 0,
        ),
      )
    }
  }, [data, isLoading])

  useEffect(() => {
    if (!updating && updated) {
      onComplete?.()
    }
  }, [updating, updated])

  useEffect(() => {
    if (created && !creating) {
      onComplete?.()
    }
  }, [creating, created])

  const [typeValue, setTypeValue] = useState<MetadataType>()
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [environmentEnabled, setEnvironmentEnabled] = useState<boolean>(false)
  const [segmentEnabled, setSegmentsEnabled] = useState<boolean>(false)
  const [flagEnabled, setFlagsEnabled] = useState<boolean>(false)
  const [environmentRequired, setEnvironmentRequired] = useState<boolean>(false)
  const [segmentRequired, setSegmentRequired] = useState<boolean>(false)
  const [flagRequired, setFlagRequired] = useState<boolean>(false)
  const [metadataFieldsArray, setMetadataFieldsArray] = useState<array>([])
  const [requiredMetadataModelFields, setRequiredMetadataModelFields] =
    useState<array>([])

  const handleMetadataModelField = (contentTypeId, enabled: boolean) => {
    if (enabled) {
      addMetadataField(contentTypeId)
    } else {
      removeMetadataField(contentTypeId)
    }
  }

  const handleRequiredMetadataModelField = (
    contentTypeId,
    enabled: boolean,
  ) => {
    if (enabled) {
      addRequiredMetadataModelFields(contentTypeId)
    } else {
      removeRequiredMetadataModelField(contentTypeId)
    }
  }

  const addMetadataField = (newMetadataField) => {
    setMetadataFieldsArray([...metadataFieldsArray, newMetadataField])
  }

  const addRequiredMetadataModelFields = (newRequiredMetadataField) => {
    setRequiredMetadataModelFields([
      ...requiredMetadataModelFields,
      newRequiredMetadataField,
    ])
  }

  const removeMetadataField = (metadataFieldToRemove) => {
    const updatedMetadataFields = metadataFieldsArray.filter(
      (m) => m !== metadataFieldToRemove,
    )
    setMetadataFieldsArray(updatedMetadataFields)
  }

  const removeRequiredMetadataModelField = (requiredMetadataFieldToRemove) => {
    const requiredMetadataModelFieldsToRemove =
      requiredMetadataModelFields.filter(
        (m) => m !== requiredMetadataFieldToRemove,
      )

    setRequiredMetadataModelFields(requiredMetadataModelFieldsToRemove)
  }

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
        placeholder='e.g. JIRA Ticket Number'
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
        placeholder={"e.g. 'The JIRA Ticket Number associated with this flag'"}
      />
      <Select
        value={typeValue}
        placeholder='Select a metadata type'
        options={metadataTypes}
        onChange={(m: MetadataType) => {
          setTypeValue(m)
        }}
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
                    environmentContentType,
                    !environmentEnabled,
                  )
                }}
                className='ml-0'
              />
            </div>
            <div className='entities-cell'>
              <Switch
                checked={environmentRequired}
                onChange={() => {
                  setEnvironmentRequired(!environmentRequired)
                  handleRequiredMetadataModelField(
                    environmentContentType,
                    !environmentRequired,
                  )
                }}
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
                  handleMetadataModelField(segmentContentType, !segmentEnabled)
                }}
                className='ml-0'
              />
            </div>
            <div className='entities-cell'>
              <Switch
                checked={segmentRequired}
                onChange={() => {
                  setSegmentRequired(!segmentRequired)
                  handleRequiredMetadataModelField(
                    segmentContentType,
                    !segmentRequired,
                  )
                }}
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
                  handleMetadataModelField(featureContentType, !flagEnabled)
                }}
                className='ml-0'
              />
            </div>
            <div className='entities-cell'>
              <Switch
                checked={flagRequired}
                onChange={() => {
                  setFlagRequired(!flagRequired)
                  handleRequiredMetadataModelField(
                    featureContentType,
                    !flagRequired,
                  )
                }}
                className='ml-0'
              />
            </div>
          </div>
        </div>
      )}
      <Button
        disabled={!name || !typeValue}
        onClick={() => {
          if (isEdit) {
            updateMetadata({
              body: {
                description,
                name,
                organisation: organisationId,
                type: `${typeValue?.value}`,
              },
              id,
            })
            if (!metadataModelFieldList?.length && id) {
              metadataFieldsArray.map((m: ContentType) => {
                createMetadataField({
                  body: { 'content_type': m.id, 'field': id },
                  organisation_id: organisationId,
                })
              })
            } else if (metadataModelFieldList?.length && id) {
              const metadataToDelete = metadataModelFieldList.filter(
                (m) => !metadataFieldsArray.includes(m.content_type),
              )
              const metadataToCreate = metadataFieldsArray.filter(
                (id: number) =>
                  !metadataModelFieldList.some((m) => m.content_type === id),
              )
              const metadataToUpdate = metadataModelFieldList.filter((m) =>
                requiredMetadataModelFields.includes(m.content_type),
              )
              if (metadataToDelete.length) {
                metadataToDelete.map((m) => {
                  deleteMetadataModelField({
                    id: m.id,
                    organisation_id: organisationId,
                  })
                })
              }
              if (metadataToCreate.length) {
                metadataToCreate.map((m: ContentType) => {
                  createMetadataField({
                    body: { 'content_type': m.id, 'field': id },
                    organisation_id: organisationId,
                  })
                })
              }
              if (metadataToUpdate.length) {
                metadataToUpdate.map((m) => {
                  const query = {
                    body: {
                      content_type: m.content_type,
                      field: m.field,
                    } as QueryBody,
                    id: m.id,
                    organisation_id: organisationId,
                  }
                  const isRequiredFor = [
                    {
                      content_type: projectContentType,
                      object_id: Number(projectId),
                    },
                  ]
                  if (
                    m.content_type === environmentContentType &&
                    environmentRequired
                  ) {
                    query.body.is_required_for = isRequiredFor
                  }
                  if (m.content_type === featureContentType && flagRequired) {
                    query.body.is_required_for = isRequiredFor
                  }
                  if (
                    m.content_type === segmentContentType &&
                    segmentRequired
                  ) {
                    query.body.is_required_for = isRequiredFor
                  }
                  updateMetadataField(query)
                })
              }
            }
          } else {
            createMetadata({
              body: {
                description,
                name,
                organisation: organisationId,
                type: `${typeValue?.value}`,
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
