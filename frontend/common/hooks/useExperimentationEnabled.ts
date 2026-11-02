import { useGetBuildVersionQuery } from 'common/services/useBuildVersion'

export type ExperimentationEnabled = {
  enabled: boolean
  isLoading: boolean
}

export function useExperimentationEnabled(): ExperimentationEnabled {
  const { data, isLoading } = useGetBuildVersionQuery({})
  return {
    enabled: !!data?.backend?.experimentation_enabled,
    isLoading,
  }
}
