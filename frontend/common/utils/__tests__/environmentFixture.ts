import type { Environment } from 'common/types/responses'

export const makeEnvironment = (id: number, name: string): Environment => ({
  allow_client_traits: true,
  api_key: `key-${id}`,
  hide_disabled_flags: null,
  hide_sensitive_data: false,
  id,
  is_creating: false,
  metadata: [],
  minimum_change_request_approvals: null,
  name,
  project: 1,
  show_disabled_flags: false,
  use_identity_composite_key_for_hashing: false,
  use_identity_overrides_in_local_eval: false,
  use_mv_v2_evaluation: false,
  use_v2_feature_versioning: false,
})
