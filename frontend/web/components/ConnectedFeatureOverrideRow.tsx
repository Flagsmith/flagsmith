import React, { FC } from 'react'
import { useGetProjectFlagQuery } from 'common/services/useProjectFlag'
import { useGetFeatureStatesQuery } from 'common/services/useFeatureState'
import FeatureOverrideRow from './feature-override/FeatureOverrideRow'
import Utils from 'common/utils/utils'

type ConnectedFeatureOverrideRowProps = {
  featureId: number
  projectId: number
  environmentId: string
  environmentIdNumeric: number
  segmentId: number
  shouldPreselect?: boolean
  level?: 'segment' | 'identity'
  index: number
  openInNewTab?: boolean
}

const ConnectedFeatureOverrideRow: FC<ConnectedFeatureOverrideRowProps> = ({
  environmentId,
  environmentIdNumeric,
  featureId,
  index,
  level = 'segment',
  openInNewTab = false,
  projectId,
  segmentId,
  shouldPreselect,
}) => {
  const { data: projectFlag, isLoading: flagLoading } = useGetProjectFlagQuery({
    id: featureId,
    project: projectId,
  })

  const { data: featureStates, isLoading: statesLoading } =
    useGetFeatureStatesQuery({
      environment: environmentIdNumeric,
      feature: featureId,
    })

  if (flagLoading || statesLoading || !projectFlag || !featureStates) {
    return (
      <div className='list-item py-3'>
        <Loader />
      </div>
    )
  }

  const _environmentFeatureState = featureStates.results.find(
    (fs) => !fs.feature_segment,
  )
  const _segmentFeatureState = featureStates.results.find(
    (fs) => fs.feature_segment?.segment === segmentId,
  )
  const environmentFeatureState = _environmentFeatureState
    ? {
        ..._environmentFeatureState,
        feature_state_value: Utils.featureStateToValue(
          _environmentFeatureState.feature_state_value,
        ),
      }
    : _environmentFeatureState
  const segmentFeatureState = _segmentFeatureState
    ? {
        ..._segmentFeatureState,
        feature_state_value: Utils.featureStateToValue(
          _segmentFeatureState.feature_state_value,
        ),
      }
    : _segmentFeatureState

  const handleClick = () => {
    if (openInNewTab) {
      window.open(
        `/project/${projectId}/environment/${environmentId}/features?feature=${featureId}`,
        '_blank',
      )
    }
  }

  if (!environmentFeatureState) {
    return null
  }
  return (
    <div
      className='rounded border-1'
      onClick={openInNewTab ? handleClick : undefined}
    >
      <FeatureOverrideRow
        shouldPreselect={shouldPreselect}
        environmentId={environmentId}
        level={level}
        valueDataTest={`user-feature-value-${index}`}
        projectFlag={projectFlag}
        dataTest={`user-feature-${index}`}
        overrideFeatureState={segmentFeatureState || environmentFeatureState}
        environmentFeatureState={environmentFeatureState}
        highlightSegmentId={segmentId}
      />
    </div>
  )
}

export default ConnectedFeatureOverrideRow
