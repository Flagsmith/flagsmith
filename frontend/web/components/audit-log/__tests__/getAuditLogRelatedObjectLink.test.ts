import {
  AuditLogDetail,
  AuditLogEnvironment,
  AuditLogRelatedObjectType,
  ProjectSummary,
} from 'common/types/responses'
import moment from 'moment'
import {
  getAuditLogRelatedObjectLink,
  isAuditLogVersionLocked,
} from 'components/audit-log/getAuditLogRelatedObjectLink'

const project: ProjectSummary = {
  enable_dynamo_db: true,
  enable_realtime_updates: false,
  enforce_feature_owners: false,
  feature_name_regex: null,
  hide_disabled_flags: false,
  id: 1,
  migration_status: 'NOT_APPLICABLE',
  minimum_change_request_approvals: null,
  name: 'Website',
  only_allow_lower_case_feature_names: true,
  organisation: 1,
  prevent_flag_defaults: false,
  show_edge_identity_overrides_for_feature: false,
  stale_flags_limit_days: 30,
  use_edge_identities: true,
  uuid: 'project-uuid',
}

const environment: AuditLogEnvironment = {
  allow_client_traits: true,
  api_key: 'prod-key',
  banner_colour: null,
  banner_text: null,
  description: null,
  hide_disabled_flags: null,
  hide_sensitive_data: false,
  id: 2,
  is_creating: false,
  minimum_change_request_approvals: null,
  name: 'Production',
  project: 1,
  use_identity_composite_key_for_hashing: true,
  use_identity_overrides_in_local_eval: false,
  use_mv_v2_evaluation: false,
  use_v2_feature_versioning: true,
  uuid: 'environment-uuid',
}

const detail = (
  related_object_type: AuditLogRelatedObjectType | null,
  overrides: Partial<AuditLogDetail> = {},
): AuditLogDetail => ({
  author: null,
  change_details: [],
  change_type: 'UPDATE',
  created_date: '2026-11-10T14:32:00',
  environment,
  id: 101,
  is_system_event: false,
  log: 'Log',
  organisation: null,
  project,
  related_object_id: 12,
  related_object_type,
  related_object_uuid: 'version-uuid',
  ...overrides,
})

const env = '/project/1/environment/prod-key'

describe('getAuditLogRelatedObjectLink', () => {
  it.each`
    type                  | label                          | to
    ${'FEATURE'}          | ${'View feature'}              | ${`${env}/features?feature=12`}
    ${'SEGMENT'}          | ${'View segment'}              | ${'/project/1/segments/12'}
    ${'ENVIRONMENT'}      | ${'View environment settings'} | ${`${env}/settings`}
    ${'CHANGE_REQUEST'}   | ${'View change request'}       | ${`${env}/change-requests/12`}
    ${'EF_VERSION'}       | ${'View version'}              | ${`${env}/history/version-uuid/`}
    ${'RELEASE_PIPELINE'} | ${'View release pipeline'}     | ${'/project/1/release-pipelines/12'}
    ${'EXPERIMENT'}       | ${'View experiment'}           | ${`${env}/experiments/12`}
    ${'METRIC'}           | ${'View metrics'}              | ${`${env}/metrics`}
  `('links $type to $to', ({ label, to, type }) => {
    expect(getAuditLogRelatedObjectLink(detail(type))).toEqual({ label, to })
  })

  it.each`
    type
    ${'FEATURE_STATE'}
    ${'EDGE_IDENTITY'}
    ${'FEATURE_HEALTH'}
    ${'IMPORT_REQUEST'}
    ${'WAREHOUSE_CONNECTION'}
    ${null}
  `('has no link for $type', ({ type }) => {
    expect(getAuditLogRelatedObjectLink(detail(type))).toBeNull()
  })

  it.each`
    type                | to
    ${'FEATURE'}        | ${'/project/1/flag/12/environments'}
    ${'CHANGE_REQUEST'} | ${'/project/1/change-requests/12'}
  `(
    'links $type at project level when there is no environment',
    ({ to, type }) => {
      expect(
        getAuditLogRelatedObjectLink(detail(type, { environment: null }))?.to,
      ).toBe(to)
    },
  )

  it.each`
    type
    ${'ENVIRONMENT'}
    ${'EF_VERSION'}
    ${'EXPERIMENT'}
    ${'METRIC'}
  `('has no link for $type without an environment', ({ type }) => {
    expect(
      getAuditLogRelatedObjectLink(detail(type, { environment: null })),
    ).toBeNull()
  })

  it('has no link for a deleted object', () => {
    expect(
      getAuditLogRelatedObjectLink(
        detail('SEGMENT', { change_type: 'DELETE' }),
      ),
    ).toBeNull()
  })

  it('has no link without a project', () => {
    expect(
      getAuditLogRelatedObjectLink(detail('SEGMENT', { project: null })),
    ).toBeNull()
  })

  it('has no link without the id the route needs', () => {
    expect(
      getAuditLogRelatedObjectLink(
        detail('SEGMENT', { related_object_id: null }),
      ),
    ).toBeNull()
    expect(
      getAuditLogRelatedObjectLink(
        detail('EF_VERSION', { related_object_uuid: null }),
      ),
    ).toBeNull()
  })
})

describe('isAuditLogVersionLocked', () => {
  const daysAgo = (days: number) => moment().subtract(days, 'days').format()

  it.each`
    name                      | type            | age   | limit   | locked
    ${'no limit on the plan'} | ${'EF_VERSION'} | ${90} | ${null} | ${false}
    ${'inside the limit'}     | ${'EF_VERSION'} | ${5}  | ${30}   | ${false}
    ${'older than the limit'} | ${'EF_VERSION'} | ${40} | ${30}   | ${true}
    ${'not a version'}        | ${'SEGMENT'}    | ${40} | ${30}   | ${false}
  `('$name', ({ age, limit, locked, type }) => {
    expect(
      isAuditLogVersionLocked(
        detail(type, { created_date: daysAgo(age) }),
        limit,
      ),
    ).toBe(locked)
  })
})
