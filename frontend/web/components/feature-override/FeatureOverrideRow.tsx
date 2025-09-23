import classNames from 'classnames'
import { FC, ReactNode } from 'react'
import {
  FeatureState,
  IdentityFeatureState,
  ProjectFlag,
} from 'common/types/responses'
import FeatureName from 'components/feature-summary/FeatureName'
import FeatureValue from 'components/feature-summary/FeatureValue'
import IdentityOverrideDescription from './IdentityOverrideDescription'
import MultivariateOverrideDescription from './MultivariateOverrideDescription'
import SegmentOverrideDescription from './SegmentOverrideDescription'
import Switch from 'components/Switch'
import TagValues from 'components/tags/TagValues'
import Tooltip from 'components/Tooltip'
import Utils from 'common/utils/utils'
import featureValuesEqual from 'common/featureValuesEqual'
import { getViewMode } from 'common/useViewMode'

const width = [200, 48, 78]

type FeatureOverrideRowType = {
  dataTest: string
  onClick: () => void
  hasOverride?: boolean
  onToggle?: () => void
  hasUserOverride?: boolean
  hasSegmentOverride?: boolean
  cta?: ReactNode
  valueDataTest?: string
  toggleDataTest?: string
  projectFlag: ProjectFlag
  editPermission: boolean
  editPermissionDescription: string
  environmentFeatureState: FeatureState
  overrideFeatureState: FeatureState | IdentityFeatureState | null | undefined
}

const FeatureOverrideRow: FC<FeatureOverrideRowType> = ({
  cta,
  dataTest,
  editPermission,
  editPermissionDescription,
  environmentFeatureState,
  hasSegmentOverride,
  hasUserOverride,
  onClick,
  onToggle,
  overrideFeatureState,
  projectFlag,
  toggleDataTest,
  valueDataTest,
}) => {
  if (!environmentFeatureState || !projectFlag) {
    return null
  }
  const name = projectFlag.name
  const projectId = projectFlag.project
  const featureId = projectFlag.id
  const isCompact = getViewMode() === 'compact'
  const flagEnabled = environmentFeatureState.enabled
  const flagValue = environmentFeatureState.feature_state_value
  const actualEnabled = overrideFeatureState?.enabled
  const actualValue = overrideFeatureState?.feature_state_value
  const description = projectFlag.description
  const flagEnabledDifferent =
    !!overrideFeatureState && actualEnabled !== flagEnabled
  const flagValueDifferent =
    !!overrideFeatureState && !featureValuesEqual(actualValue, flagValue)
  const hasOverride = flagEnabledDifferent || flagValueDifferent

  const showMultivariateOverride =
    !hasUserOverride &&
    !!flagValueDifferent &&
    !!projectFlag?.multivariate_options?.find(
      (v: any) => Utils.featureStateToValue(v) === actualValue,
    )

  const showSegmentOverride =
    hasSegmentOverride && !hasUserOverride && !showMultivariateOverride
  return (
    <div
      className={classNames(
        `flex-row space list-item clickable py-2`,
        {
          'bg-primary-opacity-5':
            !!overrideFeatureState && (hasOverride || hasSegmentOverride),
        },
        {
          'list-item-xs':
            isCompact && !flagEnabledDifferent && !flagValueDifferent,
        },
      )}
      key={featureId}
      data-test={dataTest}
      onClick={onClick}
    >
      <Flex className='table-column pt-0'>
        <div>
          <Flex>
            <div className='d-flex align-items-center'>
              <Tooltip title={<FeatureName name={name} />}>
                {description}
              </Tooltip>
              <TagValues projectId={`${projectId}`} value={projectFlag!.tags} />
            </div>
            {hasUserOverride && <IdentityOverrideDescription />}
            {showMultivariateOverride && (
              <MultivariateOverrideDescription controlValue={flagValue} />
            )}
            {showSegmentOverride && (
              <SegmentOverrideDescription
                showEnabledOverride={flagEnabledDifferent}
                showValueOverride={!flagEnabledDifferent}
                controlEnabled={flagEnabled}
                controlValue={flagValue}
              />
            )}
            {getViewMode() === 'default' && !hasUserOverride && (
              <div className='list-item-subtitle'>
                Using environment defaults
              </div>
            )}
          </Flex>
        </div>
      </Flex>
      <div className='table-column' style={{ width: width[0] }}>
        <FeatureValue data-test={valueDataTest} value={actualValue!} />
      </div>
      <div
        className='table-column'
        style={{ width: width[1] }}
        onClick={(e) => e.stopPropagation()}
      >
        {Utils.renderWithPermission(
          editPermission,
          editPermissionDescription,
          <Switch
            disabled={!editPermission}
            data-test={toggleDataTest}
            checked={actualEnabled}
            onChange={onToggle}
          />,
        )}
      </div>
      <div
        className='table-column p-0'
        style={{ width: width[2] }}
        onClick={(e) => e.stopPropagation()}
      >
        {cta}
      </div>
    </div>
  )
}

export default FeatureOverrideRow
