import React, { FC } from 'react'
import { useGetExperimentResultsQuery } from 'common/services/useExperimentResults'

type ExperimentResultsTabProps = {
  environmentId: string
  featureName: string
}

const ExperimentResultsTab: FC<ExperimentResultsTabProps> = ({
  environmentId,
  featureName,
}) => {
  const { data, error, isLoading } = useGetExperimentResultsQuery({
    environmentId,
    featureName,
  })

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  if (error || !data?.variants?.length) {
    return (
      <div className='text-center py-4'>
        Experiment is on-going, data should start appearing as soon as your
        users use it.
      </div>
    )
  }

  return (
    <div className='mt-2'>
      <pre>{JSON.stringify(data, null, 2)}</pre>
    </div>
  )
}

export default ExperimentResultsTab
