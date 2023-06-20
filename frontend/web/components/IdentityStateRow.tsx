import React, { FC } from 'react'
import Utils from 'common/utils/utils'
import { FeatureState, ProjectFlag } from 'common/types/responses' // we need this to make JSX compile
import API from 'project/api'
import Constants from 'common/constants'
import { useHasPermission } from 'common/providers/Permission'
import ConfirmToggleEnvFeature from './modals/ConfirmToggleEnvFeature'
import ConfirmRemoveFeature from './modals/ConfirmRemoveFeature'
import IdentityProvider from 'common/providers/IdentityProvider'
import Button, { ButtonLink } from './base/forms/Button'
import TagValues from './tags/TagValues'
import FeatureValue from './FeatureValue'
import Switch from './Switch'
const CreateFlagModal = require('components/modals/CreateFlag')

type IdentityStateRowType = {
  actualFlags: Record<string, FeatureState> | undefined //
  identityFlags: Record<string, FeatureState> | undefined
  projectFlags: ProjectFlag[] | undefined
  environmentFlags: Record<string, FeatureState> | undefined
  featureId: string
  featureName: string
  i: number
  environmentId: string
  projectId: string
  identityId: string
  identityName: string
  onClick?: (projectFlag: ProjectFlag) => void
  onClose?: () => void
  onSave?: () => void
}
const valuesEqual = (
  actualValue: string | undefined,
  flagValue: string | undefined,
) => {
  const nullFalseyA =
    actualValue == null ||
    actualValue === '' ||
    typeof actualValue === 'undefined'
  const nullFalseyB =
    flagValue == null || flagValue === '' || typeof flagValue === 'undefined'
  if (nullFalseyA && nullFalseyB) {
    return true
  }
  return actualValue === flagValue
}

const editFeature = (
  projectFlag: ProjectFlag,
  environmentFlag: FeatureState,
  identityFlag: FeatureState,
  identityId: string,
  identityName: string,
  environmentId: string,
  projectId: string,
  onClose?: () => void,
) => {
  const multivariate_feature_state_values =
    identityFlag?.multivariate_feature_state_values

  API.trackEvent(Constants.events.VIEW_USER_FEATURE)
  openModal(
    <span>
      Edit User Feature:{' '}
      <span className='standard-case'>{projectFlag.name}</span>
    </span>,
    <CreateFlagModal
      isEdit
      identity={identityId}
      identityName={decodeURIComponent(identityName)}
      environmentId={environmentId}
      projectId={projectId}
      projectFlag={projectFlag}
      identityFlag={{
        ...identityFlag,
        multivariate_feature_state_values,
      }}
      environmentFlag={environmentFlag}
    />,
    null,
    {
      className: 'side-modal fade create-feature-modal overflow-y-auto',
      onClose,
    },
  )
}

const confirmToggle = ({
  cb,
  environmentFlag,
  environmentId,
  identity,
  identityName,
  projectFlag,
}: {
  identity: string
  identityName: string
  environmentId: string
  projectFlag: ProjectFlag
  environmentFlag: FeatureState
  cb?: () => void
}) => {
  openModal(
    'Toggle Feature',
    <ConfirmToggleEnvFeature
      identity={identity}
      identityName={identityName}
      environmentId={environmentId}
      projectFlag={projectFlag}
      environmentFlag={environmentFlag}
      cb={cb}
    />,
  )
}

const confirmRemove = ({
  cb,
  environmentId,
  identity,
  projectFlag,
}: {
  cb: () => void
  projectFlag: ProjectFlag
  identity: string
  environmentId: string
}) => {
  openModal(
    'Reset User Feature',
    <ConfirmRemoveFeature
      identity={identity}
      environmentId={environmentId}
      projectFlag={projectFlag}
      cb={cb}
    />,
  )
}

