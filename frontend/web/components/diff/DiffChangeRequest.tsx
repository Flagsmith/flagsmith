import { FC } from 'react'
import { ChangeRequest, ChangeRequestSummary } from 'common/types/responses'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import DiffFeature from './DiffFeature'

type DiffChangeRequestType = {
  changeRequest: ChangeRequest | null
  feature: number
  projectId: string
  isVersioned: boolean
}

const DiffChangeRequest: FC<DiffChangeRequestType> = ({
  changeRequest,
  feature,
  isVersioned,
  projectId,
}) => {
  const { data, isLoading } = useGetFeatureStatesQuery(
    {
      environment: changeRequest?.environment,
      feature,
    },
    { refetchOnMountOrArgChange: true, skip: !changeRequest },
  )
  if (!changeRequest) {
    return null
  }

  if (isLoading) {
    return (
      <div className='text-center'>
        <Loader />
      </div>
    )
  }
  return (
    <DiffFeature
      featureId={feature}
      disableSegments={!isVersioned}
      projectId={projectId}
      newState={changeRequest.feature_states}
      oldState={data?.results || []}
    />
  )
}

export default DiffChangeRequest
