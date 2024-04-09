import React, { FC, useState } from 'react'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import { ContentType } from 'common/types/responses'
import InputGroup from 'components/base/forms/InputGroup'
import ContentTypesMetadataTable from './ContentTypesMetadataTable'

type SupportedContentTypesSelectType = {
  organisationId: string
  isEdit: boolean
  getMetadataContentTypes: () => void
}

export type SelectContentTypes = {
  label: string
  value: string
  isRequired?: boolean
}
const SupportedContentTypesSelect: FC<SupportedContentTypesSelectType> = ({
  isEdit,
  organisationId,
}) => {
  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: organisationId,
  })
  const [selectedContentTypes, setSelectedContentTypes] = useState<
    SelectContentTypes[]
  >([])

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
            onChange={(v: SelectContentTypes) => {
              setSelectedContentTypes((prevState) => [...prevState, v])
            }}
            className='mb-4 react-select'
          />
        }
      />
      {!!selectedContentTypes.length && (
        <ContentTypesMetadataTable
          selectedContentTypes={selectedContentTypes}
          onDelete={(v: SelectContentTypes) => {
            setSelectedContentTypes((prevState) =>
              prevState.filter((item) => item.value !== v.value),
            )
          }}
          organisationId={organisationId}
          isEdit={isEdit}
          changeMetadataRequired={(v: string, r: boolean) => {
            setSelectedContentTypes((prevState) =>
              prevState.map(
                (item): SelectContentTypes => ({
                  ...item,
                  isRequired: item.value === v ? r : item.isRequired,
                }),
              ),
            )
          }}
        />
      )}
    </>
  )
}

export default SupportedContentTypesSelect
