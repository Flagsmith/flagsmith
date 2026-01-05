import React, { FC, useCallback, useEffect, useMemo } from 'react'
import ConfirmToggleFeature from 'components/modals/ConfirmToggleFeature'
import ConfirmRemoveFeature from 'components/modals/ConfirmRemoveFeature'
import CreateFlagModal from 'components/modals/CreateFlag'
import ProjectStore from 'common/stores/project-store'
import Constants from 'common/constants'
import { useProtectedTags } from 'common/utils/useProtectedTags'
import Icon from 'components/Icon'
import FeatureValue from './FeatureValue'
import FeatureAction, { FeatureActionProps } from './FeatureAction'
import { getViewMode } from 'common/useViewMode'
import classNames from 'classnames'
import Button from 'components/base/forms/Button'
import {
  Environment,
  FeatureListProviderData,
  ProjectFlag,
  ReleasePipeline,
} from 'common/types/responses'
import Utils from 'common/utils/utils'
import API from 'project/api'
import Switch from 'components/Switch'
import AccountStore from 'common/stores/account-store'
import CondensedFeatureRow from 'components/CondensedFeatureRow'
import { useHistory } from 'react-router-dom'
import { useGetHealthEventsQuery } from 'common/services/useHealthEvents'
import FeatureName from './FeatureName'
import FeatureDescription from './FeatureDescription'
import FeatureTags from './FeatureTags'
import { useOptimisticToggle } from 'components/pages/features/hooks/useOptimisticToggle'

export interface FeatureRowProps {
  disableControls?: boolean
  environmentFlags: FeatureListProviderData['environmentFlags']
  environmentId: string
  permission?: boolean
  projectFlag: ProjectFlag
  projectId: number
  removeFlag?: (projectFlag: ProjectFlag) => void | Promise<void>
  toggleFlag?: (
    projectFlag: ProjectFlag,
    environmentFlag:
      | FeatureListProviderData['environmentFlags'][number]
      | undefined,
    onError?: () => void,
  ) => void | Promise<void>
  index: number
  readOnly?: boolean
  condensed?: boolean
  className?: string
  style?: React.CSSProperties
  fadeEnabled?: boolean
  fadeValue?: boolean
  hideAudit?: boolean
  hideRemove?: boolean
  releasePipelines?: ReleasePipeline[]
  onCloseEditModal?: () => void
}

const width = [220, 50, 55, 70, 450]

