import classNames from 'classnames'
import React, { FC, ReactNode, useMemo } from 'react'
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

const COLUMN_WIDTHS = [200, 48, 78]

type FeatureOverrideRowProps = {
  dataTest: string
  onClick: () => void
  onToggle?: () => void
  cta?: ReactNode
  valueDataTest?: string
  toggleDataTest?: string
  projectFlag: ProjectFlag
  editPermission: boolean
  editPermissionDescription: string
  environmentFeatureState: FeatureState
  overrideFeatureState?: FeatureState | IdentityFeatureState | null
  hasUserOverride?: boolean
  hasSegmentOverride?: boolean
}

const FeatureOverrideRow: FC<FeatureOverrideRowProps> = ({
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
  const viewMode = getViewMode()
  const isCompact = viewMode === 'compact'
  const showDefaultsHint = viewMode === 'default' && !hasUserOverride

  const { description, id: featureId, name, project: projectId } = projectFlag
  const flagEnabled = environmentFeatureState.enabled
  const flagValue = environmentFeatureState.feature_state_value
  const actualEnabled = overrideFeatureState?.enabled ?? flagEnabled
  const actualValue = overrideFeatureState?.feature_state_value ?? flagValue

  const { hasAnyOverride, hasEnabledDiff, hasValueDiff } = useMemo(() => {
    const enabledDiff = overrideFeatureState
      ? actualEnabled !== flagEnabled
      : false
    const valueDiff = overrideFeatureState
      ? !featureValuesEqual(actualValue, flagValue)
      : false
    return {
      hasAnyOverride: enabledDiff || valueDiff || hasUserOverride,
      hasEnabledDiff: enabledDiff,
      hasValueDiff: valueDiff,
    }
  }, [
    overrideFeatureState,
    actualEnabled,
    actualValue,
    flagEnabled,
    flagValue,
    hasUserOverride,
  ])

  const showMultivariateOverride = useMemo(() => {
    if (hasUserOverride || !hasValueDiff) return false
    return !!projectFlag?.multivariate_options?.some(
      (opt: any) => Utils.featureStateToValue(opt) === actualValue,
    )
  }, [hasUserOverride, hasValueDiff, projectFlag, actualValue])

  const showSegment =
    hasSegmentOverride && !hasUserOverride && !showMultivariateOverride
  const stopPropagation = (e: React.MouseEvent) => e.stopPropagation()
  if (!environmentFeatureState || !projectFlag) return null

  return (
    <div
      className={classNames('flex-row space list-item clickable py-2', {
        'bg-primary-opacity-5':
          !!overrideFeatureState && (hasAnyOverride || hasSegmentOverride),
        'list-item-xs': isCompact && !hasEnabledDiff && !hasValueDiff,
      })}
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
              <TagValues projectId={`${projectId}`} value={projectFlag.tags} />
            </div>

            {hasUserOverride && <IdentityOverrideDescription />}
            {showMultivariateOverride && (
              <MultivariateOverrideDescription controlValue={flagValue} />
            )}
            {showSegment && (
              <SegmentOverrideDescription
                showEnabledOverride={hasEnabledDiff}
                showValueOverride={!hasEnabledDiff}
                controlEnabled={flagEnabled}
                controlValue={flagValue}
              />
            )}
            {showDefaultsHint && (
              <div className='list-item-subtitle'>
                Using environment defaults
              </div>
            )}
          </Flex>
        </div>
      </Flex>

      <div className='table-column' style={{ width: COLUMN_WIDTHS[0] }}>
        <FeatureValue data-test={valueDataTest} value={actualValue} />
      </div>

      <div
        className='table-column'
        style={{ width: COLUMN_WIDTHS[1] }}
        onClick={stopPropagation}
      >
        {Utils.renderWithPermission(
          editPermission,
          editPermissionDescription,
          <Switch
            disabled={!editPermission}
            data-test={toggleDataTest}
            checked={!!actualEnabled}
            onChange={onToggle}
          />,
        )}
      </div>

      <div
        className='table-column p-0'
        style={{ width: COLUMN_WIDTHS[2] }}
        onClick={stopPropagation}
      >
        {cta}
      </div>
    </div>
  )
}

export default FeatureOverrideRow
