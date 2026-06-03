import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import { useToggleFeatureWithToast } from 'web/components/pages/features/hooks/useToggleFeatureWithToast'
import { Environment } from 'common/types/responses'

type UseOnboardingFlagToggleArgs = {
  projectId: number | null
  environment: Environment | null
  featureName: string
}

type OnboardingFlagToggle = {
  enabled: boolean
  isReady: boolean
  isLoading: boolean
  toggle: () => void
}

/**
 * Backs the single-page flag toggle with the *real* flag, so it never lies:
 * its state reflects the flag's actual `enabled` value in the Development
 * environment, and flipping it persists to Flagsmith (the same code path the
 * features page uses, including v2 feature versioning). That's what makes the
 * page's promise — "flip it and your app changes, no deploy" — true rather
 * than a cosmetic switch.
 */
export const useOnboardingFlagToggle = ({
  environment,
  featureName,
  projectId,
}: UseOnboardingFlagToggleArgs): OnboardingFlagToggle => {
  const { data: projectFlags, refetch } = useGetProjectFlagsQuery(
    {
      environment: environment?.id,
      project: `${projectId}`,
    },
    { skip: !projectId || !environment },
  )
  const [toggleWithToast, { isLoading }] = useToggleFeatureWithToast()

  const flag = projectFlags?.results?.find((f) => f.name === featureName)
  const environmentFlag = flag?.environment_feature_state
  const enabled = !!environmentFlag?.enabled

  const toggle = () => {
    if (!flag || !environment) {
      return
    }
    toggleWithToast(flag, environmentFlag, environment, {
      errorMessage: `Couldn’t toggle ${featureName}. Please try again.`,
      onSuccess: () => refetch(),
      successMessage: `${featureName} is now ${enabled ? 'off' : 'on'}.`,
    })
  }

  return {
    enabled,
    isLoading,
    isReady: !!flag && !!environment,
    toggle,
  }
}
