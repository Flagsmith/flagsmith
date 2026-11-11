import { skipToken } from '@reduxjs/toolkit/query'
import { useGetChangeRequestQuery } from 'common/services/useChangeRequest'
import { useGetEnvironmentFeatureStateQuery } from 'common/services/useFeatureState'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { getChangeRequestFeature } from 'common/utils/getChangeRequestFeature'
import { isNotFoundError, toErrorMessage } from 'common/utils/requestError'

type ChangeRequestDetailParams = {
  environmentId: string
  id: string
  projectId: string
}

// Refetch after an action, not on window focus
const options = { refetchOnFocus: false }

export const useChangeRequestDetail = ({
  environmentId,
  id,
  projectId,
}: ChangeRequestDetailParams) => {
  const changeRequest = useGetChangeRequestQuery({ id }, options)
  const feature = getChangeRequestFeature(changeRequest.data)
  const projectFlag = useGetProjectFlagQuery(
    feature ? { id: feature, project: Number(projectId) } : skipToken,
    options,
  )
  const featureState = useGetEnvironmentFeatureStateQuery(
    feature ? { environmentId, feature } : skipToken,
    options,
  )

  // A 404 means the feature was deleted since, which the page explains
  const featureDeleted = !feature || isNotFoundError(projectFlag.error)
  const flagsLoaded =
    featureDeleted || (!!projectFlag.data && featureState.data !== undefined)
  const lookupError = featureDeleted
    ? undefined
    : projectFlag.error || featureState.error

  return {
    // Held back until the flags arrive, so the page renders once
    changeRequest: flagsLoaded ? changeRequest.data : undefined,
    environmentFlag: featureDeleted
      ? undefined
      : featureState.data ?? undefined,
    isFetching:
      changeRequest.isFetching ||
      projectFlag.isFetching ||
      featureState.isFetching,
    loadError: toErrorMessage(changeRequest.error || lookupError),
    notFound: !changeRequest.data && isNotFoundError(changeRequest.error),
    projectFlag: featureDeleted ? undefined : projectFlag.data,
  }
}
