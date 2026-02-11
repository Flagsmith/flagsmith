import { FC, useEffect } from 'react'
import { useGetEnvironmentAnalyticsQuery } from 'common/services/useFeatureAnalytics'

type EvaluationCheckerProps = {
  featureId: number
  projectId: number
  environmentId: string
  period: number
  onResult: (featureId: number, envId: string, hasEvaluations: boolean) => void
}

const EvaluationChecker: FC<EvaluationCheckerProps> = ({
  environmentId,
  featureId,
  onResult,
  period,
  projectId,
}) => {
  const { data, isSuccess } = useGetEnvironmentAnalyticsQuery({
    environment_id: environmentId,
    feature_id: featureId,
    period,
    project_id: projectId,
  })

  useEffect(() => {
    if (isSuccess && data) {
      const total = data.reduce((sum, entry) => sum + entry.count, 0)
      onResult(featureId, environmentId, total > 0)
    }
  }, [data, isSuccess, featureId, environmentId, onResult])

  return null
}

export default EvaluationChecker
