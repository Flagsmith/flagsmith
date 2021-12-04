// import propTypes from 'prop-types';
import React, { Component } from 'react';
import EnvironmentSelect from '../EnvironmentSelect';
import data from '../../../common/data/base/_data';
import ProjectStore from '../../../common/stores/project-store';

class TheComponent extends Component {
    static displayName = 'TheComponent';

    static propTypes = {};

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props) {
        super();
        this.state = {
            environmentLeft: props.match.params.environmentId,
            environmentRight: '',
            projectFlags: null,
            isLoading: true,
        };
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (this.state.environmentLeft !== prevState.environmentLeft || this.state.environmentRight !== prevState.environmentRight) {
            this.setState({ isLoading: true });
            return Promise.all([
                this.state.projectFlags ? Promise.resolve(this.state.projectFlags) : data.get(`${Project.api}projects/${this.props.match.params.projectId}/features/?page_size=999`),
                data.get(`${Project.api}environments/${this.state.environmentLeft}/featurestates/?page_size=999`),
                data.get(`${Project.api}environments/${this.state.environmentRight}/featurestates/?page_size=999`),
            ]).then(([projectFlags, environmentLeftFlags, environmentRightFlags]) => {
                const changes = [];
                _.each(projectFlags.results, (projectFlag) => {
                    const leftSide = environmentLeftFlags.results.find(v => v.feature === projectFlag.id);
                    const rightSide = environmentRightFlags.results.find(v => v.feature === projectFlag.id);
                    const change = {
                        projectFlag,
                        leftEnabled: leftSide.enabled,
                        rightEnabled: rightSide.enabled,
                        leftValue: leftSide.feature_state_value,
                        rightValue: rightSide.feature_state_value,
                    };
                    change.enabledChanged = change.rightEnabled !== change.leftEnabled;
                    change.valueChanged = change.rightValue !== change.leftValue;
                    if (change.enabledChanged || change.valueChanged) {
                        changes.push(change);
                    }
                });
                this.setState({ changes, isLoading: false });
            }).catch((e) => {
                debugger;
            });
        }
    }

    render() {
        const featureNameWidth = 300;
        return (
            <div className="app-container container">
                <h3>
                    Compare Environments
                </h3>
                <p>
                    Compare feature flag and segment override changes across environments.
                </p>
                <Row>
                    <Row>
                        <div style={{ width: featureNameWidth }}>
                            <EnvironmentSelect onChange={environmentLeft => this.setState({ environmentLeft })} value={this.state.environmentLeft}/>
                        </div>

                        <div>
                            <ion className="icon ios ion-md-arrow-back mx-2"/>
                        </div>

                        <div style={{ width: featureNameWidth }}>
                            <EnvironmentSelect ignoreAPIKey={this.state.environmentLeft} onChange={environmentRight => this.setState({ environmentRight })} value={this.state.environmentRight}/>
                        </div>
                    </Row>

                </Row>

                {
                    this.state.environmentLeft && this.state.environmentRight ? (
                        <div>
                            {this.state.isLoading && (
                                <div className="text-center">
                                    <Loader/>
                                </div>
                            )}
                            {!this.state.isLoading && (!this.state.changes || !this.state.changes.length) && (
                                <div className="text-center">
                                  These environments have no flag differences
                                </div>
                            )}
                            {!this.state.isLoading && (this.state.changes && !!this.state.changes.length) && (
                                <div style={{ minWidth: 800 }}>
                                    <PanelSearch
                                      title={
                                      (
                                          <Row>
                                              <span style={{ width: featureNameWidth }}>
                                                Feature
                                              </span>
                                          </Row>
)
                                  }
                                      header={(
                                      (
                                          <Row className="mt-2" style={{ marginLeft: '0.75rem', marginRight: '0.75rem' }}>
                                              <span style={{ width: featureNameWidth }} />
                                              <Flex>
                                                  <strong>
                                                      {ProjectStore.getEnvironment(this.state.environmentLeft).name}

                                                  </strong>
                                              </Flex>
                                              <Flex>
                                                  <strong>
                                                      {ProjectStore.getEnvironment(this.state.environmentRight).name}
                                                  </strong>
                                              </Flex>
                                          </Row>
)
                                  )}
                                      className="no-pad mt-2"
                                      items={this.state.changes}
                                      renderRow={p => (
                                          <div className="list-item">
                                              <Row>
                                                  <div style={{ width: featureNameWidth }}>
                                                      <Tooltip title={(
                                                          <strong>
                                                              {p.projectFlag.name}
                                                          </strong>
                                                  )}
                                                      >
                                                          {p.projectFlag.description}
                                                      </Tooltip>
                                                  </div>
                                                  <Flex>
                                                      <Row>
                                                          <div className={`mr-2 ${!p.enabledChanged && 'faded'}`}>
                                                              <Switch checked={p.leftEnabled}/>
                                                          </div>
                                                          <div className={`mr-2 ${!p.valueChanged && 'faded'}`}>
                                                              <FeatureValue value={p.leftValue}/>
                                                          </div>
                                                      </Row>

                                                  </Flex>
                                                  <Flex>
                                                      <Row>
                                                          <div className={`mr-2 ${!p.enabledChanged && 'faded'}`}>
                                                              <Switch checked={p.rightEnabled}/>
                                                          </div>
                                                          <div className={`mr-2 ${!p.valueChanged && 'faded'}`}>
                                                              <FeatureValue value={p.rightValue}/>
                                                          </div>
                                                      </Row>

                                                  </Flex>
                                              </Row>


                                          </div>
                                      )}
                                    />
                                </div>
                            )}
                        </div>
                    ) : ''
                }

            </div>
        );
    }
}

module.exports = hot(module)(ConfigProvider(TheComponent));
