import React, { FC, useEffect, useState } from 'react'
import Utils from 'common/utils/utils'
import InputGroup from 'components/base/forms/InputGroup'
import Button from 'components/base/forms/Button'
import SupportedContentTypesSelect from 'components/metadata/SupportedContentTypesSelect'

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
import { MetadataModelField } from 'common/types/responses'

type CreateMetadataType = {
  id?: string
  isEdit: boolean
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

type metadataUpdatedSelectListType = {
  id: number
  field: number
  content_type: number
  is_required_for: boolean
  removed: boolean
}

type metadataListType = { label: string; value: string; isRequired?: boolean }

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
    { organisation_id: id! },
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

  const save = () => {
    if (isEdit) {
      updateMetadata({
        body: {
          description,
          name,
          organisation: organisationId,
          type: `${typeValue?.value}`,
        },
        id: id!,
      }).then(() => {
        Promise.all(
          metadataUpdatedSelectList?.map(async (m) => {
            const query = {
              body: {
                content_type: m.content_type,
                field: m.field,
                is_required_for: m.is_required_for
                  ? [
                      {
                        content_type: projectContentType.id,
                        object_id: projectId,
                      },
                    ]
                  : [],
              },
              id: m.id,
              organisation_id: organisationId,
            }
            if (!('removed' in m)) {
              await updateMetadataField(query)
            } else if (m.removed) {
              await deleteMetadataModelField({
                id: m.id,
                organisation_id: organisationId,
              })
            }
          }),
        )
        closeModal()
      })
    } else {
      createMetadata({
        body: {
          description,
          name,
          organisation: organisationId,
          type: `${typeValue?.value}`,
        },
      }).then((res) => {
        Promise.all(
          metadataSelectList.map(async (m) => {
            await createMetadataField({
              body: {
                content_type: m.value,
                field: `${res?.data.id}`,
              },
              organisation_id: organisationId,
            })
          }),
        )
      })
    }
  }

  const [typeValue, setTypeValue] = useState<MetadataType>()
  const [name, setName] = useState<string>('')
  const [description, setDescription] = useState<string>('')
  const [metadataSelectList, setMetadataSelectList] = useState<
    metadataListType[]
  >([])
  const [metadataUpdatedSelectList, setMetadataUpdatedSelectList] = useState<
    metadataUpdatedSelectListType[]
  >([])

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
        getMetadataContentTypes={(m: metadataListType[]) => {
          if (isEdit) {
            const newMetadataArray: metadataUpdatedSelectListType[] = []

            metadataModelFieldList?.forEach((item1) => {
              const match = m.find(
                (item2) => item2.value === item1.content_type.toString(),
              )

              if (match) {
                const isRequiredLength = !!item1.is_required_for.length
                const isRequired = match.isRequired
                if (isRequiredLength !== isRequired) {
                  newMetadataArray.push({
                    ...item1,
                    is_required_for: isRequired,
                  })
                }
              } else {
                newMetadataArray.push({
                  ...item1,
                  removed: true,
                })
              }
            })
            setMetadataUpdatedSelectList(newMetadataArray)
          } else {
            setMetadataSelectList(m)
          }
        }}
        metadataModelFieldList={metadataModelFieldList!}
      />
      <Button
        disabled={!name || !typeValue || !metadataSelectList}
        onClick={save}
        className='float-right'
      >
        {isEdit ? 'Update Metadata' : 'Create Metadata'}
      </Button>
    </div>
  )
}

export default CreateMetadata
