import { useGetProjectFlagsQuery } from 'common/services/useProjectFlag'
import {
  useGetFeatureStatesQuery,
  useUpdateFeatureStateMutation,
} from 'common/services/useFeatureState'
import { useGetTagsQuery } from 'common/services/useTag'
import { Environment, Tag } from 'common/types/responses'
import { useFeatureRowState } from 'components/pages/features/hooks/useFeatureRowState'

// Resolves the demo flag (by name, since bootstrap returns the name) and its
// Dev feature state, exposing a persisted toggle and the flag's tags.
export const useOnboardingFlag = (
  environment: Environment | null,
  projectId: number | null,
  featureName: string,
) => {
  const { data: flags } = useGetProjectFlagsQuery(
    { project: `${projectId}` },
    { skip: !projectId },
  )
  const flag = flags?.results?.find((f) => f.name === featureName)

  const { data: projectTags } = useGetTagsQuery(
    { projectId: projectId ?? 0 },
    { skip: !projectId },
  )
  const tags = (flag?.tags ?? [])
    .map((id) => projectTags?.find((tag) => tag.id === id))
    .filter((tag): tag is Tag => !!tag)

  const { data: states } = useGetFeatureStatesQuery(
    { environment: environment?.id, feature: flag?.id },
    { skip: !environment || !flag },
  )
  const state = states?.results?.[0]

  const [updateFeatureState] = useUpdateFeatureStateMutation()

  // Optimistic (like the product row): displayEnabled flips instantly and
  // reverts on failure, instead of waiting on the update + refetch.
  const { displayEnabled, isLoading, revertToggle, startToggle } =
    useFeatureRowState(state?.enabled)

  const toggle = async (enabled: boolean) => {
    if (!environment || !state || !startToggle(enabled)) {
      return
    }
    try {
      await updateFeatureState({
        body: { enabled },
        environmentFlagId: state.id,
        environmentId: environment.api_key,
      }).unwrap()
    } catch {
      revertToggle()
      toast('Couldn’t update your flag. Please try again.', 'danger')
    }
  }

  return {
    enabled: !!displayEnabled,
    isToggling: isLoading,
    ready: !!state,
    tags,
    toggle,
  }
}
