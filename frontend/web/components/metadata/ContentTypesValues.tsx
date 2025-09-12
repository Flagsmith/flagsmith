import React, { FC } from 'react'
import { useGetSupportedContentTypeQuery } from 'common/services/useSupportedContentType'
import { MetadataModelField } from 'common/types/responses'
import classNames from 'classnames'

type ContentTypesValuesType = {
  contentTypes: MetadataModelField[]
  organisationId: string
}

const ContentTypesValues: FC<ContentTypesValuesType> = ({
  contentTypes,
  organisationId,
}) => {
  const { data: supportedContentTypes } = useGetSupportedContentTypeQuery({
    organisation_id: `${organisationId}`,
  })

  const combinedData = contentTypes.map((contentType) => {
    const match = supportedContentTypes?.find(
      (item) => item.id === contentType.content_type,
    )
    return { ...contentType, model: match ? match.model : null }
  })

  return (
    <Row>
      {combinedData.map((contentType, index) => (
        <Tooltip
          key={index}
          title={
            <span
              className={classNames(
                'chip me-2 chip--xs justify-content-start d-inline',
                {
                  'bg-required': !!contentType.is_required_for.length,
                },
              )}
              data-test={'data-test'}
            >
              {`${contentType.model}${
                contentType.is_required_for.length ? '*' : ''
              }`}
            </span>
          }
          place='right'
        >
          {contentType.is_required_for.length ? 'Required' : 'Optional'}
        </Tooltip>
      ))}
    </Row>
  )
}

export default ContentTypesValues
