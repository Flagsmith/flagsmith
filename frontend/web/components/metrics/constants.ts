type ExtraMetrics = Record<string, { link?: string; tooltip?: string }>

type GetExtraMetricsFunc = (
  projectId: string,
  environmentApiKey: string,
) => ExtraMetrics

export const getExtraMetricsData: GetExtraMetricsFunc = (
  projectId,
  environmentApiKey,
) => {
  return {
    enabled_features: {
      tooltip: 'The number of features enabled for this environment',
    },
    identity_overrides: {
      link: `/project/${projectId}/environment/${environmentApiKey}/identities`,
    },
    open_change_requests: {
      link: `/project/${projectId}/environment/${environmentApiKey}/change-requests`,
    },
    segment_overrides: {
      link: `/project/${projectId}/segments`,
    },
  }
}
