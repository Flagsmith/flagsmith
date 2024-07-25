import { FC, useMemo } from 'react'
import { ChangeRequest } from 'common/types/responses'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import DiffFeature from './DiffFeature'
import { mergeChangeSets } from 'common/services/useChangeRequest'

type DiffChangeRequestType = {
  changeRequest: ChangeRequest | null
  feature: number
  projectId: string
  environmentId: string
  isVersioned: boolean
}
const DiffChangeRequest: FC<DiffChangeRequestType> = ({
  changeRequest,
  environmentId,
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

  const newState = useMemo(() => {
    const changeSets = changeRequest?.change_sets?.filter(
      (v) => v.feature === feature,
    )
    if (!changeSets?.length) {
      return changeRequest?.feature_states
    }
    return mergeChangeSets(changeSets, data?.results, changeRequest?.conflicts)
  }, [changeRequest, feature, data])

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
      conflicts={changeRequest.conflicts}
      environmentId={environmentId}
      featureId={feature}
      disableSegments={!isVersioned}
      projectId={projectId}
      newState={newState || []}
      oldState={data?.results || []}
    />
  )
}

export default DiffChangeRequest
