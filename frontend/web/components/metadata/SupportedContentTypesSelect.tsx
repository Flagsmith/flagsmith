import React, { FC, useState } from 'react'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import { ContentType } from 'common/types/responses'
import InputGroup from 'components/base/forms/InputGroup'
import ContentTypesMetadataTable from './ContentTypesMetadataTable'

type SupportedContentTypesSelectType = {
  organisationId: string
  isEdit: boolean
}

export type SelectContentTypes = { label: string; value: string }
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
              .filter((v) => {
                return v.model !== 'project' && v.model !== 'organisation'
              })
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
        />
      )}
    </>
  )
}

export default SupportedContentTypesSelect
