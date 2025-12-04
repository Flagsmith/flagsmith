import React, { FC } from 'react'
import EnvironmentMetricsList from 'components/metrics/EnvironmentMetricsList'
import Utils from 'common/utils/utils'

type FeatureMetricsSectionProps = {
  environmentId?: string
  projectId: number
}

export const FeatureMetricsSection: FC<FeatureMetricsSectionProps> = ({
  environmentId,
  projectId,
}) => {
  const environmentMetricsEnabled = Utils.getFlagsmithHasFeature(
    'environment_metrics',
  )

  if (!environmentMetricsEnabled || !environmentId) {
    return null
  }

  return (
    <EnvironmentMetricsList
      environmentId={environmentId}
      projectId={projectId}
    />
  )
}
