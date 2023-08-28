import React, { Component } from 'react'
import TagValues from './tags/TagValues'
import ConfirmToggleFeature from './modals/ConfirmToggleFeature'
import ConfirmRemoveFeature from './modals/ConfirmRemoveFeature'
import CreateFlagModal from './modals/CreateFlag'
import ProjectStore from 'common/stores/project-store'
import Permission from 'common/providers/Permission'
import Constants from 'common/constants'
import { hasProtectedTag } from 'common/utils/hasProtectedTag'
import SegmentsIcon from './svg/SegmentsIcon'
import UsersIcon from './svg/UsersIcon' // we need this to make JSX compile
import Icon from './Icon'
import FeatureValue from './FeatureValue'

export const width = [200, 65, 48, 75]
class TheComponent extends Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  state = {}

  confirmToggle = (projectFlag, environmentFlag, cb) => {
    openModal(
      'Toggle Feature',
      <ConfirmToggleFeature
        environmentId={this.props.environmentId}
        projectFlag={projectFlag}
        environmentFlag={environmentFlag}
        cb={cb}
      />,
      'p-0',
    )
  }

  componentDidMount() {
    const { environmentFlags, projectFlag } = this.props
    const { feature, tab } = Utils.fromParam()
    const { id } = projectFlag
    if (`${id}` === feature) {
      this.editFeature(projectFlag, environmentFlags[id], tab)
    }
  }

  confirmRemove = (projectFlag, cb) => {
    openModal(
      'Remove Feature',
      <ConfirmRemoveFeature
        environmentId={this.props.environmentId}
        projectFlag={projectFlag}
        cb={cb}
      />,
      'p-0',
    )
  }

  editFeature = (projectFlag, environmentFlag, tab) => {
    API.trackEvent(Constants.events.VIEW_FEATURE)

    history.replaceState(
      {},
      null,
      `${document.location.pathname}?feature=${projectFlag.id}${
        tab ? `&tab=${tab}` : ''
      }`,
    )
    openModal(
      `${this.props.permission ? 'Edit Feature' : 'Feature'}: ${
        projectFlag.name
      }`,
      <CreateFlagModal
        environmentId={this.props.environmentId}
        projectId={this.props.projectId}
        projectFlag={projectFlag}
        noPermissions={!this.props.permission}
        environmentFlag={environmentFlag}
        flagId={environmentFlag.id}
      />,
      'side-modal create-feature-modal',
      () => {
        history.replaceState({}, null, `${document.location.pathname}`)
      },
    )
  }

  render() {
    const {
      environmentFlags,
      environmentId,
      permission,
      projectFlag,
      projectFlags,
      projectId,
      removeFlag,
      toggleFlag,
    } = this.props
    const { created_date, description, id, name } = this.props.projectFlag
    const readOnly =
      this.props.readOnly || Utils.getFlagsmithHasFeature('read_only_mode')
    const isProtected = hasProtectedTag(projectFlag, projectId)
    const environment = ProjectStore.getEnvironment(environmentId)
    const changeRequestsEnabled = Utils.changeRequestsEnabled(
      environment && environment.minimum_change_request_approvals,
    )

    if (this.props.condensed) {
      return Utils.renderWithPermission(
        permission,
        Constants.environmentPermissions(
          Utils.getManageFeaturePermissionDescription(changeRequestsEnabled),
        ),
        <Flex
          onClick={() =>
            !readOnly && this.editFeature(projectFlag, environmentFlags[id])
          }
          style={{
            ...(this.props.style || {}),
          }}
          className='flex-row'
        >
          <div
            className={`table-column ${this.props.fadeEnabled && 'faded'}`}
            style={{ width: '120px' }}
          >
            <Switch
              disabled={!permission || readOnly}
              data-test={`feature-switch-${this.props.index}${
                environmentFlags[id] && environmentFlags[id].enabled
                  ? '-on'
                  : '-off'
              }`}
              checked={environmentFlags[id] && environmentFlags[id].enabled}
              onChange={() => {
                if (changeRequestsEnabled) {
                  this.editFeature(projectFlag, environmentFlags[id])
                  return
                }
                this.confirmToggle(
                  projectFlag,
                  environmentFlags[id],
                  (environments) => {
                    toggleFlag(
                      _.findIndex(projectFlags, { id }),
                      environments,
                      null,
                      this.props.environmentFlags,
                      this.props.projectFlags,
                    )
                  },
                )
              }}
            />
          </div>
          <Flex
            className={`table-column clickable ${
              this.props.fadeValue && 'faded'
            }`}
          >
            <FeatureValue
              onClick={() =>
                permission &&
                !readOnly &&
                this.editFeature(projectFlag, environmentFlags[id])
              }
              value={
                environmentFlags[id] && environmentFlags[id].feature_state_value
              }
              data-test={`feature-value-${this.props.index}`}
            />
          </Flex>
        </Flex>,
      )
    }
    return Utils.renderWithPermission(
      permission,
      Constants.environmentPermissions(
        Utils.getManageFeaturePermissionDescription(changeRequestsEnabled),
      ),
      <Row
        className={`list-item ${readOnly ? '' : 'clickable'} ${
          this.props.widget ? 'py-1' : 'py-2'
        }`}
        key={id}
        space
        data-test={`feature-item-${this.props.index}`}
        onClick={() =>
          !readOnly && this.editFeature(projectFlag, environmentFlags[id])
        }
      >
        <Flex className='table-column'>
          <Row>
            <Flex>
              <Row
                className='font-weight-medium mb-1'
                style={{
                  alignItems: 'start',
                  lineHeight: 1,
                  rowGap: 4,
                  wordBreak: 'break-all',
                }}
              >
                <span className='me-2'>
                  {description ? (
                    <Tooltip
                      title={
                        <span>
                          {name}
                          <span className={'ms-1'}></span>
                          <Icon name='info-outlined' />
                        </span>
                      }
                    >
                      {description}
                    </Tooltip>
                  ) : (
                    name
                  )}
                </span>

                {!!projectFlag.num_segment_overrides && (
                  <Tooltip
                    title={
                      <span
                        className='chip me-2 chip--xs bg-primary text-white'
                        style={{ border: 'none' }}
                      >
                        <SegmentsIcon className='chip-svg-icon' />
                        <span>{projectFlag.num_segment_overrides}</span>
                      </span>
                    }
                    place='top'
                  >
                    {`${projectFlag.num_segment_overrides} Segment Override${
                      projectFlag.num_segment_overrides !== 1 ? 's' : ''
                    }`}
                  </Tooltip>
                )}
                {!!projectFlag.num_identity_overrides && (
                  <Tooltip
                    title={
                      <span
                        className='chip me-2 chip--xs bg-primary text-white'
                        style={{ border: 'none' }}
                      >
                        <UsersIcon className='chip-svg-icon' />
                        <span>{projectFlag.num_identity_overrides}</span>
                      </span>
                    }
                    place='top'
                  >
                    {`${projectFlag.num_identity_overrides} Identity Override${
                      projectFlag.num_identity_overrides !== 1 ? 's' : ''
                    }`}
                  </Tooltip>
                )}
                <TagValues
                  inline
                  projectId={`${projectId}`}
                  value={projectFlag.tags}
                />
              </Row>
              <div className='list-item-subtitle'>
                Created {moment(created_date).format('Do MMM YYYY HH:mma')}
              </div>
            </Flex>
          </Row>
        </Flex>
        <div className='table-column' style={{ width: width[0] }}>
          <FeatureValue
            onClick={() =>
              !readOnly && this.editFeature(projectFlag, environmentFlags[id])
            }
            value={
              environmentFlags[id] && environmentFlags[id].feature_state_value
            }
            data-test={`feature-value-${this.props.index}`}
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
            disabled={!permission || readOnly}
            data-test={`feature-switch-${this.props.index}${
              environmentFlags[id] && environmentFlags[id].enabled
                ? '-on'
                : '-off'
            }`}
            checked={environmentFlags[id] && environmentFlags[id].enabled}
            onChange={() => {
              if (
                Utils.changeRequestsEnabled(
                  environment.minimum_change_request_approvals,
                )
              ) {
                this.editFeature(projectFlag, environmentFlags[id])
                return
              }
              this.confirmToggle(
                projectFlag,
                environmentFlags[id],
                (environments) => {
                  toggleFlag(_.findIndex(projectFlags, { id }), environments)
                },
              )
            }}
          />
        </div>
        <div
          className='table-column'
          style={{ width: width[2] }}
          onClick={(e) => {
            e.stopPropagation()
          }}
        >
          {AccountStore.getOrganisationRole() === 'ADMIN' &&
            !this.props.hideAudit && (
              <Tooltip
                html
                title={
                  <div
                    onClick={() => {
                      this.context.router.history.push(
                        Utils.getFlagsmithHasFeature('feature_versioning')
                          ? `/project/${projectId}/environment/${environmentId}/feature-history?feature=${projectFlag.id}`
                          : `/project/${projectId}/environment/${environmentId}/audit-log?env=${environment.id}&search=${projectFlag.name}`,
                      )
                    }}
                    data-test={`feature-history-${this.props.index}`}
                  >
                    <Icon name='clock' width={24} fill='#9DA4AE' />
                  </div>
                }
              >
                Feature history
              </Tooltip>
            )}
        </div>
        <div
          className='table-column'
          style={{ width: width[3] }}
          onClick={(e) => {
            e.stopPropagation()
          }}
        >
          {!this.props.hideRemove && (
            <Permission
              level='project'
              permission='DELETE_FEATURE'
              id={projectId}
            >
              {({ permission: removeFeaturePermission }) =>
                Utils.renderWithPermission(
                  removeFeaturePermission,
                  Constants.projectPermissions('Delete Feature'),
                  <Tooltip
                    html
                    title={
                      <Button
                        disabled={
                          !removeFeaturePermission || readOnly || isProtected
                        }
                        onClick={() =>
                          this.confirmRemove(projectFlag, () => {
                            removeFlag(projectId, projectFlag)
                          })
                        }
                        className='btn btn-with-icon'
                        data-test={`remove-feature-btn-${this.props.index}`}
                      >
                        <Icon name='trash-2' width={20} fill='#656D7B' />
                      </Button>
                    }
                  >
                    {isProtected
                      ? '<span>This feature has been tagged as <bold>protected</bold>, <bold>permanent</bold>, <bold>do not delete</bold>, or <bold>read only</bold>. Please remove the tag before attempting to delete this flag.</span>'
                      : 'Remove feature'}
                  </Tooltip>,
                )
              }
            </Permission>
          )}
        </div>
      </Row>,
    )
  }
}

export default TheComponent
