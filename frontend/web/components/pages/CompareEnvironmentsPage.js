// import propTypes from 'prop-types';
import React, { Component } from 'react';
import EnvironmentSelect from '../EnvironmentSelect';
import data from '../../../common/data/base/_data';
import ProjectStore from '../../../common/stores/project-store';
import ConfirmToggleFeature from '../modals/ConfirmToggleFeature';
import FeatureRow from '../FeatureRow';

const featureNameWidth = 300;

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
            this.fetch();
        }
    }


    fetch =() => {
        this.setState({ isLoading: true });
        AppActions.getFeatures(this.props.match.params.projectId, this.state.environmentLeft);
        return Promise.all([
            this.state.projectFlags ? Promise.resolve({ results: this.state.projectFlags }) : data.get(`${Project.api}projects/${this.props.match.params.projectId}/features/?page_size=999`),
            data.get(`${Project.api}environments/${this.state.environmentLeft}/featurestates/?page_size=999`),
            data.get(`${Project.api}environments/${this.state.environmentRight}/featurestates/?page_size=999`),
        ]).then(([projectFlags, environmentLeftFlags, environmentRightFlags]) => {
            const changes = [];
            const same = [];
            _.each(_.sortBy(projectFlags.results, p => p.name), (projectFlag) => {
                const leftSide = environmentLeftFlags.results.find(v => v.feature === projectFlag.id);
                const rightSide = environmentRightFlags.results.find(v => v.feature === projectFlag.id);
                const change = {
                    projectFlag,
                    leftEnabled: leftSide.enabled,
                    rightEnabled: rightSide.enabled,
                    leftEnvironmentFlag: leftSide,
                    rightEnvironmentFlag: rightSide,
                    leftValue: leftSide.feature_state_value,
                    rightValue: rightSide.feature_state_value,
                };
                change.enabledChanged = change.rightEnabled !== change.leftEnabled;
                change.valueChanged = change.rightValue !== change.leftValue;
                if (change.enabledChanged || change.valueChanged) {
                    changes.push(change);
                } else {
                    same.push(change);
                }
            });
            this.setState({
                environmentLeftFlags: _.keyBy(environmentLeftFlags.results, 'feature'),
                environmentRightFlags: _.keyBy(environmentRightFlags.results, 'feature'),
                changes,
                projectFlags: projectFlags.results,
                isLoading: false,
                same,
            });
        });
    }


    onSave = () => this.fetch()


    render() {
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
                            <EnvironmentSelect ignoreAPIKey={this.state.environmentRight} onChange={environmentLeft => this.setState({ environmentLeft })} value={this.state.environmentLeft}/>
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
                        <FeatureListProvider onSave={this.onSave} onError={this.onError}>
                            {({ isLoading, projectFlags, environmentFlags }, {
                                environmentHasFlag,
                                toggleFlag,
                                editFlag,
                                removeFlag,
                            }) => {
                                const renderRow = (p, i, fadeEnabled, fadeValue) => (
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
                                            <Flex className="mr-2">
                                                <Permission
                                                  level="environment" permission="ADMIN"
                                                  id={this.props.match.params.environmentId}
                                                >
                                                    {({ permission, isLoading }) => (
                                                        <FeatureRow
                                                          condensed
                                                          fadeEnabled={fadeEnabled}
                                                          fadeValue={fadeValue}
                                                          environmentFlags={this.state.environmentLeftFlags}
                                                          projectFlags={this.state.projectFlags}
                                                          permission={permission}
                                                          environmentId={this.state.environmentLeft}
                                                          projectId={this.props.match.params.projectId}
                                                          index={i}
                                                          canDelete={permission}
                                                          toggleFlag={toggleFlag}
                                                          editFlag={editFlag}
                                                          removeFlag={removeFlag}
                                                          projectFlag={p.projectFlag}
                                                        />
                                                    )}
                                                </Permission>
                                            </Flex>
                                            <Flex className="ml-2">
                                                <Permission
                                                  level="environment" permission="ADMIN"
                                                  id={this.props.match.params.environmentId}
                                                >
                                                    {({ permission, isLoading }) => (
                                                        <FeatureRow
                                                          condensed
                                                          fadeEnabled={fadeEnabled}
                                                          fadeValue={fadeValue}
                                                          environmentFlags={this.state.environmentRightFlags}
                                                          projectFlags={this.state.projectFlags}
                                                          permission={permission}
                                                          environmentId={this.state.environmentRight}
                                                          projectId={this.props.match.params.projectId}
                                                          index={i}
                                                          canDelete={permission}
                                                          toggleFlag={toggleFlag}
                                                          editFlag={editFlag}
                                                          removeFlag={removeFlag}
                                                          projectFlag={p.projectFlag}
                                                        />
                                                    )}
                                                </Permission>
                                            </Flex>
                                        </Row>
                                    </div>

                                );
                                return (
                                    <div>
                                        {this.state.isLoading && (
                                            <div className="text-center">
                                                <Loader />
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
                                                                    Changed Flags
                                                                </span>
                                                            </Row>
                                                        )
                                                    }
                                                  header={(
                                                        (
                                                            <Row
                                                              className="mt-2" style={{
                                                                  marginLeft: '0.75rem',
                                                                  marginRight: '0.75rem',
                                                              }}
                                                            >
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
                                                  renderRow={(p, i) => renderRow(p, i, !p.enabledChanged, !p.valueChanged)}
                                                />
                                            </div>
                                        )}
                                        {!this.state.isLoading && (this.state.same && !!this.state.same.length) && (
                                            <div style={{ minWidth: 800 }}>
                                                <div className="mt-4">
                                                    <PanelSearch
                                                      title={
                                                            (
                                                                <Row>
                                                                    <span style={{ width: featureNameWidth }}>
                                                                        Unchanged Flags
                                                                    </span>
                                                                </Row>
                                                            )
                                                        }
                                                      header={(
                                                            (
                                                                <Row
                                                                  className="mt-2" style={{
                                                                      marginLeft: '0.75rem',
                                                                      marginRight: '0.75rem',
                                                                  }}
                                                                >
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
                                                      items={this.state.same}
                                                      renderRow={(p, i) => renderRow(p, i, !p.enabledChanged, !p.valueChanged)}
                                                    />
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                );
                            }
                            }
                        </FeatureListProvider>
                    )
                        : ''
                }
            </div>
        );
    }
}

module.exports = hot(module)(ConfigProvider(TheComponent));
