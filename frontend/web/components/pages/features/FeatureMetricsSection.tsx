import React, { FC } from 'react'
import EnvironmentMetricsList from 'components/metrics/EnvironmentMetricsList'
import Utils from 'common/utils/utils'

type FeatureMetricsSectionProps = {
  environmentApiKey?: string
  projectId: string
}

/**
 * Wrapper for EnvironmentMetricsList with feature flag check
 *
 * Note: Metrics automatically refresh via RTK Query cache invalidation.
 * Feature mutations invalidate the METRICS tag, triggering automatic refetch.
 */
export const FeatureMetricsSection: FC<FeatureMetricsSectionProps> = ({
  environmentApiKey,
  projectId,
}) => {
  const environmentMetricsEnabled = Utils.getFlagsmithHasFeature(
    'environment_metrics',
  )

  if (!environmentMetricsEnabled) {
    return null
  }

  return (
    <EnvironmentMetricsList
      environmentApiKey={environmentApiKey}
      projectId={projectId}
    />
  )
}
