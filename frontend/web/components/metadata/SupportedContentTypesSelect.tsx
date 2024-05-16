import React, { FC, useEffect, useState } from 'react'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import { ContentType, MetadataModelField } from 'common/types/responses'
import InputGroup from 'components/base/forms/InputGroup'
import ContentTypesMetadataFieldTable from './ContentTypesMetadataFieldTable'

type SupportedContentTypesSelectType = {
  organisationId: string
  isEdit: boolean
  getMetadataContentTypes: (m: SelectContentTypesType[]) => void
  metadataModelFieldList: MetadataModelField[]
}

export type SelectContentTypesType = {
  label: string
  value: string
  isRequired?: boolean
}
const SupportedContentTypesSelect: FC<SupportedContentTypesSelectType> = ({
  getMetadataContentTypes,
  isEdit,
  metadataModelFieldList,
  organisationId,
}) => {
  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: organisationId,
  })
  const [selectedContentTypes, setSelectedContentTypes] = useState<
    SelectContentTypesType[]
  >([])

  useEffect(() => {
    if (isEdit && !!supportedContentTypes?.length) {
      const excludedModels = ['project', 'organisation']
      const newSelectedContentTypes = supportedContentTypes
        .filter((item) => !excludedModels.includes(item.model))
        .filter((item) =>
          metadataModelFieldList.some(
            (entry) => entry.content_type === item.id,
          ),
        )
        .map((item) => {
          const match = metadataModelFieldList.find(
            (entry) => entry.content_type === item.id,
          )
          const isRequired = match && !!match.is_required_for.length

          return {
            isRequired: isRequired,
            label: item.model,
            value: item.id.toString(),
          }
        })

      setSelectedContentTypes(newSelectedContentTypes)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [supportedContentTypes])

  useEffect(() => {
    getMetadataContentTypes(selectedContentTypes)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedContentTypes])

  return (
    <>
      <InputGroup
        title={'Entities'}
        component={
          <Select
            placeholder='Select the Entity'
            options={(supportedContentTypes || [])
              .filter(
                (v) =>
                  v.model !== 'project' &&
                  v.model !== 'organisation' &&
                  !selectedContentTypes.some((x) => x.value === `${v.id}`),
              )
              .map((v: ContentType) => ({
                label: v.model,
                value: `${v.id}`,
              }))}
            onChange={(v: SelectContentTypesType) => {
              setSelectedContentTypes((prevState) => [...prevState, v])
            }}
            className='mb-4 react-select'
          />
        }
      />
      {!!selectedContentTypes.length && (
        <ContentTypesMetadataFieldTable
          metadataModelFieldList={metadataModelFieldList}
          selectedContentTypes={selectedContentTypes}
          onDelete={(v: SelectContentTypesType) => {
            setSelectedContentTypes((prevState) =>
              prevState.filter((item) => item.value !== v.value),
            )
          }}
          organisationId={organisationId}
          isEdit={isEdit}
          changeMetadataRequired={(v: string, r: boolean) => {
            setSelectedContentTypes((prevState) =>
              prevState.map((item): SelectContentTypesType => {
                const updatedItem: SelectContentTypesType = {
                  ...item,
                  isRequired: item.value === v ? r : item.isRequired,
                }
                return updatedItem
              }),
            )
          }}
        />
      )}
    </>
  )
}

export default SupportedContentTypesSelect
