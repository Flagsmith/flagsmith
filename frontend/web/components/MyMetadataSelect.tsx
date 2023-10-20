import { FC, useEffect, useState } from 'react'
import { useGetListMetaDataQuery } from 'common/services/useMetadata'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'

import MetadataSelect, { MetadataSelectType } from './MetadataSelect' // we need this to make JSX compile

type MyMetadataSelectType = MetadataSelectType & {
  orgId: string
  contentType: number
}

const MyMetadataSelect: FC<MyMetadataSelectType> = ({
  contentType,
  orgId,
  ...props
}) => {
  const [metadataList, setMetadataList] = useState()
  const { data: metadata } = useGetListMetaDataQuery({ organisation: orgId })
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
  }, [metadata, metadataModelField])

  return <MetadataSelect {...props} metadataList={metadataList} />
}

export default MyMetadataSelect
