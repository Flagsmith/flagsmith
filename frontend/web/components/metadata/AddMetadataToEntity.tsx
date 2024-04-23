import React, { FC, useEffect, useState } from 'react'
import PanelSearch from 'components/PanelSearch'
import Button from 'components/base/forms/Button'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'
import { useGetMetadataFieldListQuery } from 'common/services/useMetadataField'
import { useGetSegmentQuery } from 'common/services/useSegment'
import {
  useGetEnvironmentQuery,
  useUpdateEnvironmentMutation,
} from 'common/services/useEnvironment'
import { MetadataField, Metadata } from 'common/types/responses'
import Input from 'components/base/forms/Input'
import Utils from 'common/utils/utils'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import Tooltip from 'components/Tooltip'
import { sortBy } from 'lodash'

export type CustomMetadataField = MetadataField & {
  metadataModelFieldId: number | string | null
  isRequiredFor: boolean
  model_field?: string | number
  metadataEntity?: boolean
  field_value?: string
}

type CustomMetadata = (Metadata & CustomMetadataField) | null

type AddMetadataToEntityType = {
  organisationId: string
  projectId: string | number
  entityContentType: number
  entityId: string
  entity: number | string
  envName?: string
  onChange?: (m: CustomMetadataField[]) => void
}

const AddMetadataToEntity: FC<AddMetadataToEntityType> = ({
  entity,
  entityContentType,
  entityId,
  envName,
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

  const [updateEnvironment] = useUpdateEnvironmentMutation()

  const [
    metadataFieldsAssociatedtoEntity,
    setMetadataFieldsAssociatedtoEntity,
  ] = useState<CustomMetadataField[]>()

  useEffect(() => {
    if (metadataFieldsAssociatedtoEntity?.length && metadataChanged) {
      const metadataParsed = metadataFieldsAssociatedtoEntity
        .filter((m) => m.metadataEntity)
        .map((i) => {
          const { metadataModelFieldId, ...rest } = i
          return { model_field: metadataModelFieldId, ...rest }
        })
      onChange?.(metadataParsed as CustomMetadataField[])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metadataFieldsAssociatedtoEntity])

  const [metadataChanged, setMetadataChanged] = useState<boolean>(false)
  useEffect(() => {
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [metadataFieldsAssociatedtoEntity])

  const mergeMetadataEntityWithMetadataField = (
    metadata: Metadata[],
    metadataField: CustomMetadataField[],
  ) => {
    const map = new Map(
      metadataField.map((item) => [item.metadataModelFieldId, item]),
    )
    return metadataField.map((item) => {
      const mergedItem = {
        ...item,
        ...(map.get(item.model_field!) || {}),
        ...(metadata.find((m) => m.model_field === item.metadataModelFieldId) ||
          {}),
      }
      mergedItem.metadataEntity =
        mergedItem.metadataModelFieldId !== undefined &&
        mergedItem.model_field !== undefined
      return mergedItem
    })
  }

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
        const mergedFeatureEntity = mergeMetadataEntityWithMetadataField(
          projectFeatureData?.metadata,
          metadataForContentType,
        )
        const sortedArray = sortBy(mergedFeatureEntity, (m) =>
          m.isRequiredFor ? -1 : 1,
        )
        setMetadataFieldsAssociatedtoEntity(sortedArray)
      } else if (segmentData?.metadata && segmentDataLoaded) {
        const mergedSegmentEntity = mergeMetadataEntityWithMetadataField(
          segmentData?.metadata,
          metadataForContentType,
        )
        const sortedArray = sortBy(mergedSegmentEntity, (m) =>
          m.isRequiredFor ? -1 : 1,
        )
        setMetadataFieldsAssociatedtoEntity(sortedArray)
      } else if (envData?.metadata && envDataLoaded) {
        const mergedEnvEntity = mergeMetadataEntityWithMetadataField(
          envData?.metadata,
          metadataForContentType,
        )
        const sortedArray = sortBy(mergedEnvEntity, (m) =>
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
              <Row className='table-column flex-1'>Metadata </Row>
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
                getMetadataValue={(m: CustomMetadata) => {
                  setMetadataFieldsAssociatedtoEntity((prevState) =>
                    prevState?.map((metadata) => {
                      if (metadata.id === m?.id) {
                        return {
                          ...metadata,
                          field_value: m?.field_value,
                          metadataEntity: !!m?.field_value,
                        }
                      }
                      return metadata
                    }),
                  )
                  setMetadataChanged(true)
                }}
              />
            )
          }}
        />
        {entity === 'environment' && (
          <div className='text-right'>
            <Button
              theme='primary'
              className='mt-2'
              onClick={() => {
                updateEnvironment({
                  body: {
                    metadata: metadataFieldsAssociatedtoEntity
                      ?.filter((m) => m.metadataEntity)
                      .map((i) => {
                        const { field_value, ...rest } = i
                        return {
                          field_value,
                          model_field: i.metadataModelFieldId,
                          ...rest,
                        }
                      }) as Metadata[],
                    name: envName!,
                    project: parseInt(`${projectId}`),
                  },
                  id: entityId,
                }).then(() => {
                  toast('Environment Metadata Updated')
                })
              }}
            >
              Save Metadata
            </Button>
          </div>
        )}
      </FormGroup>
    </>
  )
}

type MetadataRowType = {
  metadata: CustomMetadata
  onDelete?: () => void
  isEdit: boolean
  getMetadataValue?: (metadata: CustomMetadata) => void
}
const MetadataRow: FC<MetadataRowType> = ({
  getMetadataValue,
  isEdit,
  metadata,
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
          disabled={
            !!metadataValue &&
            (!metadataValueChanged ||
              !Utils.validateMetadataType(metadata?.type, metadataValue))
          }
          onClick={() => {
            const updatedMetadataObject = { ...metadata }
            updatedMetadataObject.field_value = metadataValue
            setMetadataValueChanged(false)
            getMetadataValue?.(updatedMetadataObject as CustomMetadata)
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
