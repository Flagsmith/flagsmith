import React, { FC, useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import SupportedContentTypesSelect, {
  SelectContentTypesType,
} from 'components/metadata/SupportedContentTypesSelect'

import {
  useCreateMetadataFieldMutation,
  useGetMetadataFieldQuery,
  useUpdateMetadataFieldMutation,
} from 'common/services/useMetadataField'

import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'

import {
  useCreateMetadataModelFieldMutation,
  useUpdateMetadataModelFieldMutation,
  useDeleteMetadataModelFieldMutation,
} from 'common/services/useMetadataModelField'
import {
  ContentType,
  MetadataModelField,
  isRequiredFor,
} from 'common/types/responses'

type CreateMetadataFieldType = {
  id?: string
  isEdit: boolean
  metadataModelFieldList?: MetadataModelField[]
  onComplete?: () => void
  organisationId: string
  projectId: string
}

type QueryBody = Omit<MetadataModelField, 'id'>

type Query = {
  body: QueryBody
  id?: number
  organisation_id: string
}

type MetadataType = {
  id: number
  value: string
  label: string
}

type metadataFieldUpdatedSelectListType = MetadataModelField & {
  removed: boolean
  new: boolean
}

const CreateMetadataField: FC<CreateMetadataFieldType> = ({
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
  const { data, isLoading } = useGetMetadataFieldQuery(
    { organisation_id: id! },
    { skip: !id },
  )

  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: `${organisationId}`,
  })
  const [createMetadataField, { isLoading: creating, isSuccess: created }] =
    useCreateMetadataFieldMutation()
  const [updateMetadataField, { isLoading: updating, isSuccess: updated }] =
    useUpdateMetadataFieldMutation()

  const [createMetadataModelField] = useCreateMetadataModelFieldMutation()
  const [updateMetadataModelField] = useUpdateMetadataModelFieldMutation()

  const [deleteMetadataModelField] = useDeleteMetadataModelFieldMutation()
  const projectContentType: ContentType =
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
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, isLoading])

  useEffect(() => {
    if (!updating && updated) {
      onComplete?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [updating, updated])

  useEffect(() => {
    if (created && !creating) {
      onComplete?.()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [creating, created])

  const [typeValue, setTypeValue] = useState<MetadataType>()
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [metadataFieldSelectList, setMetadataFieldSelectList] = useState<
    SelectContentTypesType[]
  >([])
  const [metadataUpdatedSelectList, setMetadataFieldUpdatedSelectList] =
    useState<metadataFieldUpdatedSelectListType[]>([])

  const generateDataQuery = (
    contentType: string | number,
    field: number,
    isRequiredFor: boolean,
    id: number,
    isNew = false,
  ) => {
    const query: Query = {
      body: {
        content_type: contentType,
        field: field,
        is_required_for: isRequiredFor
          ? ([
              {
                content_type: projectContentType.id,
                object_id: parseInt(projectId),
              } as isRequiredFor,
            ] as isRequiredFor[])
          : [],
      },
      id: id,
      organisation_id: organisationId,
    }
    if (isNew) {
      const newQuery = { ...query }
      delete newQuery.id
      return newQuery
    }
    return query
  }

  const save = () => {
    if (isEdit) {
      updateMetadataField({
        body: {
          description,
          name,
          organisation: organisationId,
          type: `${typeValue?.value}`,
        },
        id: id!,
      }).then(() => {
        Promise.all(
          metadataUpdatedSelectList?.map(
            async (m: metadataFieldUpdatedSelectListType) => {
              const query = generateDataQuery(
                m.content_type,
                m.field,
                m.is_required_for,
                m.id,
                m.new,
              )
              if (!m.removed && !m.new) {
                await updateMetadataModelField(query)
              } else if (m.removed) {
                await deleteMetadataModelField({
                  id: m.id,
                  organisation_id: organisationId,
                })
              } else if (m.new) {
                const newQuery = { ...query }
                delete newQuery.id
                await createMetadataModelField(newQuery)
              }
            },
          ),
        )
        closeModal()
      })
    } else {
      createMetadataField({
        body: {
          description,
          name,
          organisation: organisationId,
          type: `${typeValue?.value}`,
        },
      }).then((res) => {
        Promise.all(
          metadataFieldSelectList.map(async (m) => {
            const query = generateDataQuery(
              m.value,
              res?.data.id,
              !!m?.isRequired,
              0,
              true,
            )
            await createMetadataModelField(query)
          }),
        )
      })
    }
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
      <InputGroup
        title={'Type'}
        component={
          <Select
            value={typeValue}
            placeholder='Select a metadata type'
            options={metadataTypes}
            onChange={(m: MetadataType) => {
              setTypeValue(m)
            }}
            className='mb-4 react-select'
          />
        }
      />
      <SupportedContentTypesSelect
        organisationId={organisationId}
        isEdit={isEdit}
        getMetadataContentTypes={(m: SelectContentTypesType[]) => {
          if (isEdit) {
            const newMetadataFieldArray: metadataFieldUpdatedSelectListType[] =
              []

            metadataModelFieldList?.forEach((item1) => {
              const match = m.find(
                (item2) => item2.value === item1.content_type.toString(),
              )

              if (match) {
                const isRequiredLength = !!item1.is_required_for.length
                const isRequired = match.isRequired
                if (isRequiredLength !== isRequired) {
                  newMetadataFieldArray.push({
                    ...item1,
                    is_required_for: isRequired,
                  })
                }
              } else {
                newMetadataFieldArray.push({
                  ...item1,
                  new: false,
                  removed: true,
                })
              }
              m.forEach((item) => {
                const match = metadataModelFieldList.find(
                  (item2) => item2.content_type.toString() === item.value,
                )
                if (!match) {
                  newMetadataFieldArray.push({
                    ...item1,
                    content_type: item.value,
                    is_required_for: m?.isRequired,
                    new: true,
                    removed: false,
                  })
                }
              })
            })
            setMetadataFieldUpdatedSelectList(newMetadataFieldArray)
          } else {
            setMetadataFieldSelectList(m)
          }
        }}
        metadataModelFieldList={metadataModelFieldList!}
      />
      <Button
        disabled={!name || !typeValue || !metadataFieldSelectList}
        onClick={save}
        className='float-right'
      >
        {isEdit ? 'Update Metadata Field' : 'Create Metadata Field'}
      </Button>
    </div>
  )
}

export default CreateMetadataField