const IdentityStateRow: FC<IdentityStateRowType> = ({
  actualFlags,
  environmentFlags,
  environmentId,
  featureId,
  featureName,
  i,
  identityFlags,
  identityId,
  identityName,
  onClick,
  onClose,
  onSave,
  projectFlags,
  projectId,
}) => {
  const identityFlag = identityFlags?.[featureId]
  const environmentFlag = environmentFlags && environmentFlags[featureId]
  const hasUserOverride = identityFlag?.identity || identityFlag?.identity_uuid
  const flagEnabled = hasUserOverride
    ? identityFlag.enabled
    : environmentFlag?.enabled // show default value s
  const flagValue = hasUserOverride
    ? identityFlag.feature_state_value
    : environmentFlag?.feature_state_value
  const actualFlag = actualFlags?.[featureName]
  const actualEnabled = !!actualFlag?.enabled
  const actualValue = actualFlag?.feature_state_value
  const flagEnabledDifferent = hasUserOverride
    ? false
    : actualEnabled !== flagEnabled
  const flagValueDifferent = hasUserOverride
    ? false
    : !valuesEqual(actualValue, flagValue)
  const projectFlag = projectFlags?.find(
    (p) => p.id === (environmentFlag && environmentFlag.feature),
  )
  const isMultiVariateOverride =
    flagValueDifferent &&
    projectFlag &&
    projectFlag.multivariate_options &&
    projectFlag.multivariate_options.find((v) => {
      const value = Utils.featureStateToValue(v)
      return value === actualValue
    })
  const flagDifferent = flagEnabledDifferent || flagValueDifferent

  const permission = useHasPermission({
    id: environmentId,
    level: 'environment',
    permission: Utils.getManageFeaturePermission(false),
  })
  return (
    <IdentityProvider onSave={onSave}>
      {(
        _: any,
        { removeFlag, toggleFlag }: any, //todo: Identity provider will be replaced
      ) => (
        <Row
          className={`list-item clickable py-1 ${
            flagDifferent && 'flag-different'
          }`}
          space
          data-test={`user-feature-${i}`}
        >
          <div
            onClick={() => {
              onClick?.(projectFlag!)
              editFeature(
                projectFlag!,
                environmentFlag!,
                identityFlag || actualFlag!,
                identityId,
                identityName,
                environmentId,
                projectId,
                onClose,
              )
            }}
            className='flex flex-1'
          >
            <Row>
              <ButtonLink className='mr-2'>{featureName}</ButtonLink>
              <TagValues projectId={`${projectId}`} value={projectFlag?.tags} />
            </Row>
            {hasUserOverride ? (
              <Row className='chip'>
                <span>Overriding defaults</span>
                <span className='chip-icon icon ion-md-information' />
              </Row>
            ) : flagEnabledDifferent ? (
              <span
                data-test={`feature-override-${i}`}
                className='flex-row chip'
              >
                <Row>
                  <Flex>
                    {isMultiVariateOverride ? (
                      <span>
                        This flag is being overridden by a variation defined on
                        your feature, the control value is{' '}
                        <strong>{flagEnabled ? 'on' : 'off'}</strong> for this
                        user
                      </span>
                    ) : (
                      <span>
                        This flag is being overridden by segments and would
                        normally be{' '}
                        <strong>{flagEnabled ? 'on' : 'off'}</strong> for this
                        user
                      </span>
                    )}
                  </Flex>
                  <span className='ml-1 chip-icon icon ion-md-information' />
                </Row>
              </span>
            ) : flagValueDifferent ? (
              isMultiVariateOverride ? (
                <span
                  data-test={`feature-override-${i}`}
                  className='flex-row chip'
                >
                  <span>
                    This feature is being overriden by a % variation in the
                    environment, the control value of this feature is{' '}
                    <FeatureValue
                      includeEmpty
                      data-test={`user-feature-original-value-${i}`}
                      value={`${flagValue}`}
                    />
                  </span>
                  <span className='chip-icon icon ion-md-information' />
                </span>
              ) : (
                <span
                  data-test={`feature-override-${i}`}
                  className='flex-row chip'
                >
                  <span>
                    This feature is being overriden by segments and would
                    normally be{' '}
                    <FeatureValue
                      includeEmpty
                      data-test={`user-feature-original-value-${i}`}
                      value={`${flagValue}`}
                    />{' '}
                    for this user
                  </span>
                  <span className='chip-icon icon ion-md-information' />
                </span>
              )
            ) : (
              <div className='list-item-footer'>
                <span className='faint'>Using environment defaults</span>
              </div>
            )}
          </div>
          <Row>
            <Column>
              <div className='feature-value'>
                <FeatureValue
                  data-test={`user-feature-value-${i}`}
                  value={actualValue as any}
                />
              </div>
            </Column>
            <Column>
              <div>
                {Utils.renderWithPermission(
                  permission,
                  Constants.environmentPermissions(
                    Utils.getManageFeaturePermissionDescription(false, true),
                  ),
                  <Switch
                    disabled={!permission}
                    data-test={`user-feature-switch-${i}${
                      actualEnabled ? '-on' : '-off'
                    }`}
                    checked={actualEnabled}
                    onChange={() =>
                      confirmToggle({
                        cb: () => {
                          toggleFlag({
                            environmentFlag,
                            environmentId,
                            identity: identityId,
                            identityFlag,
                            projectFlag,
                          })
                        },
                        environmentFlag: environmentFlag!,
                        environmentId,
                        identity: identityId,
                        identityName: identityName,
                        projectFlag: projectFlag!,
                      })
                    }
                  />,
                )}
              </div>
            </Column>
            {hasUserOverride && (
              <Column>
                {Utils.renderWithPermission(
                  permission,
                  Constants.environmentPermissions(
                    Utils.getManageFeaturePermissionDescription(false, true),
                  ),
                  <Button
                    disabled={!permission}
                    onClick={() =>
                      confirmRemove({
                        cb: () => {
                          removeFlag({
                            environmentId: environmentId,
                            identity: identityId,
                            identityFlag,
                          })
                        },
                        environmentId,
                        identity: identityId,
                        projectFlag: projectFlag!,
                      })
                    }
                  >
                    Reset
                  </Button>,
                )}
              </Column>
            )}
          </Row>
        </Row>
      )}
    </IdentityProvider>
  )
}

export default IdentityStateRow
