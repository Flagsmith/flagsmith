// import propTypes from 'prop-types';
import React, { Component } from 'react'
import EnvironmentSelect from './EnvironmentSelect'
import data from 'common/data/base/_data'
import ProjectStore from 'common/stores/project-store'
import FeatureRow from './FeatureRow'
import FeatureListStore from 'common/stores/feature-list-store'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'
import Tag from './tags/Tag'

const featureNameWidth = 300

class CompareEnvironments extends Component {
  static displayName = 'CompareEnvironments'

  static propTypes = {}

  static contextTypes = {
    router: propTypes.object.isRequired,
  }

  constructor(props) {
    super(props)
    this.state = {
      environmentLeft: props.environmentId,
      environmentRight: '',
      isLoading: true,
      projectFlags: null,
      showArchived: false,
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (
      this.state.environmentLeft !== prevState.environmentLeft ||
      this.state.environmentRight !== prevState.environmentRight
    ) {
      this.fetch()
    }
  }

  fetch = () => {
    this.setState({ isLoading: true })
    return Promise.all([
      this.state.projectFlags
        ? Promise.resolve({ results: this.state.projectFlags })
        : data.get(
            `${Project.api}projects/${this.props.projectId}/features/?page_size=999`,
          ),
      data.get(
        `${Project.api}environments/${this.state.environmentLeft}/featurestates/?page_size=999`,
      ),
      data.get(
        `${Project.api}environments/${this.state.environmentRight}/featurestates/?page_size=999`,
      ),
    ]).then(([projectFlags, environmentLeftFlags, environmentRightFlags]) => {
      const changes = []
      const same = []
      _.each(
        _.sortBy(projectFlags.results, (p) => p.name),
        (projectFlag) => {
          const leftSide = environmentLeftFlags.results.find(
            (v) => v.feature === projectFlag.id,
          )
          const rightSide = environmentRightFlags.results.find(
            (v) => v.feature === projectFlag.id,
          )
          const change = {
            leftEnabled: leftSide.enabled,
            leftEnvironmentFlag: leftSide,
            leftValue: leftSide.feature_state_value,
            projectFlag,
            rightEnabled: rightSide.enabled,
            rightEnvironmentFlag: rightSide,
            rightValue: rightSide.feature_state_value,
          }
          change.enabledChanged = change.rightEnabled !== change.leftEnabled
          change.valueChanged = change.rightValue !== change.leftValue
          if (change.enabledChanged || change.valueChanged) {
            changes.push(change)
          } else {
            same.push(change)
          }
        },
      )
      this.setState({
        changes,
        environmentLeftFlags: _.keyBy(environmentLeftFlags.results, 'feature'),
        environmentRightFlags: _.keyBy(
          environmentRightFlags.results,
          'feature',
        ),
        isLoading: false,
        projectFlags: projectFlags.results,
        same,
      })
    })
  }

  onSave = () => this.fetch()

  filter = (items) => {
    if (!items) return items

    return items.filter((v) => {
      if (this.state.showArchived) {
        return true
      }
      return !v.projectFlag.is_archived
    })
  }

  render() {
    return (
      <div>
        <h3>Compare Environments</h3>
        <p>Compare feature flag changes across environments.</p>
        <Row>
          <Row>
            <div style={{ width: featureNameWidth }}>
              <EnvironmentSelect
                ignoreAPIKey={this.state.environmentRight}
                onChange={(environmentLeft) =>
                  this.setState({ environmentLeft })
                }
                value={this.state.environmentLeft}
              />
            </div>

            <div>
              <span className='icon ios ion-md-arrow-back mx-2' />
            </div>

            <div style={{ width: featureNameWidth }}>
              <EnvironmentSelect
                ignoreAPIKey={this.state.environmentLeft}
                onChange={(environmentRight) =>
                  this.setState({ environmentRight })
                }
                value={this.state.environmentRight}
              />
            </div>
          </Row>
        </Row>

        {this.state.environmentLeft && this.state.environmentRight ? (
          <FeatureListProvider onSave={this.onSave} onError={this.onError}>
            {({}, { removeFlag, toggleFlag }) => {
              const renderRow = (p, i, fadeEnabled, fadeValue) => {
                const environmentLeft = ProjectStore.getEnvironment(
                  this.state.environmentLeft,
                )
                const environmentRight = ProjectStore.getEnvironment(
                  this.state.environmentRight,
                )
                return (
                  <div className='list-item'>
                    <Row>
                      <div style={{ width: featureNameWidth }}>
                        {p.projectFlag.description ? (
                          <Tooltip
                            title={
                              <strong style={{ wordWrap: 'break-word' }}>
                                {p.projectFlag.name}
                              </strong>
                            }
                          >
                            {p.projectFlag.description}
                          </Tooltip>
                        ) : (
                          <strong style={{ wordWrap: 'break-word' }}>
                            {p.projectFlag.name}
                          </strong>
                        )}
                      </div>
                      <Flex className='mr-2'>
                        <Permission
                          level='environment'
                          permission={Utils.getManageFeaturePermission(
                            Utils.changeRequestsEnabled(
                              environmentLeft.minimum_change_request_approvals,
                            ),
                          )}
                          id={environmentLeft.api_key}
                        >
                          {({ permission }) => (
                            <FeatureRow
                              condensed
                              isCompareEnv
                              fadeEnabled={fadeEnabled}
                              fadeValue={fadeValue}
                              environmentFlags={this.state.environmentLeftFlags}
                              projectFlags={this.state.projectFlags}
                              permission={permission}
                              environmentId={this.state.environmentLeft}
                              projectId={this.props.projectId}
                              index={i}
                              canDelete={permission}
                              toggleFlag={toggleFlag}
                              removeFlag={removeFlag}
                              projectFlag={p.projectFlag}
                            />
                          )}
                        </Permission>
                      </Flex>
                      <Flex className='ml-2'>
                        <Permission
                          level='environment'
                          permission={Utils.getManageFeaturePermission(
                            Utils.changeRequestsEnabled(
                              environmentRight.minimum_change_request_approvals,
                            ),
                          )}
                          id={environmentRight.api_key}
                        >
                          {({ permission }) => (
                            <FeatureRow
                              condensed
                              isCompareEnv
                              fadeEnabled={fadeEnabled}
                              fadeValue={fadeValue}
                              environmentFlags={
                                this.state.environmentRightFlags
                              }
                              projectFlags={this.state.projectFlags}
                              permission={permission}
                              environmentId={this.state.environmentRight}
                              projectId={this.props.projectId}
                              index={i}
                              canDelete={permission}
                              toggleFlag={toggleFlag}
                              removeFlag={removeFlag}
                              projectFlag={p.projectFlag}
                            />
                          )}
                        </Permission>
                      </Flex>
                    </Row>
                  </div>
                )
              }
              return (
                <div>
                  {this.state.isLoading && (
                    <div className='text-center'>
                      <Loader />
                    </div>
                  )}
                  {!this.state.isLoading &&
                    (!this.state.changes || !this.state.changes.length) && (
                      <div className='text-center mt-2'>
                        These environments have no flag differences
                      </div>
                    )}
                  {!this.state.isLoading &&
                    this.state.changes &&
                    !!this.state.changes.length && (
                      <div className='mt-4' style={{ minWidth: 800 }}>
                        <Row>
                          <Tag
                            selected={this.state.showArchived}
                            onClick={() => {
                              FeatureListStore.isLoading = true
                              this.setState({
                                showArchived: !this.state.showArchived,
                              })
                            }}
                            className='px-2 py-2 ml-2 mr-2'
                            tag={{ label: 'Archived' }}
                          />
                        </Row>

                        <PanelSearch
                          title={
                            <Row>
                              <span style={{ width: featureNameWidth }}>
                                Changed Flags
                              </span>
                            </Row>
                          }
                          header={
                            <Row
                              className='mt-2'
                              style={{
                                marginLeft: '0.75rem',
                                marginRight: '0.75rem',
                              }}
                            >
                              <span style={{ width: featureNameWidth }} />
                              <Flex>
                                <strong
                                  style={{
                                    display: 'flex',
                                    flex: 1,
                                    justifyContent: 'center',
                                  }}
                                >
                                  {
                                    ProjectStore.getEnvironment(
                                      this.state.environmentLeft,
                                    ).name
                                  }
                                </strong>
                              </Flex>
                              <Flex>
                                <strong
                                  style={{
                                    display: 'flex',
                                    justifyContent: 'center',
                                  }}
                                >
                                  {
                                    ProjectStore.getEnvironment(
                                      this.state.environmentRight,
                                    ).name
                                  }
                                </strong>
                              </Flex>
                            </Row>
                          }
                          className='no-pad mt-2'
                          items={this.filter(this.state.changes)}
                          renderRow={(p, i) =>
                            renderRow(p, i, !p.enabledChanged, !p.valueChanged)
                          }
                        />
                      </div>
                    )}
                  {!this.state.isLoading &&
                    this.state.same &&
                    !!this.state.same.length && (
                      <div style={{ minWidth: 800 }}>
                        <div className='mt-4'>
                          <PanelSearch
                            title={
                              <Row>
                                <span style={{ width: featureNameWidth }}>
                                  Unchanged Flags
                                </span>
                              </Row>
                            }
                            header={
                              <Row
                                className='mt-2'
                                style={{
                                  marginLeft: '0.75rem',
                                  marginRight: '0.75rem',
                                }}
                              >
                                <span style={{ width: featureNameWidth }} />
                                <Flex>
                                  <strong
                                    style={{
                                      display: 'flex',
                                      justifyContent: 'center',
                                    }}
                                  >
                                    {
                                      ProjectStore.getEnvironment(
                                        this.state.environmentLeft,
                                      ).name
                                    }
                                  </strong>
                                </Flex>
                                <Flex>
                                  <strong
                                    style={{
                                      display: 'flex',
                                      justifyContent: 'center',
                                    }}
                                  >
                                    {
                                      ProjectStore.getEnvironment(
                                        this.state.environmentRight,
                                      ).name
                                    }
                                  </strong>
                                </Flex>
                              </Row>
                            }
                            className='no-pad mt-2'
                            items={this.filter(this.state.same)}
                            renderRow={(p, i) =>
                              renderRow(
                                p,
                                i,
                                !p.enabledChanged,
                                !p.valueChanged,
                              )
                            }
                          />
                        </div>
                      </div>
                    )}
                </div>
              )
            }}
          </FeatureListProvider>
        ) : (
          ''
        )}
      </div>
    )
  }
}

module.exports = ConfigProvider(CompareEnvironments)
