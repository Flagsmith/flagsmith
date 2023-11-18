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
import { Actionables } from './Actionables'

export const width = [200, 65, 48, 75, 450]
class TheComponent extends Component {
  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  state = {
    features_compact_view: propTypes.compactView,
    showActions: false,
  }

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

  componentDidUpdate(prevProps) {
    if (this.props.compactView !== prevProps.compactView) {
      this.setState({ features_compact_view: this.props.compactView })
    }
  }

  componentDidMount() {
    const { environmentFlags, projectFlag } = this.props
    const { feature, tab } = Utils.fromParam()
    console.log(this.state)
    const { id } = projectFlag
    if (`${id}` === feature) {
      this.editFeature(projectFlag, environmentFlags[id], tab)
    }
  }

  showActions = () => {
    this.setState({ showActions: true })
  }

  hideActions = () => {
    this.setState({ showActions: false })
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
      `${document.location.pathname}?feature=${projectFlag.id}`,
    )
    openModal(
      `${this.props.permission ? 'Edit Feature' : 'Feature'}: ${
        projectFlag.name
      }`,
      <CreateFlagModal
        isEdit
        environmentId={this.props.environmentId}
        projectId={this.props.projectId}
        projectFlag={projectFlag}
        noPermissions={!this.props.permission}
        environmentFlag={environmentFlag}
        tab={tab}
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
      return (
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
        </Flex>
      )
    }
    return (
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
        onMouseEnter={this.showActions}
        onMouseLeave={this.hideActions}
        onTouchStart={this.showActions}
        onBlur={this.hideActions}
      >
        <Flex className='table-column'>
          <Row>
            <Flex>
              <Row
                className='font-weight-medium'
                style={{
                  alignItems: 'start',
                  lineHeight: 1,
                  rowGap: 4,
                  wordBreak: 'break-all',
                }}
              >
                <span className='me-2'>{name}</span>

                <Actionables showActions={this.state.showActions}>
                  {created_date && (
                    <Tooltip
                      place='top'
                      title={
                        <span>
                          {/* {name} */}
                          <span className={'ms-1'}></span>
                          <Icon name='info-outlined' />
                        </span>
                      }
                    >
                      {`Created ${moment(created_date).format(
                        'Do MMM YYYY HH:mma',
                      )}`}
                    </Tooltip>
                  )}
                  {AccountStore.getOrganisationRole() === 'ADMIN' &&
                    !this.props.hideAudit && (
                      <Tooltip
                        html
                        title={
                          <div
                            onClick={() => {
                              this.context.router.history.push(
                                `/project/${projectId}/environment/${environmentId}/audit-log?env=${environment.id}&search=${projectFlag.name}`,
                              )
                            }}
                            data-test={`feature-history-${this.props.index}`}
                          >
                            <Icon name='clock' width={20} fill='#9DA4AE' />
                          </div>
                        }
                      >
                        Feature history
                      </Tooltip>
                    )}
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
                                  !removeFeaturePermission ||
                                  readOnly ||
                                  isProtected
                                }
                                onClick={() =>
                                  this.confirmRemove(projectFlag, () => {
                                    removeFlag(projectId, projectFlag)
                                  })
                                }
                                className='btn btn-with-icon'
                                data-test={`remove-feature-btn-${this.props.index}`}
                              >
                                <Icon
                                  name='trash-2'
                                  width={20}
                                  fill='#656D7B'
                                />
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
                </Actionables>

                {!!projectFlag.num_segment_overrides && (
                  <div
                    onClick={(e) => {
                      e.stopPropagation()
                      this.editFeature(projectFlag, environmentFlags[id], 1)
                    }}
                  >
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
                  </div>
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
                <TagValues
                  inline
                  projectId={`${projectId}`}
                  value={projectFlag.tags}
                />
              </Row>
              {description && !this.state.features_compact_view && (
                <div
                  className='list-item-subtitle mt-1'
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
      </Row>
    )
  }
}

export default TheComponent
