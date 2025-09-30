import classNames from 'classnames'
import React, { FC, useCallback, useEffect, useMemo, useRef } from 'react'
import {
  FeatureState,
  IdentityFeatureState,
  ProjectFlag,
} from 'common/types/responses'
import AppActions from 'common/dispatcher/app-actions'

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
import { useHasPermission } from 'common/providers/Permission'
// import FeatureOverrideCTA from './FeatureOverrideCTA'
import API from 'project/api'
import Constants from 'common/constants'
import Button from 'components/base/forms/Button'
import Icon from 'components/Icon'
import CreateFlagModal from 'components/modals/CreateFlag'
import { useHistory } from 'react-router-dom'
import ProjectStore from 'common/stores/project-store'
import ConfirmToggleFeature from 'components/modals/ConfirmToggleFeature'
import FeatureOverrideCTA from './FeatureOverrideCTA'

const COLUMN_WIDTHS = [200, 48, 78]

type FeatureOverrideRowProps = {
  shouldPreselect?: boolean
  level: 'identity' | 'segment'
  dataTest: string
  identity?: string
  identifier?: string
  identityName?: string
  valueDataTest?: string
  toggleDataTest?: string
  projectFlag: ProjectFlag
  environmentFeatureState: FeatureState
  overrideFeatureState?: FeatureState | IdentityFeatureState | null
}

const FeatureOverrideRow: FC<FeatureOverrideRowProps> = ({
  dataTest,
  environmentFeatureState,
  identifier,
  identity,
  identityName,
  level,
  overrideFeatureState,
  projectFlag,
  shouldPreselect,
  toggleDataTest,
  valueDataTest,
}) => {
  const hasUserOverride =
    !!overrideFeatureState?.identity ||
    !!(overrideFeatureState as IdentityFeatureState).identity_uuid
  const hasPreselected = useRef(false)
  const viewMode = getViewMode()
  const isCompact = viewMode === 'compact'
  const history = useHistory()
  const environmentId = ProjectStore.getEnvironmentById(
    environmentFeatureState.environment,
  )?.api_key
  const { description, id: featureId, name, project: projectId } = projectFlag
  const flagEnabled = environmentFeatureState.enabled
  const flagValue = environmentFeatureState.feature_state_value
  const actualEnabled = overrideFeatureState?.enabled ?? flagEnabled
  const actualValue = overrideFeatureState?.feature_state_value ?? flagValue

  const onToggle = () => {
    const confirmToggle = (projectFlag: any, environmentFlag: any, cb: any) => {
      openModal(
        'Toggle Feature',
        <ConfirmToggleFeature
          identity={identity}
          identityName={decodeURIComponent(identity)}
          environmentId={environmentId}
          projectFlag={projectFlag}
          environmentFlag={environmentFlag}
          cb={cb}
        />,
        'p-0',
      )
    }

    confirmToggle(projectFlag, overrideFeatureState, () =>
      AppActions.toggleUserFlag({
        environmentFlag: environmentFeatureState,
        environmentId,
        identity,
        identityFlag: overrideFeatureState,
        projectFlag: {
          id: featureId,
        },
      }),
    )
  }

  const onClick = useCallback(() => {
    if (
      !projectFlag ||
      !environmentId ||
      !environmentFeatureState ||
      !overrideFeatureState
    )
      return

    history.replace(`${document.location.pathname}?flag=${projectFlag.name}`)
    API.trackEvent(Constants.events.VIEW_USER_FEATURE)
    openModal(
      <span>
        <Row>
          Edit User Feature:{' '}
          <span className='standard-case'>{projectFlag.name}</span>
          <Button
            onClick={() => {
              Utils.copyToClipboard(projectFlag.name)
            }}
            theme='icon'
            className='ms-2'
          >
            <Icon name='copy' />
          </Button>
        </Row>
      </span>,
      <CreateFlagModal
        history={history}
        identity={identity}
        identityName={identityName}
        environmentId={environmentId}
        projectId={projectId}
        projectFlag={projectFlag}
        identityFlag={{
          ...overrideFeatureState,
        }}
        environmentFlag={environmentFeatureState}
      />,
      'side-modal create-feature-modal overflow-y-auto',
      () => {
        history.replace(document.location.pathname)
      },
    )
  }, [
    projectId,
    overrideFeatureState,
    projectFlag,
    environmentFeatureState,
    history,
    environmentId,
  ])
  useEffect(() => {
    if (shouldPreselect && !hasPreselected.current) {
      hasPreselected.current = true
      onClick()
    }
  }, [shouldPreselect, onClick])

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

  const { permission, permissionDescription } =
    Utils.getOverridePermission(level)
  const editPermission = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission,
    tags: projectFlag.tags,
  })
  const showDefaultsHint = viewMode === 'default' && !hasAnyOverride

  const showMultivariateOverride = useMemo(() => {
    if (hasUserOverride || !hasValueDiff) return false
    return !!projectFlag?.multivariate_options?.some(
      (opt: any) => Utils.featureStateToValue(opt) === actualValue,
    )
  }, [hasUserOverride, hasValueDiff, projectFlag, actualValue])

  const showSegmentOverride =
    hasUserOverride && !hasUserOverride && !showMultivariateOverride
  const stopPropagation = (e: React.MouseEvent) => e.stopPropagation()
  if (!environmentFeatureState || !projectFlag) return null

  return (
    <div
      className={classNames('flex-row space list-item clickable py-2', {
        'bg-primary-opacity-5': hasAnyOverride,
        'list-item-xs': isCompact && !hasAnyOverride,
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
            {showSegmentOverride && (
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
          permissionDescription,
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
        <FeatureOverrideCTA
          identifier={identifier}
          identity={identity}
          environmentId={environmentId}
          projectFlag={projectFlag}
          environmentFeatureState={environmentFeatureState}
          hasUserOverride={hasUserOverride}
          overrideFeatureState={overrideFeatureState}
          level={level}
        />
      </div>
    </div>
  )
}

export default FeatureOverrideRow
