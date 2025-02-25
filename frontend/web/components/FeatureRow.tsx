import React, { FC, useEffect } from 'react'
import TagValues from './tags/TagValues'
import ConfirmToggleFeature from './modals/ConfirmToggleFeature'
import ConfirmRemoveFeature from './modals/ConfirmRemoveFeature'
import CreateFlagModal from './modals/CreateFlag'
import ProjectStore from 'common/stores/project-store'
import Constants from 'common/constants'
import { useProtectedTags } from 'common/utils/useProtectedTags'
import Icon from './Icon'
import FeatureValue from './FeatureValue'
import FeatureAction from './FeatureAction'
import { getViewMode } from 'common/useViewMode'
import classNames from 'classnames'
import Tag from './tags/Tag'
import Button from './base/forms/Button'
import SegmentOverridesIcon from './SegmentOverridesIcon'
import IdentityOverridesIcon from './IdentityOverridesIcon'
import StaleFlagWarning from './StaleFlagWarning'
import UnhealthyFlagWarning from './UnhealthyFlagWarning'
import {
  Environment,
  FeatureListProviderActions,
  FeatureListProviderData,
  FeatureState,
  ProjectFlag,
} from 'common/types/responses'
import Utils from 'common/utils/utils'
import API from 'project/api'
import Switch from './Switch'
import AccountStore from 'common/stores/account-store'
import CondensedFeatureRow from './CondensedFeatureRow'
import { RouterChildContext } from 'react-router'

interface FeatureRowProps {
  disableControls?: boolean
  environmentFlags: FeatureListProviderData['environmentFlags']
  environmentId: string
  permission?: boolean
  projectFlag: ProjectFlag
  projectId: string
  removeFlag?: FeatureListProviderActions['removeFlag']
  toggleFlag?: FeatureListProviderActions['toggleFlag']
  index: number
  readOnly?: boolean
  condensed?: boolean
  className?: string
  style?: React.CSSProperties
  fadeEnabled?: boolean
  fadeValue?: boolean
  hideAudit?: boolean
  hideRemove?: boolean
  history?: RouterChildContext['router']['history']
}

const width = [200, 70, 55, 70, 450]

