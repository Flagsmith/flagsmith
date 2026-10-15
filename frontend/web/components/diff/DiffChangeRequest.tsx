import { FC, useMemo } from 'react'
import { ChangeRequest } from 'common/types/responses'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import DiffFeature from './DiffFeature'
import { mergeChangeSets } from 'common/services/useChangeRequest'
import { useFeatureStates } from 'common/hooks/useFeatureStates'
import { useDependencyChanges } from 'components/feature-dependencies/useDependencyChanges'

type DiffChangeRequestType = {
  changeRequest: ChangeRequest | null
  feature: number
  projectId: string
  identity: number | null
  environmentId: string
  isVersioned: boolean
}
const DiffChangeRequest: FC<DiffChangeRequestType> = ({
  changeRequest,
  environmentId,
  feature,
  identity = null,
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

  const dependencies = useDependencyChanges({
    changeRequestId: changeRequest?.id ?? 0,
    environmentId,
    featureId: feature,
    // The API refuses to list a published change request's dependencies.
    skip:
      !changeRequest ||
      changeRequest.is_committed ||
      !Utils.getFlagsmithHasFeature('flag_dependencies_change_requests'),
  })
  // Whether each prerequisite is on now, so a reviewer can see an added one
  // that would hold this feature off.
  const states = useFeatureStates({
    environmentId,
    projectId: Number(projectId),
  })

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
      dependencies={{
        ...dependencies,
        // Until the states are known, no column rather than every row "No".
        isEnabled:
          states.isLoading || states.isError ? undefined : states.isEnabled,
      }}
      environmentId={environmentId}
      featureId={feature}
      disableSegments={!isVersioned}
      projectId={projectId}
      newState={newState || []}
      oldState={data?.results?.filter((v) => v.identity === identity) || []}
    />
  )
}

export default DiffChangeRequest
