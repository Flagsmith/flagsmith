import { useOnboardingFlag } from 'components/pages/onboarding/hooks/useOnboardingFlag'
import { makeEnvironment } from 'common/utils/__tests__/environmentFixture'
import type {
  Environment,
  FeatureState,
  FeatureStateValue,
  ProjectFlag,
} from 'common/types/responses'

// The featurestates endpoint returns the value typed, not flat as FeatureState says
type FeatureStateResponse = Omit<FeatureState, 'feature_state_value'> & {
  feature_state_value: FeatureStateValue
}

const flag: ProjectFlag = {
  code_references_counts: [],
  created_date: '2026-01-01T00:00:00Z',
  default_enabled: false,
  group_owners: [],
  id: 7,
  initial_value: 'control',
  is_archived: false,
  is_num_identity_overrides_complete: true,
  is_server_key_only: false,
  metadata: [],
  multivariate_options: [],
  name: 'show_demo_button',
  num_identity_overrides: null,
  num_segment_overrides: null,
  owners: [],
  project: 3,
  tags: [],
  type: 'MULTIVARIATE',
  uuid: 'flag-uuid',
}

const state: FeatureStateResponse = {
  created_at: '2026-01-01T00:00:00Z',
  enabled: false,
  environment: 5,
  environment_feature_version: 'version-uuid',
  feature: 7,
  feature_state_value: {
    boolean_value: null,
    integer_value: null,
    string_value: 'control',
    type: 'unicode',
  },
  id: 11,
  multivariate_feature_state_values: [],
  updated_at: '2026-01-01T00:00:00Z',
  uuid: 'state-uuid',
}

const v1Environment: Environment = makeEnvironment(5, 'Development')
const v2Environment: Environment = {
  ...v1Environment,
  use_v2_feature_versioning: true,
}

const updateFeatureState = jest.fn()
const createAndSetFeatureVersion = jest.fn()
const revertToggle = jest.fn()

// The hook only calls other hooks, so with those mocked it runs as a function
jest.mock('common/services/useProjectFlag', () => ({
  useGetProjectFlagsQuery: () => ({ data: { results: [flag] } }),
}))
jest.mock('common/services/useTag', () => ({
  useGetTagsQuery: () => ({ data: [] }),
}))
jest.mock('common/services/useFeatureState', () => ({
  useGetFeatureStatesQuery: () => ({ data: { results: [state] } }),
  useUpdateFeatureStateMutation: () => [updateFeatureState],
}))
jest.mock('common/services/useFeatureVersion', () => ({
  useCreateAndSetFeatureVersionMutation: () => [
    createAndSetFeatureVersion,
    { isLoading: false },
  ],
}))
// Utils pulls in the Flux stores, which Jest can't load
jest.mock('common/utils/utils', () => ({
  __esModule: true,
  default: {
    featureStateToValue: jest.requireActual('common/utils/featureStateToValue')
      .featureStateToValue,
  },
}))
jest.mock('components/pages/features/hooks/useFeatureRowState', () => ({
  useFeatureRowState: () => ({
    displayEnabled: false,
    isLoading: false,
    revertToggle,
    startToggle: () => true,
  }),
}))

const resolved = () => ({ unwrap: () => Promise.resolve() })

beforeEach(() => {
  updateFeatureState.mockReset().mockImplementation(resolved)
  createAndSetFeatureVersion.mockReset().mockImplementation(resolved)
  revertToggle.mockReset()
  Object.assign(global, { toast: jest.fn() })
})

describe('useOnboardingFlag toggle', () => {
  it('saves the feature state on a v1 environment', async () => {
    const { toggle } = useOnboardingFlag(v1Environment, flag.project, flag.name)

    expect(await toggle(true)).toBe(true)

    expect(updateFeatureState).toHaveBeenCalledWith({
      body: { enabled: true },
      environmentFlagId: state.id,
      environmentId: v1Environment.api_key,
    })
    expect(createAndSetFeatureVersion).not.toHaveBeenCalled()
  })

  it('creates a version with the flat value on a v2 environment', async () => {
    const { toggle } = useOnboardingFlag(v2Environment, flag.project, flag.name)

    expect(await toggle(true)).toBe(true)

    expect(createAndSetFeatureVersion).toHaveBeenCalledWith({
      environmentApiKey: v2Environment.api_key,
      environmentId: v2Environment.id,
      featureId: flag.id,
      featureStates: [
        { ...state, enabled: true, feature_state_value: 'control' },
      ],
      projectId: flag.project,
    })
    expect(updateFeatureState).not.toHaveBeenCalled()
    expect(revertToggle).not.toHaveBeenCalled()
  })

  it('reverts the switch and shows an error when the save fails', async () => {
    createAndSetFeatureVersion.mockImplementation(() => ({
      unwrap: () => Promise.reject(new Error('Bad request')),
    }))
    const { toggle } = useOnboardingFlag(v2Environment, flag.project, flag.name)

    expect(await toggle(true)).toBe(false)

    expect(revertToggle).toHaveBeenCalledTimes(1)
    expect(toast).toHaveBeenCalledWith(
      'Couldn’t update your flag. Please try again.',
      'danger',
    )
  })
})
