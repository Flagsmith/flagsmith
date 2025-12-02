import React, { FC } from 'react'
import EnvironmentMetricsList from 'components/metrics/EnvironmentMetricsList'
import Utils from 'common/utils/utils'

type FeatureMetricsSectionProps = {
  environmentApiKey?: string
  projectId: string
}

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
