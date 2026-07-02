import { FC } from 'react'
import { useHistory, useParams } from 'react-router-dom'
import Utils from 'common/utils/utils'
import {
  useGetExperimentBayesianResultsQuery,
  useGetExperimentExposuresQuery,
  useGetExperimentQuery,
} from 'common/services/useExperiment'
import { getHeadlineTotal } from 'components/experiments/results/derive'
import ExperimentDetailHeader from 'components/experiments/results/ExperimentDetailHeader'
import ExperimentConfiguration from 'components/experiments/results/ExperimentConfiguration'
import ExperimentRecommendation from 'components/experiments/results/ExperimentRecommendation'
import ExperimentSummaryScorecard from 'components/experiments/results/ExperimentSummaryScorecard'
import ExperimentMetricScorecard from 'components/experiments/results/ExperimentMetricScorecard'
import ExperimentExposuresPanel from 'components/experiments/results/ExperimentExposuresPanel'
import ExperimentResultsRefreshControl from 'components/experiments/results/ExperimentResultsRefreshControl'

type ExperimentDetailParams = {
  projectId: string
  environmentId: string
  experimentId: string
}

const ExperimentDetailPage: FC = () => {
  const { environmentId, experimentId, projectId } =
    useParams<ExperimentDetailParams>()
  const history = useHistory()
  const numericId = Number(experimentId)
  const hasFeature = Utils.getFlagsmithHasFeature('experimental_flags')

  const {
    data: experiment,
    isError,
    isLoading,
  } = useGetExperimentQuery(
    { environmentId, experimentId: numericId },
    { refetchOnMountOrArgChange: true, skip: !hasFeature },
  )

  const { data: exposures } = useGetExperimentExposuresQuery(
    { environmentId, experimentId: numericId },
    { skip: !hasFeature },
  )

  const { data: bayesianResults } = useGetExperimentBayesianResultsQuery(
    { environmentId, experimentId: numericId },
    { skip: !hasFeature },
  )

  const results = bayesianResults?.payload ?? undefined

  if (!hasFeature) {
    history.replace(
      `/project/${projectId}/environment/${environmentId}/features`,
    )
    return null
  }

  if (isLoading) {
    return (
      <div className='app-container container'>
        <div className='text-center py-5'>
          <Loader />
        </div>
      </div>
    )
  }

  if (isError || !experiment) {
    return (
      <div className='app-container container'>
        <div className='alert alert-danger'>
          We couldn't load this experiment.
        </div>
      </div>
    )
  }

  const usersEnrolled = exposures?.payload
    ? getHeadlineTotal(exposures.payload)
    : null

  return (
    <div className='app-container container mt-4'>
      <ExperimentDetailHeader
        environmentId={environmentId}
        experiment={experiment}
      />
      {experiment.status !== 'created' && (
        <ExperimentRecommendation experiment={experiment} results={results} />
      )}
      <ExperimentConfiguration
        experiment={experiment}
        environmentId={environmentId}
      />

      {experiment.status !== 'created' && (
        <>
          <div className='d-flex justify-content-between align-items-center mb-3 mt-5'>
            <h5 className='mb-0'>Results</h5>
            <ExperimentResultsRefreshControl
              environmentId={environmentId}
              experimentId={numericId}
              status={experiment.status}
            />
          </div>
          <ExperimentSummaryScorecard
            experiment={experiment}
            results={results}
            usersEnrolled={usersEnrolled}
          />

          <h5 className='mb-3 mt-5'>Analysis</h5>
          <ExperimentMetricScorecard
            experiment={experiment}
            results={results}
          />

          <h5 className='mb-3 mt-5'>Exposures</h5>
          <ExperimentExposuresPanel
            environmentId={environmentId}
            experiment={experiment}
          />
        </>
      )}
    </div>
  )
}

export default ExperimentDetailPage
