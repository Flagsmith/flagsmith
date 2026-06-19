import React, { FC, useMemo } from 'react'
import Permission from 'common/providers/Permission'
import Utils from 'common/utils/utils'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import FeatureRow from 'components/feature-summary/FeatureRow'

type FeaturePermalinkHandlerProps = {
  featureId: number
  projectId: number
  environmentApiKey: string
  environmentId: number
  minimumChangeRequestApprovals?: number | null
  experimentMode?: boolean
}

/**
 * Opens the feature panel for a permalinked feature (`?feature=<id>`) that is not
 * present on the current page of results.
 *
 * `FeatureRow` opens the panel from its own effect when the feature id in the URL
 * matches its feature, but rows are only rendered for the current page. For a
 * feature on a later page no row exists, so the permalink would otherwise be a
 * no-op and the user would simply land on the first page (see #4239).
 *
 * Here we fetch the feature (and its environment feature state) directly and render
 * a single hidden `FeatureRow`, so the exact same panel-opening logic runs without
 * having to duplicate it.
 */
const FeaturePermalinkHandler: FC<FeaturePermalinkHandlerProps> = ({
  environmentApiKey,
  environmentId,
  experimentMode,
  featureId,
  minimumChangeRequestApprovals,
  projectId,
}) => {
  const { data: projectFlag } = useGetProjectFlagQuery({
    id: featureId,
    project: projectId,
  })
  const { data: featureStates } = useGetFeatureStatesQuery({
    environment: environmentId,
    feature: featureId,
  })

  const environmentFlags = useMemo(() => {
    const environmentFeatureState = featureStates?.results?.find(
      (featureState) => !featureState.feature_segment && !featureState.identity,
    )
    return environmentFeatureState
      ? { [featureId]: environmentFeatureState }
      : {}
  }, [featureStates, featureId])

  if (!projectFlag) {
    return null
  }

  return (
    <div className='d-none'>
      <Permission
        level='environment'
        tags={projectFlag.tags}
        permission={Utils.getManageFeaturePermission(
          Utils.changeRequestsEnabled(minimumChangeRequestApprovals),
        )}
        id={environmentApiKey}
      >
        {({ permission }) => (
          <FeatureRow
            environmentFlags={environmentFlags}
            permission={permission}
            environmentId={environmentApiKey}
            projectId={projectId}
            index={0}
            projectFlag={projectFlag}
            experimentMode={experimentMode}
          />
        )}
      </Permission>
    </div>
  )
}

export default FeaturePermalinkHandler
