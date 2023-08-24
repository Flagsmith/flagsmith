// import propTypes from 'prop-types';
import React, { Component } from 'react'
import FlagSelect from './FlagSelect'
import ProjectStore from 'common/stores/project-store'
import data from 'common/data/base/_data'
import FeatureRow from './FeatureRow'
import ConfigProvider from 'common/providers/ConfigProvider'
import Permission from 'common/providers/Permission'

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
      flagId: '',
      selectedIndex: 0,
      // isLoading: true,
    }
  }

  componentDidUpdate(prevProps, prevState) {
    if (this.state.flagId !== prevState.flagId) {
      this.fetch()
    }
  }

  fetch = () => {
    if (this.state.flagId) {
      Promise.all(
        [
          data.get(
            `${Project.api}projects/${this.props.projectId}/features/${this.state.flagId}/`,
          ),
        ].concat(
          ProjectStore.getEnvs().map((v) =>
            data.get(
              `${Project.api}environments/${v.api_key}/featurestates/?feature=${this.state.flagId}`,
            ),
          ),
        ),
      ).then(([_flag, ...rest]) => {
        const flag = _flag
        const environmentResults = ProjectStore.getEnvs().map((env, i) => {
          const flags = {}
          flags[flag.id] = rest[i].results[0]
          return flags
        })
        this.setState({
          environmentResults,
          flag,
          isLoading: false,
        })
      })
    }
  }

  onSave = () => this.fetch()

  render() {
    return (
      <div>
        <div className='col-md-8'>
          <h5 className='mb-1'>Compare Feature Values</h5>
          <p className='fs-small mb-4 lh-sm'>
            Compare a feature's value across all of your environments. Select an
            environment to compare against others.
          </p>
        </div>
        <Row>
          <Row>
            <div style={{ width: featureNameWidth }}>
              <FlagSelect
                placeholder='Select a Feature...'
                projectId={this.props.projectId}
                onChange={(flagId, flag) =>
                  this.setState({ flag, flagId, isLoading: true })
                }
                value={this.state.flagId}
              />
            </div>
          </Row>
        </Row>
        {this.state.flagId && (
          <div>
            <FeatureListProvider onSave={this.onSave} onError={this.onError}>
              {({}, { removeFlag, toggleFlag }) => {
                const renderRow = (data, i) => {
                  const flagValues = this.state.environmentResults[i]
                  const compare =
                    this.state.environmentResults[this.state.selectedIndex]
                  const flagA = flagValues[this.state.flagId]
                  const flagB = compare[this.state.flagId]
                  const fadeEnabled = flagA.enabled === flagB.enabled
                  const fadeValue =
                    flagB.feature_state_value === flagA.feature_state_value
                  const changeRequestsEnabled = Utils.changeRequestsEnabled(
                    data.minimum_change_request_approvals,
                  )
                  return (
                    <Permission
                      level='environment'
                      permission={Utils.getManageFeaturePermission(
                        changeRequestsEnabled,
                      )}
                      id={data.api_key}
                    >
                      {({ permission }) => (
                        <Row className='list-item clickable'>
                          <Flex className=' flex-row table-column px-3'>
                            <div
                              onMouseDown={(e) => {
                                e.stopPropagation()
                                this.setState({ selectedIndex: i })
                              }}
                              className={`btn-radio mr-2 ${
                                this.state.selectedIndex === i
                                  ? 'btn-radio-on'
                                  : ''
                              }`}
                            />
                            <div className='font-weight-medium'>
                              {data.name}
                            </div>
                          </Flex>
                          <FeatureRow
                            fadeEnabled={fadeEnabled}
                            fadeValue={fadeValue}
                            condensed
                            environmentFlags={flagValues}
                            projectFlags={[this.state.flag]}
                            permission={permission}
                            environmentId={data.api_key}
                            projectId={this.props.projectId}
                            index={i}
                            canDelete={permission}
                            toggleFlag={toggleFlag}
                            removeFlag={removeFlag}
                            projectFlag={this.state.flag}
                          />
                        </Row>
                      )}
                    </Permission>
                  )
                }
                return (
                  <div>
                    {this.state.isLoading && (
                      <div className='text-center'>
                        <Loader />
                      </div>
                    )}
                    {!this.state.isLoading && (
                      <div>
                        <PanelSearch
                          className='mt-4 no-pad'
                          title={' Feature Values'}
                          header={
                            <Row className='table-header'>
                              <Flex className='table-column px-3'>
                                Environment
                              </Flex>
                              <Flex className='flex-row'>
                                <div
                                  className='table-column'
                                  style={{ width: '120px' }}
                                ></div>
                                <Flex className='table-column'>Value</Flex>
                              </Flex>
                            </Row>
                          }
                          items={ProjectStore.getEnvs()}
                          renderRow={renderRow}
                        />
                      </div>
                    )}
                  </div>
                )
              }}
            </FeatureListProvider>
          </div>
        )}
      </div>
    )
  }
}

module.exports = ConfigProvider(CompareEnvironments)
