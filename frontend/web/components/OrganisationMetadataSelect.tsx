import { FC, useEffect, useState } from 'react'
import { useGetMetadataListQuery } from 'common/services/useMetadata'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'
import { MetadataField } from 'common/types/responses'

import MetadataSelect, { MetadataSelectType } from './MetadataSelect' // we need this to make JSX compile

type OrganisationMetadataSelectType = MetadataSelectType & {
  orgId: string
  contentType: number
}

const OrganisationMetadataSelect: FC<OrganisationMetadataSelectType> = ({
  contentType,
  orgId,
  ...props
}) => {
  const [metadataList, setMetadataList] = useState<MetadataField[]>([])
  const { data: metadata } = useGetMetadataListQuery({ organisation: orgId })
  const { data: metadataModelField } = useGetMetadataModelFieldListQuery({
    organisation_id: orgId,
  })

  useEffect(() => {
    if (metadata?.results?.length && metadataModelField?.results?.length) {
      const metadataForContentType = metadata.results.filter((meta) => {
        return metadataModelField.results.some(
          (item) => item.field === meta.id && item.content_type === contentType,
        )
      })
      setMetadataList(metadataForContentType)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metadata, metadataModelField])

  return <MetadataSelect {...props} metadata={metadataList} />
}

export default OrganisationMetadataSelect
