import { FC } from 'react'
import { ChangeRequest, ChangeRequestSummary } from 'common/types/responses'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import DiffFeature from './DiffFeature'

type DiffChangeRequestType = {
  changeRequest: ChangeRequest | null
  feature: number
  projectId: string
}

const DiffChangeRequest: FC<DiffChangeRequestType> = ({
  changeRequest,
  feature,
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
    <div className='col-md-8'>
      <DiffFeature
        featureId={feature}
        projectId={projectId}
        newState={changeRequest.feature_states}
        oldState={data?.results || []}
      />
    </div>
  )
}

export default DiffChangeRequest
