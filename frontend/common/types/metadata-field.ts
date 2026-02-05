import { MetadataField } from './responses'

export type CustomMetadataField = MetadataField & {
  metadataModelFieldId: number | string | null
  isRequiredFor: boolean
  model_field?: string | number
  hasValue?: boolean
  field_value?: string
}
