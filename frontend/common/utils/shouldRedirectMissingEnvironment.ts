/**
 * Pure helper that decides whether the EnvironmentReadyChecker should redirect
 * away from a URL whose environment identifier does not correspond to a real
 * environment for the current project. See Flagsmith#7446.
 *
 * Both signals are combined defensively:
 *
 *   - `envListLoadedAndMissing` is the fast path: once the environments list
 *     for the project has loaded, we can tell immediately that the URL's
 *     `environmentId` (treated as an `api_key`) is not in it.
 *
 *   - `envByIdReturned404` is the belt-and-braces path: if the per-environment
 *     query returns a 404 (e.g. when the list cache is stale after permission
 *     changes), we redirect even when the list hasn't yet resolved.
 *
 * The helper does no IO and renders nothing — testing it does not require a
 * DOM. The calling component is responsible for invoking `history.replace`.
 */

type EnvironmentLike = {
  api_key: string
}

type EnvironmentsListLike = {
  results?: EnvironmentLike[]
}

export type ShouldRedirectMissingEnvironmentArgs = {
  hasEnvironmentId: boolean
  hasRedirected: boolean
  isLoadingEnvironments: boolean
  isLoadingEnvById: boolean
  environmentsData: EnvironmentsListLike | undefined
  environmentId: string | undefined
  envByIdError: unknown
}

const is404Error = (error: unknown): boolean => {
  if (!error || typeof error !== 'object') {
    return false
  }
  const status = (error as { status?: unknown }).status
  return status === 404
}

export const shouldRedirectMissingEnvironment = ({
  envByIdError,
  environmentId,
  environmentsData,
  hasEnvironmentId,
  hasRedirected,
  isLoadingEnvById,
  isLoadingEnvironments,
}: ShouldRedirectMissingEnvironmentArgs): boolean => {
  if (hasRedirected) return false
  if (!hasEnvironmentId) return false
  if (isLoadingEnvironments || isLoadingEnvById) return false

  const envList = environmentsData?.results ?? []
  const envListLoadedAndMissing =
    !!environmentsData &&
    envList.length > 0 &&
    !envList.some((env) => env.api_key === environmentId)

  const envByIdReturned404 = is404Error(envByIdError)

  return envListLoadedAndMissing || envByIdReturned404
}
