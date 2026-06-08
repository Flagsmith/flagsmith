import {
  useCreateProjectFlagMutation,
  useGetProjectFlagsQuery,
  useRemoveProjectFlagMutation,
} from 'common/services/useProjectFlag'
import { useToggleFeatureWithToast } from 'web/components/pages/features/hooks/useToggleFeatureWithToast'
import { Environment } from 'common/types/responses'
import { Req } from 'common/types/requests'

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
  // "Rename" the flag. Feature names are immutable once created, so this is a
  // delete + recreate under the hood. Resolves true on success. Safe at
  // onboarding: the flag is freshly created and not yet depended on.
  rename: (name: string) => Promise<boolean>
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
  const [createProjectFlag] = useCreateProjectFlagMutation()
  const [removeProjectFlag] = useRemoveProjectFlagMutation()

  const flag = projectFlags?.results?.find((f) => f.name === featureName)
  const environmentFlag = flag?.environment_feature_state
  const enabled = !!environmentFlag?.enabled

  const rename = async (name: string): Promise<boolean> => {
    if (!flag || projectId === null || name === flag.name) {
      return false
    }
    try {
      // Recreate first (names differ, so no unique conflict), then drop the
      // old one — so a flag always exists even if the second call fails.
      await createProjectFlag({
        body: {
          name,
          project: projectId,
          type: 'STANDARD',
        } as Req['createProjectFlag']['body'],
        project_id: projectId,
      }).unwrap()
      await removeProjectFlag({
        flag_id: flag.id,
        project_id: projectId,
      }).unwrap()
      refetch()
      return true
    } catch {
      return false
    }
  }

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
    rename,
    toggle,
  }
}
