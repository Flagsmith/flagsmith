import {
  shouldRedirectMissingEnvironment,
  type ShouldRedirectMissingEnvironmentArgs,
} from 'common/utils/shouldRedirectMissingEnvironment'

const buildArgs = (
  overrides?: Partial<ShouldRedirectMissingEnvironmentArgs>,
): ShouldRedirectMissingEnvironmentArgs => ({
  envByIdError: undefined,
  environmentId: 'real-key',
  environmentsData: { results: [{ api_key: 'real-key' }] },
  hasEnvironmentId: true,
  hasRedirected: false,
  isLoadingEnvById: false,
  isLoadingEnvironments: false,
  ...overrides,
})

describe('shouldRedirectMissingEnvironment', () => {
  it('returns false when the environmentId matches an entry in the loaded list', () => {
    expect(shouldRedirectMissingEnvironment(buildArgs())).toBe(false)
  })

  it('returns true when the loaded environments list does not include the environmentId', () => {
    const result = shouldRedirectMissingEnvironment(
      buildArgs({
        environmentId: 'undefined',
        environmentsData: { results: [{ api_key: 'real-key' }] },
      }),
    )

    expect(result).toBe(true)
  })

  it('returns true when the per-environment query returns a 404', () => {
    const result = shouldRedirectMissingEnvironment(
      buildArgs({
        envByIdError: { status: 404 },
        environmentId: 'stale-key',
        environmentsData: { results: [{ api_key: 'real-key' }] },
      }),
    )

    expect(result).toBe(true)
  })

  it('returns false on non-404 errors (e.g. 500)', () => {
    const result = shouldRedirectMissingEnvironment(
      buildArgs({
        envByIdError: { status: 500 },
        environmentsData: { results: [{ api_key: 'real-key' }] },
      }),
    )

    expect(result).toBe(false)
  })

  it('returns false while either query is still loading', () => {
    const stillLoadingList = shouldRedirectMissingEnvironment(
      buildArgs({
        environmentId: 'undefined',
        environmentsData: undefined,
        isLoadingEnvironments: true,
      }),
    )
    const stillLoadingEnvById = shouldRedirectMissingEnvironment(
      buildArgs({
        envByIdError: { status: 404 },
        isLoadingEnvById: true,
      }),
    )

    expect(stillLoadingList).toBe(false)
    expect(stillLoadingEnvById).toBe(false)
  })

  it('returns false when the URL has no environmentId (e.g. project-level routes)', () => {
    const result = shouldRedirectMissingEnvironment(
      buildArgs({ hasEnvironmentId: false }),
    )

    expect(result).toBe(false)
  })

  it('returns false when the project has zero environments (let create-flow handle it)', () => {
    const result = shouldRedirectMissingEnvironment(
      buildArgs({
        environmentId: 'undefined',
        environmentsData: { results: [] },
      }),
    )

    expect(result).toBe(false)
  })

  it('returns false after a redirect has already been issued (ref guard)', () => {
    const result = shouldRedirectMissingEnvironment(
      buildArgs({
        envByIdError: { status: 404 },
        environmentId: 'undefined',
        environmentsData: { results: [{ api_key: 'real-key' }] },
        hasRedirected: true,
      }),
    )

    expect(result).toBe(false)
  })

  it('returns false for an undefined error object', () => {
    const result = shouldRedirectMissingEnvironment(
      buildArgs({ envByIdError: undefined }),
    )

    expect(result).toBe(false)
  })
})
