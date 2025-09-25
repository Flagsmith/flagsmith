import React from 'react'
import { useGetHealthEventsQuery } from 'common/services/useHealthEvents'
import {} from 'common/types/responses'
import { useGetHealthProvidersQuery } from 'common/services/useHealthProvider'
import FeatureHealthEventsList from './components/FeatureHealthEventsList'
import EmptyFeatureHealthProviders from './components/EmptyFeatureHealthProviders'

type FeatureHealthTabContentProps = {
  projectId: number
  environmentId: number
  featureId: number
}

const FeatureHealthTabContent: React.FC<FeatureHealthTabContentProps> = ({
  environmentId,
  featureId,
  projectId,
}) => {
  const { data: healthEvents, isLoading } = useGetHealthEventsQuery(
    { projectId: String(projectId) },
    { skip: !projectId },
  )

  const { data: providers, isLoading: isLoadingProviders } =
    useGetHealthProvidersQuery({ projectId: projectId })

  if (isLoading || isLoadingProviders) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }

  const hasFeatureHealthConfigured = providers && providers?.length > 0

  return (
    <div>
      {hasFeatureHealthConfigured ? (
        <FeatureHealthEventsList
          featureHealthEvents={healthEvents || []}
          projectId={projectId}
          environmentId={environmentId}
          featureId={featureId}
        />
      ) : (
        <EmptyFeatureHealthProviders projectId={projectId} />
      )}
    </div>
  )
}

export default FeatureHealthTabContent