const FeatureRow: FC<FeatureRowProps> = ({
  className,
  condensed = false,
  disableControls,
  environmentFlags,
  environmentId,
  fadeEnabled,
  fadeValue,
  hideAudit = false,
  hideRemove = false,
  history,
  index,
  permission,
  projectFlag,
  projectId,
  readOnly = false,
  removeFlag,
  style,
  toggleFlag,
}) => {
  const protectedTags = useProtectedTags(projectFlag, projectId)

  useEffect(() => {
    const { feature } = Utils.fromParam()
    const { id } = projectFlag

    const isModalOpen = !!document?.getElementsByClassName(
      'create-feature-modal',
    )?.length
    if (`${id}` === feature && !isModalOpen) {
      editFeature(projectFlag, environmentFlags?.[id])
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [environmentFlags, projectFlag])

  const copyFeature = () => {
    Utils.copyToClipboard(projectFlag.name)
  }

  const confirmRemove = (projectFlag: ProjectFlag, cb: () => void) => {
    openModal2(
      'Remove Feature',
      <ConfirmRemoveFeature projectFlag={projectFlag} cb={cb} />,
      'p-0',
    )
  }

  const confirmToggle = () => {
    const { id } = projectFlag
    openModal(
      'Toggle Feature',
      <ConfirmToggleFeature
        environmentId={environmentId}
        projectFlag={projectFlag}
        environmentFlag={environmentFlags?.[id]}
        cb={() => {
          toggleFlag?.(
            projectId,
            environmentId,
            projectFlag,
            environmentFlags?.[id],
          )
        }}
      />,
      'p-0',
    )
  }

  const onChange = () => {
    if (disableControls) {
      return
    }
    if (
      projectFlag?.multivariate_options?.length ||
      Utils.changeRequestsEnabled(environment?.minimum_change_request_approvals)
    ) {
      editFeature(projectFlag, environmentFlags?.[id])
      return
    }
    confirmToggle()
  }

  const editFeature = (
    projectFlag: ProjectFlag,
    environmentFlag?: FeatureState,
    tab?: string,
  ) => {
    if (disableControls) {
      return
    }

    API.trackEvent(Constants.events.VIEW_FEATURE)
    const tabValue = tab || Utils.fromParam().tab || 'value'

    history.replace({
      pathname: document.location.pathname,
      search: `?feature=${projectFlag.id}&tab=${tabValue}`,
    })

    openModal(
      <Row>
        {permission ? 'Edit Feature' : 'Feature'}: {projectFlag.name}
        <Button
          onClick={() => {
            Utils.copyToClipboard(projectFlag.name)
          }}
          theme='icon'
          className='ms-2'
        >
          <Icon name='copy' />
        </Button>
      </Row>,
      <CreateFlagModal
        hideTagsByType={['UNHEALTHY']}
        history={history}
        environmentId={environmentId}
        projectId={projectId}
        projectFlag={projectFlag}
        noPermissions={!permission}
        environmentFlag={environmentFlag}
        tab={tab}
        flagId={environmentFlag?.id}
      />,
      'side-modal create-feature-modal',
      () => {
        history.replace({
          pathname: document.location.pathname,
          search: '',
        })
      },
    )
  }

  const isReadOnly = readOnly || Utils.getFlagsmithHasFeature('read_only_mode')
  const isFeatureHealthEnabled = Utils.getFlagsmithHasFeature('feature_health')

  const { created_date, description, id, name } = projectFlag
  const environment = ProjectStore.getEnvironment(
    environmentId,
  ) as Environment | null

  const isCompact = getViewMode() === 'compact'
  const showPlusIndicator =
    projectFlag?.is_num_identity_overrides_complete === false

  if (condensed) {
    return (
      <CondensedFeatureRow
        disableControls={disableControls}
        readOnly={isReadOnly}
        projectFlag={projectFlag}
        environmentFlags={environmentFlags}
        permission={permission}
        editFeature={editFeature}
        onChange={onChange}
        style={style}
        className={className}
        isCompact={isCompact}
        fadeEnabled={fadeEnabled}
        fadeValue={fadeValue}
        index={index}
      />
    )
  }

  return (
    <Row
      className={classNames(
        `list-item ${isReadOnly ? '' : 'clickable'} ${
          isCompact ? 'py-0 list-item-xs fs-small' : 'py-1'
        }`,
        className,
      )}
      key={id}
      space
      data-test={`feature-item-${index}`}
      onClick={() =>
        !isReadOnly && editFeature(projectFlag, environmentFlags?.[id])
      }
    >
      <Flex className='table-column'>
        <Row>
          <Flex>
            <Row>
              <Row
                className='font-weight-medium'
                style={{
                  lineHeight: 1,
                  wordBreak: 'break-all',
                }}
              >
                <span>
                  {created_date ? (
                    <Tooltip place='right' title={name}>
                      {isCompact && description ? `${description}` : ''}
                    </Tooltip>
                  ) : (
                    name
                  )}
                </span>
                <Button
                  onClick={copyFeature}
                  theme='icon'
                  className='ms-2 me-2'
                >
                  <Icon name='copy' />
                </Button>
              </Row>
              <SegmentOverridesIcon
                onClick={(e) => {
                  e.stopPropagation()
                  editFeature(
                    projectFlag,
                    environmentFlags?.[id],
                    Constants.featurePanelTabs.SEGMENT_OVERRIDES,
                  )
                }}
                count={projectFlag.num_segment_overrides}
              />
              <IdentityOverridesIcon
                onClick={(e) => {
                  e.stopPropagation()
                  editFeature(
                    projectFlag,
                    environmentFlags?.[id],
                    Constants.featurePanelTabs.IDENTITY_OVERRIDES,
                  )
                }}
                count={projectFlag.num_identity_overrides}
                showPlusIndicator={showPlusIndicator}
              />
              {projectFlag.is_server_key_only && (
                <Tooltip
                  title={
                    <span
                      className='chip me-2 chip--xs bg-primary text-white'
                      style={{ border: 'none' }}
                    >
                      <span>{'Server-side only'}</span>
                    </span>
                  }
                  place='top'
                >
                  {
                    'Prevent this feature from being accessed with client-side SDKs.'
                  }
                </Tooltip>
              )}
              <TagValues projectId={`${projectId}`} value={projectFlag.tags}>
                {projectFlag.is_archived && (
                  <Tag className='chip--xs' tag={Constants.archivedTag} />
                )}
              </TagValues>
              {!!isCompact && <StaleFlagWarning projectFlag={projectFlag} />}
              {isFeatureHealthEnabled && !!isCompact && (
                <UnhealthyFlagWarning projectFlag={projectFlag} />
              )}
            </Row>
            {!isCompact && <StaleFlagWarning projectFlag={projectFlag} />}
            {isFeatureHealthEnabled && !isCompact && (
              <UnhealthyFlagWarning projectFlag={projectFlag} />
            )}
            {description && !isCompact && (
              <div
                className='list-item-subtitle'
                style={{ lineHeight: '20px', width: width[4] }}
              >
                {description}
              </div>
            )}
          </Flex>
        </Row>
      </Flex>
      <div className='table-column' style={{ width: width[0] }}>
        <FeatureValue
          onClick={() =>
            !isReadOnly && editFeature(projectFlag, environmentFlags?.[id])
          }
          value={environmentFlags?.[id]?.feature_state_value ?? null}
          data-test={`feature-value-${index}`}
        />
      </div>
      <div
        className='table-column'
        style={{ width: width[1] }}
        onClick={(e) => {
          e.stopPropagation()
        }}
      >
        <Switch
          disabled={!permission || isReadOnly}
          data-test={`feature-switch-${index}${
            environmentFlags?.[id]?.enabled ? '-on' : '-off'
          }`}
          checked={environmentFlags?.[id]?.enabled}
          onChange={onChange}
        />
      </div>

      <div
        className='table-column'
        style={{ width: isCompact ? width[2] : width[3] }}
        onClick={(e) => {
          e.stopPropagation()
        }}
      >
        <FeatureAction
          projectId={projectId}
          featureIndex={index}
          readOnly={isReadOnly}
          protectedTags={protectedTags}
          tags={projectFlag.tags}
          isCompact={isCompact}
          hideAudit={
            AccountStore.getOrganisationRole() !== 'ADMIN' || hideAudit
          }
          hideRemove={hideRemove}
          hideHistory={!environment?.use_v2_feature_versioning}
          onShowHistory={() => {
            if (disableControls) return
            editFeature(
              projectFlag,
              environmentFlags?.[id],
              Constants.featurePanelTabs.HISTORY,
            )
          }}
          onShowAudit={() => {
            if (disableControls) return
            history.push(
              `/project/${projectId}/audit-log?env=${environment?.id}&search=${projectFlag.name}`,
              '',
            )
          }}
          onRemove={() => {
            if (disableControls) return
            confirmRemove(projectFlag, () => {
              removeFlag?.(projectId, projectFlag)
            })
          }}
          onCopyName={copyFeature}
        />
      </div>
    </Row>
  )
}

export default FeatureRow
