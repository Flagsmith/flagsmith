import { IconName } from 'components/icons/Icon'
import { AuditLogRelatedObjectType } from 'common/types/responses'

type AuditLogTypeItem = {
  related_object_type: AuditLogRelatedObjectType | null
  project: { id: number } | null
}

const TYPES: Record<
  AuditLogRelatedObjectType,
  { icon: IconName; label: string }
> = {
  CHANGE_REQUEST: { icon: 'request', label: 'Change request' },
  EDGE_IDENTITY: { icon: 'person', label: 'Identity' },
  EF_VERSION: { icon: 'clock', label: 'Feature' },
  ENVIRONMENT: { icon: 'layers', label: 'Environment' },
  EXPERIMENT: { icon: 'flask', label: 'Experiment' },
  FEATURE: { icon: 'features', label: 'Feature' },
  FEATURE_HEALTH: { icon: 'warning', label: 'Other' },
  FEATURE_STATE: { icon: 'features', label: 'Feature' },
  IMPORT_REQUEST: { icon: 'file-text', label: 'Other' },
  METRIC: { icon: 'bar-chart', label: 'Experiment' },
  RELEASE_PIPELINE: { icon: 'rocket', label: 'Release pipeline' },
  SEGMENT: { icon: 'pie-chart', label: 'Segment' },
  WAREHOUSE_CONNECTION: { icon: 'code', label: 'Other' },
}

// Organisation events (members, roles, groups) have no related object yet.
export const getAuditLogTypeIcon = (item: AuditLogTypeItem): IconName => {
  if (item.related_object_type) return TYPES[item.related_object_type].icon
  return item.project ? 'list' : 'people'
}

export const getAuditLogTypeLabel = (item: AuditLogTypeItem): string => {
  if (item.related_object_type) return TYPES[item.related_object_type].label
  return item.project ? 'Project' : 'Organisation'
}
