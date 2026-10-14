import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'
import Utils from 'common/utils/utils'

export type ExperimentationFeature = {
  enabled: boolean
  isLoading: boolean
}

// Experimentation features need both their flag and the experimentation infra.
export function useHasExperimentationFeature(
  flag: string,
): ExperimentationFeature {
  const { data, isLoading } = useGetBuildVersionQuery({})
  return {
    enabled:
      Utils.getFlagsmithHasFeature(flag) &&
      !!data?.backend?.experimentation_enabled,
    isLoading,
  }
}
