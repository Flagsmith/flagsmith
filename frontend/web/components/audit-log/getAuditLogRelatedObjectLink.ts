import {
  AuditLogDetail,
  AuditLogRelatedObjectType,
} from 'common/types/responses'
import { isVersionOverLimit } from 'common/utils/isVersionOverLimit'

export type AuditLogRelatedObjectLink = {
  to: string
  label: string
}

type LinkParts = {
  project: string
  env: string | null
  id: number | null
  uuid: string | null
}

// One entry per type with a page. A path is null when the log lacks what the
// route needs.
const LINKS: Partial<
  Record<
    AuditLogRelatedObjectType,
    { label: string; path: (parts: LinkParts) => string | null }
  >
> = {
  CHANGE_REQUEST: {
    label: 'View change request',
    path: ({ env, id, project }) =>
      id === null ? null : `${env ?? project}/change-requests/${id}`,
  },
  EF_VERSION: {
    label: 'View version',
    path: ({ env, uuid }) => (env && uuid ? `${env}/history/${uuid}/` : null),
  },
  ENVIRONMENT: {
    label: 'View environment settings',
    path: ({ env }) => env && `${env}/settings`,
  },
  EXPERIMENT: {
    label: 'View experiment',
    path: ({ env, id }) =>
      env && id !== null ? `${env}/experiments/${id}` : null,
  },
  FEATURE: {
    label: 'View feature',
    path: ({ env, id, project }) => {
      if (id === null) return null
      return env
        ? `${env}/features?feature=${id}`
        : `${project}/flag/${id}/environments`
    },
  },
  METRIC: {
    label: 'View metrics',
    path: ({ env }) => env && `${env}/metrics`,
  },
  RELEASE_PIPELINE: {
    label: 'View release pipeline',
    path: ({ id, project }) =>
      id === null ? null : `${project}/release-pipelines/${id}`,
  },
  SEGMENT: {
    label: 'View segment',
    path: ({ id, project }) =>
      id === null ? null : `${project}/segments/${id}`,
  },
}

// Where to go when a log has no field changes to show. Null when the object has
// no page, is gone, or the log lacks what the route needs.
export const getAuditLogRelatedObjectLink = (
  item: AuditLogDetail,
): AuditLogRelatedObjectLink | null => {
  const link = item.related_object_type && LINKS[item.related_object_type]
  if (!link || item.change_type === 'DELETE' || !item.project) return null
  const project = `/project/${item.project.id}`
  const env =
    item.environment && `${project}/environment/${item.environment.api_key}`
  const to = link.path({
    env,
    id: item.related_object_id,
    project,
    uuid: item.related_object_uuid,
  })
  return to ? { label: link.label, to } : null
}

// A version older than the plan's history limit can't be opened.
export const isAuditLogVersionLocked = (
  item: AuditLogDetail,
  versionLimitDays: number | null | undefined,
) =>
  item.related_object_type === 'EF_VERSION' &&
  isVersionOverLimit(versionLimitDays, item.created_date)