const FeatureRow: FC<FeatureRowProps> = (props) => {
  const {
    className,
    condensed = false,
    disableControls,
    environmentFlags,
    environmentId,
    fadeEnabled,
    fadeValue,
    hideAudit = false,
    hideRemove = false,
    index,
    onCloseEditModal,
    permission,
    projectFlag,
    projectId,
    readOnly = false,
    removeFlag,
    style,
    toggleFlag,
  } = props
  const protectedTags = useProtectedTags(projectFlag, projectId)
  const history = useHistory()
  const { id } = projectFlag

  const actualEnabled = environmentFlags?.[id]?.enabled
  const {
    displayValue: displayEnabled,
    revertOptimistic,
    setOptimistic,
  } = useOptimisticToggle(actualEnabled)

  const { data: healthEvents } = useGetHealthEventsQuery(
    { projectId: String(projectFlag.project) },
    { skip: !projectFlag?.project },
  )

  useEffect(() => {
    const { feature } = Utils.fromParam()
    const { id } = projectFlag

    const isModalOpen = !!document?.getElementsByClassName(
      'create-feature-modal',
    )?.length
    if (`${id}` === feature && !isModalOpen) {
      editFeature()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [environmentFlags, projectFlag])

  const featureUnhealthyEvents = useMemo(
    () =>
      healthEvents?.filter(
        (event) =>
          event.type === 'UNHEALTHY' && event.feature === projectFlag.id,
      ),
    [healthEvents, projectFlag],
  )

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
    openModal(
      'Toggle Feature',
      <ConfirmToggleFeature
        environmentId={environmentId}
        projectFlag={projectFlag}
        environmentFlag={environmentFlags?.[id]}
        cb={() => {
          handleToggle()
        }}
      />,
      'p-0',
    )
  }

  const handleToggle = useCallback(() => {
    setOptimistic(!actualEnabled)
    toggleFlag?.(projectFlag, environmentFlags?.[id], revertOptimistic)
  }, [
    actualEnabled,
    environmentFlags,
    id,
    projectFlag,
    revertOptimistic,
    setOptimistic,
    toggleFlag,
  ])

  const onChange = () => {
    if (disableControls) {
      return
    }
    if (
      projectFlag?.multivariate_options?.length ||
      Utils.changeRequestsEnabled(environment?.minimum_change_request_approvals)
    ) {
      editFeature()
      return
    }
    confirmToggle()
  }

  const editFeature = (tab?: string) => {
    const projectFlag = props.projectFlag
    const environmentFlag = environmentFlags?.[id]
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
        hasUnhealthyEvents={
          isFeatureHealthEnabled && !!featureUnhealthyEvents?.length
        }
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
        if (onCloseEditModal) {
          return onCloseEditModal()
        }

        history.replace({
          pathname: document.location.pathname,
          search: '',
        })
      },
    )
  }

  const isReadOnly = readOnly || Utils.getFlagsmithHasFeature('read_only_mode')
  const isFeatureHealthEnabled = Utils.getFlagsmithHasFeature('feature_health')

  const { description } = projectFlag
  const environment = ProjectStore.getEnvironment(
    environmentId,
  ) as Environment | null

  const isCompact = getViewMode() === 'compact'

  if (condensed) {
    return (
      <CondensedFeatureRow
        disableControls={disableControls}
        readOnly={isReadOnly}
        projectFlag={projectFlag}
        environmentFlags={environmentFlags}
        permission={permission}
        editFeature={editFeature}
        hasUnhealthyEvents={
          isFeatureHealthEnabled && !!featureUnhealthyEvents?.length
        }
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
  const featureActionProps: Omit<FeatureActionProps, 'e2e'> = {
    featureIndex: index,
    hideAudit: AccountStore.getOrganisationRole() !== 'ADMIN' || hideAudit,
    hideHistory: !environment?.use_v2_feature_versioning,
    hideRemove,
    onCopyName: copyFeature,
    onRemove: () => {
      if (disableControls) return
      confirmRemove(projectFlag, () => {
        removeFlag?.(projectFlag)
      })
    },
    onShowAudit: () => {
      if (disableControls) return
      history.push(
        `/project/${projectId}/audit-log?env=${environment?.id}&search=${projectFlag.name}`,
        '',
      )
    },
    onShowHistory: () => {
      if (disableControls) return
      editFeature(Constants.featurePanelTabs.HISTORY)
    },
    projectId,
    protectedTags,
    readOnly: isReadOnly,
    tags: projectFlag.tags,
  }
  return (
    <>
      <div
        className={classNames(
          `d-none d-lg-flex align-items-lg-center flex-lg-row list-item py-0 list-item-xs fs-small' ${
            isReadOnly ? '' : 'clickable'
          }`,
          className,
        )}
        key={id}
        data-test={`feature-item-${index}`}
        onClick={() => !isReadOnly && editFeature()}
      >
        <div className='table-column ps-2 px-0 align-items-center flex-1'>
          <div className='mx-0 flex-1 flex-column'>
            <div className='d-flex align-items-center'>
              <FeatureName name={projectFlag.name} />
              <FeatureTags
                editFeature={editFeature}
                projectFlag={projectFlag}
              />
            </div>
            {!isCompact && <FeatureDescription description={description} />}
          </div>
          <div className='d-none d-lg-flex align-items-center'>
            <div
              className='table-column px-1 px-lg-2 flex-1 flex-lg-auto'
              style={{ width: width[0] }}
            >
              <FeatureValue
                onClick={() => !isReadOnly && editFeature()}
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
                  displayEnabled ? '-on' : '-off'
                }`}
                checked={displayEnabled}
                onChange={onChange}
              />
            </div>
            <div
              className='table-column px-1 px-lg-2'
              style={{ width: isCompact ? width[2] : width[3] }}
              onClick={(e) => {
                e.stopPropagation()
              }}
            >
              <FeatureAction {...featureActionProps} />
            </div>
          </div>
        </div>
      </div>
      <div
        onClick={() => !isReadOnly && editFeature()}
        className='d-flex cursor-pointer flex-column justify-content-center px-2 list-item py-1  d-lg-none'
      >
        <div className='d-flex gap-2 align-items-center'>
          <div className='flex-1 align-items-center flex-wrap'>
            <FeatureName name={projectFlag.name} />
            <FeatureTags editFeature={editFeature} projectFlag={projectFlag} />
          </div>
          <Switch
            disabled={!permission || isReadOnly}
            data-test={`feature-switch-${index}${
              displayEnabled ? '-on' : '-off'
            }`}
            checked={displayEnabled}
            onChange={onChange}
          />
          <FeatureAction {...featureActionProps} disableE2E={true} />
        </div>
      </div>
    </>
  )
}

export default FeatureRow
