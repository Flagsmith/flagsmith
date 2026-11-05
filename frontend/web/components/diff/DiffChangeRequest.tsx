import { FC, useMemo } from 'react'
import { ChangeRequest } from 'common/types/responses'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import DiffFeature from './DiffFeature'
import { mergeChangeSets } from 'common/services/useChangeRequest'
import { useFeatureStates } from 'common/hooks/useFeatureStates'
import { useDependencyChanges } from 'components/feature-dependencies/useDependencyChanges'
import { useHasPermission } from 'common/providers/Permission'
import { EnvironmentPermission } from 'common/types/permissions.types'

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

  // The API lists a change request's dependencies only to those who can
  // create change requests.
  const { permission: canCreateChangeRequest } = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: EnvironmentPermission.CREATE_CHANGE_REQUEST,
  })
  const skipDependencies =
    !changeRequest ||
    // The API rejects these.
    changeRequest.is_committed ||
    !isVersioned ||
    !canCreateChangeRequest ||
    !Utils.getFlagsmithHasFeature('flag_dependencies') ||
    !Utils.getFlagsmithHasFeature('flag_dependencies_change_requests')
  const dependencies = useDependencyChanges({
    changeRequestId: changeRequest?.id ?? 0,
    environmentId,
    featureId: feature,
    skip: skipDependencies,
  })
  // Shows if an added prerequisite is off.
  const states = useFeatureStates({
    environmentId,
    projectId: Number(projectId),
    skip: skipDependencies,
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
