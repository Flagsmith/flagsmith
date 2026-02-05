import { useMemo } from 'react'
import { sortBy } from 'lodash'
import { useGetMetadataModelFieldListQuery } from 'common/services/useMetadataModelField'
import { useGetMetadataFieldListQuery } from 'common/services/useMetadataField'
import { useGetSegmentQuery } from 'common/services/useSegment'
import { useGetEnvironmentQuery } from 'common/services/useEnvironment'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { MetadataField, Metadata } from 'common/types/responses'

export type CustomMetadataField = MetadataField & {
  metadataModelFieldId: number | string | null
  isRequiredFor: boolean
  model_field?: string | number
  hasValue?: boolean
  field_value?: string
}

type UseEntityMetadataFieldsParams = {
  organisationId: number
  projectId: number
  entityContentType: number
  entityType: 'feature' | 'segment' | 'environment'
  entityId?: number
}

type UseEntityMetadataFieldsResult = {
  metadataFields: CustomMetadataField[]
  isLoading: boolean
}

/**
 * Merges field definitions with existing entity values.
 * This takes the list of metadata field definitions and enriches them
 * with any existing values from the entity.
 */
function mergeFieldDefinitionsWithValues(
  fieldDefinitions: CustomMetadataField[],
  existingValues: Metadata[],
): CustomMetadataField[] {
  return fieldDefinitions.map((field) => {
    const existingValue = existingValues.find(
      (v) => v.model_field === field.metadataModelFieldId,
    )
    return {
      ...field,
      field_value: existingValue?.field_value ?? '',
      hasValue: !!existingValue,
    }
  })
}

/**
 * Hook that fetches and merges metadata fields for an entity.
 *
 * This encapsulates the complex data fetching and merging logic that was
 * previously spread across multiple useEffects in AddMetadataToEntity.
 */
export function useEntityMetadataFields({
  entityContentType,
  entityId,
  entityType,
  organisationId,
  projectId,
}: UseEntityMetadataFieldsParams): UseEntityMetadataFieldsResult {
  // Fetch all metadata field definitions for the organisation
  const { data: metadataFieldList, isLoading: metadataFieldListLoading } =
    useGetMetadataFieldListQuery({
      organisation: organisationId,
    })

  // Fetch all model field mappings
  const { data: metadataModelFieldList, isLoading: metadataModelFieldLoading } =
    useGetMetadataModelFieldListQuery({
      organisation_id: organisationId,
    })

  // Fetch entity-specific data based on type
  const { data: projectFeatureData, isLoading: projectFeatureLoading } =
    useGetProjectFlagQuery(
      { id: entityId!, project: projectId },
      { skip: entityType !== 'feature' || !entityId },
    )

  const { data: segmentData, isLoading: segmentLoading } = useGetSegmentQuery(
    { id: entityId!, projectId },
    { skip: entityType !== 'segment' || !entityId || !projectId },
  )

  const { data: envData, isLoading: envLoading } = useGetEnvironmentQuery(
    { id: entityId! },
    { skip: entityType !== 'environment' || !entityId },
  )

  // Compute the merged metadata fields
  const metadataFields = useMemo<CustomMetadataField[]>(() => {
    if (!metadataFieldList || !metadataModelFieldList) {
      return []
    }

    // Filter metadata fields that apply to this content type
    const fieldsForContentType: CustomMetadataField[] =
      metadataFieldList.results
        .filter((meta) =>
          metadataModelFieldList.results.some(
            (item) =>
              item.field === meta.id && item.content_type === entityContentType,
          ),
        )
        .map((meta) => {
          const matchingItem = metadataModelFieldList.results.find(
            (item) =>
              item.field === meta.id && item.content_type === entityContentType,
          )
          return {
            ...meta,
            isRequiredFor: !!matchingItem?.is_required_for.length,
            metadataModelFieldId: matchingItem ? matchingItem.id : null,
          }
        })

    // Get existing values from the entity
    let existingValues: Metadata[] = []
    if (entityType === 'feature' && projectFeatureData?.metadata) {
      existingValues = projectFeatureData.metadata
    } else if (entityType === 'segment' && segmentData?.metadata) {
      existingValues = segmentData.metadata
    } else if (entityType === 'environment' && envData?.metadata) {
      existingValues = envData.metadata
    }

    // Merge field definitions with existing values
    const mergedMetadata = mergeFieldDefinitionsWithValues(
      fieldsForContentType,
      existingValues,
    )

    return sortBy(mergedMetadata, (m) => (m.isRequiredFor ? -1 : 1))
  }, [
    metadataFieldList,
    metadataModelFieldList,
    entityContentType,
    entityType,
    projectFeatureData,
    segmentData,
    envData,
  ])

  const isLoading =
    metadataFieldListLoading ||
    metadataModelFieldLoading ||
    (entityType === 'feature' && entityId && projectFeatureLoading) ||
    (entityType === 'segment' && entityId && segmentLoading) ||
    (entityType === 'environment' && entityId && envLoading)

  return {
    isLoading: !!isLoading,
    metadataFields,
  }
}
