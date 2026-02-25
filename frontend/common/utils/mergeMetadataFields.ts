import { sortBy } from 'lodash'
import {
  Metadata,
  MetadataField,
  MetadataModelField,
  PagedResponse,
} from 'common/types/responses'
import { CustomMetadataField } from 'common/types/metadata-field'

type EntityWithMetadata = {
  metadata?: Metadata[]
}

/**
 * Merges metadata field definitions with model field mappings and existing entity values.
 */
export function mergeMetadataFields(
  fieldList: PagedResponse<MetadataField>,
  modelFieldList: PagedResponse<MetadataModelField>,
  entityData: EntityWithMetadata | null,
  entityContentType: number,
): CustomMetadataField[] {
  // Filter fields that apply to this content type
  const fieldsForContentType: CustomMetadataField[] = fieldList.results
    .filter((meta) =>
      modelFieldList.results.some(
        (item) =>
          item.field === meta.id && item.content_type === entityContentType,
      ),
    )
    .map((meta) => {
      const matchingItem = modelFieldList.results.find(
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
  const existingValues: Metadata[] = entityData?.metadata ?? []

  // Merge field definitions with existing values
  const mergedMetadata = fieldsForContentType.map((field) => {
    const existingValue = existingValues.find(
      (v) => v.model_field === field.metadataModelFieldId,
    )
    return {
      ...field,
      field_value: existingValue?.field_value ?? '',
      hasValue: !!existingValue,
    }
  })

  // Sort required fields first
  return sortBy(mergedMetadata, (m) => (m.isRequiredFor ? -1 : 1))
}
