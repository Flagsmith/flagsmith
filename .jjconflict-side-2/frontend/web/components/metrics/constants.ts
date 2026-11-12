type ExtraMetrics = Record<string, { link?: string; tooltip?: string }>

type GetExtraMetricsFunc = (
  projectId: string,
  environmentId: string,
) => ExtraMetrics

export const getExtraMetricsData: GetExtraMetricsFunc = (
  projectId,
  environmentId,
) => {
  return {
    enabled_features: {
      tooltip: 'The number of features enabled for this environment',
    },
    identity_overrides: {
      link: `/project/${projectId}/environment/${environmentId}/identities`,
    },
    open_change_requests: {
      link: `/project/${projectId}/environment/${environmentId}/change-requests`,
    },
    segment_overrides: {
      link: `/project/${projectId}/segments`,
    },
  }
}
