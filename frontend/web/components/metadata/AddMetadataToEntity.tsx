import React, { FC, useEffect, useState } from 'react'
import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'
import { useGetMetadataFieldListQuery } from 'common/services/useMetadataField'
import { useGetSegmentQuery } from 'common/services/useSegment'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import { MetadataField, Metadata, ProjectFlag } from 'common/types/responses'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import Tooltip from 'components/Tooltip'
import { sortBy } from 'lodash'

type CustomMetadataField = MetadataField & {
  metadataModelFieldId: number | string | null
  isRequiredFor: boolean
  model_field?: string | number
}

type CustomMetadata = (Metadata & CustomMetadataField) | null

type AddMetadataToEntityType = {
  organisationId: string
  projectId: string | number
  entityContentType: number
  entityId: string
  entity: number | string
  onChange: () => void
}

const AddMetadataToEntity: FC<AddMetadataToEntityType> = ({
  entity,
  entityContentType,
  entityId,
  onChange,
  organisationId,
  projectId,
}) => {
  const { data: metadataFieldList, isSuccess: metadataFieldListLoaded } =
    useGetMetadataFieldListQuery({
      organisation: organisationId,
    })
  const {
    data: metadataModelFieldList,
    isSuccess: metadataModelFieldListLoaded,
  } = useGetMetadataModelFieldListQuery({
    organisation_id: organisationId,
  })

  const { data: projectFeatureData, isSuccess: projectFeatureDataLoaded } =
    useGetProjectFlagQuery(
      {
        id: entityId,
        project: projectId,
      },
      { skip: entity !== 'feature' || !entityId },
    )

  const { data: segmentData, isSuccess: segmentDataLoaded } =
    useGetSegmentQuery(
      {
        id: `${entityId}`,
        projectId: `${projectId}`,
      },
      { skip: entity !== 'segment' || !entityId },
    )

  const { data: envData, isSuccess: envDataLoaded } = useGetEnvironmentQuery(
    { id: entityId },
    { skip: entity !== 'environment' || !entityId },
  )

  const [
    metadataFieldsAssociatedtoEntity,
    setMetadataFieldsAssociatedtoEntity,
  ] = useState<CustomMetadataField[]>()

  const [metadataChanged, setMetadataChanged] = useState<boolean>(false)
  useEffect(() => {
    // onChange?.(metadataFieldsAssociatedtoEntity!)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metadataFieldsAssociatedtoEntity])

  console.log(
    'DEBUG: metadataFieldsAssociatedtoEntity:',
    metadataFieldsAssociatedtoEntity,
  )

  useEffect(() => {
    if (
      metadataFieldList &&
      metadataFieldListLoaded &&
      metadataModelFieldList &&
      metadataModelFieldListLoaded
    ) {
      // Filter metadata fields based on the provided content type
      const metadataForContentType = metadataFieldList.results
        // Filter metadata fields that have corresponding entries in the metadata model field list
        .filter((meta) => {
          return metadataModelFieldList.results.some((item) => {
            return (
              item.field === meta.id && item.content_type === entityContentType
            )
          })
        })
        // Map each filtered metadata field to include additional information from the metadata model field list
        .map((meta) => {
          // Find the matching item in the metadata model field list
          const matchingItem = metadataModelFieldList.results.find((item) => {
            return (
              item.field === meta.id && item.content_type === entityContentType
            )
          })
          // Determine if isRequiredFor should be true or false based on is_required_for array
          const isRequiredFor = !!matchingItem?.is_required_for.length
          // Return the metadata field with additional metadata model field information including isRequiredFor
          return {
            ...meta,
            isRequiredFor: isRequiredFor || false,
            metadataModelFieldId: matchingItem ? matchingItem.id : null,
          }
        })
      if (projectFeatureData?.metadata && projectFeatureDataLoaded) {
        const mergeLists = (
          metadata: ProjectFlag['metadata'],
          metadataField: CustomMetadataField[],
        ) => {
          const map = new Map(
            metadataField.map((item) => [item.metadataModelFieldId, item]),
          )
          return metadataField.map((item) => ({
            ...item,
            ...(map.get(item.model_field!) || {}),
            ...(metadata.find(
              (m) => m.model_field === item.metadataModelFieldId,
            ) || {}),
          }))
        }

        const mergedList = mergeLists(
          projectFeatureData?.metadata,
          metadataForContentType,
        )
        const sortedArray = sortBy(mergedList, (m) =>
          m.isRequiredFor ? -1 : 1,
        )
        setMetadataFieldsAssociatedtoEntity(sortedArray)
      } else {
        const sortedArray = sortBy(metadataForContentType, (m) =>
          m.isRequiredFor ? -1 : 1,
        )
        setMetadataFieldsAssociatedtoEntity(sortedArray)
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    metadataFieldList,
    metadataFieldListLoaded,
    metadataModelFieldList,
    metadataModelFieldListLoaded,
    projectFeatureDataLoaded,
    projectFeatureData,
  ])
  return (
    <>
      <FormGroup className='mt-4 setting'>
        <PanelSearch
          className='mt-1 no-pad'
          header={
            <Row className='table-header'>
              <Row className='table-column flex-1'>
                Metadata{' '}
                {metadataChanged && (
                  <div className='unread ml-2 px-1'>{'*'}</div>
                )}
              </Row>
              <Flex className='table-column'>Value</Flex>
              <div className='table-column text-center px-3'></div>
            </Row>
          }
          items={metadataFieldsAssociatedtoEntity}
          renderRow={(m: CustomMetadata) => {
            return (
              <MetadataRow
                metadata={m}
                isEdit={true}
                getMetadataValue={(m: string) => {
                  console.log('DEBUG: m:', m)
                }}
                unSavedMetadata={onChange}
              />
            )
          }}
        />
      </FormGroup>
    </>
  )
}

type MetadataRowType = {
  metadata: CustomMetadata
  onDelete?: () => void
  isEdit: boolean
  getMetadataValue?: (value: string) => void
  unSavedMetadata: () => void
}
const MetadataRow: FC<MetadataRowType> = ({
  getMetadataValue,
  isEdit,
  metadata,
  unSavedMetadata,
}) => {
  const [metadataValue, setMetadataValue] = useState<string>(
    metadata?.field_value || '',
  )
  const [metadataValueChanged, setMetadataValueChanged] =
    useState<boolean>(false)

  return (
    <Row className='space list-item clickable py-2'>
      {metadataValueChanged && <div className='unread ml-2 px-1'>{'*'}</div>}
      <Flex className='table-column'>{`${metadata?.name} ${
        metadata?.isRequiredFor ? '*' : ''
      }`}</Flex>
      {isEdit ? (
        <Flex className='flex-row'>
          <Tooltip
            title={
              <Input
                value={metadataValue}
                onChange={(e: InputEvent) => {
                  setMetadataValue(Utils.safeParseEventValue(e))
                  setMetadataValueChanged(true)
                  unSavedMetadata?.()
                  getMetadataValue?.(Utils.safeParseEventValue(e))
                }}
                className='mr-2'
                style={{ width: '250px' }}
                placeholder='Metadata Value'
                isValid={Utils.validateMetadataType(
                  metadata?.type,
                  metadataValue,
                )}
              />
            }
            place='top'
          >
            {`This value has to be of type ${metadata?.type}`}
          </Tooltip>
        </Flex>
      ) : (
        <Flex className='flex-row'>
          <Flex className='table-column'>{metadata?.field_value}</Flex>
        </Flex>
      )}
      <div className='table-column text-center px-3'>
        <Button
          disabled={!metadataValueChanged}
          onClick={() => {
            openConfirm({
              body: (
                <div>
                  {'Are you sure you delete this metadata '}
                  {'? This action cannot be undone.'}
                </div>
              ),
              destructive: true,
              onYes: () => true,
              title: 'Delete Group',
              yesText: 'Confirm',
            })
          }}
          className='btn'
        >
          Save
        </Button>
      </div>
    </Row>
  )
}

export default AddMetadataToEntity
