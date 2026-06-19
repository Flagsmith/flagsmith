import { FC } from 'react'
import { useHistory, useParams } from 'react-router-dom'
import Utils from 'common/utils/utils'
import { useGetExperimentQuery } from 'common/services/useExperiment'
import ExperimentDetailHeader from 'components/experiments/results/ExperimentDetailHeader'
import ExperimentConfiguration from 'components/experiments/results/ExperimentConfiguration'
import ExperimentExposuresPanel from 'components/experiments/results/ExperimentExposuresPanel'

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

  return (
    <div className='app-container container mt-4'>
      <ExperimentDetailHeader
        environmentId={environmentId}
        experiment={experiment}
      />
      <ExperimentConfiguration experiment={experiment} />

      {experiment.status !== 'created' && (
        <>
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
