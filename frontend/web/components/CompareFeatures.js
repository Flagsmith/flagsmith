// import propTypes from 'prop-types';
import React, { Component } from 'react';
import FlagSelect from "./FlagSelect";
import ProjectStore from '../../common/stores/project-store'
import FeatureListStore from '../../common/stores/feature-list-store'
import data from "../../common/data/base/_data";
import FeatureRow from "./FeatureRow";
const featureNameWidth = 300;

class CompareEnvironments extends Component {
    static displayName = 'CompareEnvironments';

    static propTypes = {};

    static contextTypes = {
        router: propTypes.object.isRequired,
    };

    constructor(props) {
        super();
        this.state = {
            flagId: '',
            selectedIndex: 0
            // isLoading: true,
        };
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        ES6Component(this)
        this.listenTo(FeatureListStore, 'saved', ()=>{
            toast('Saved')
            this.fetch()
        })
        if (this.state.flagId !== prevState.flagId) {
            this.fetch();
        }
    }


    fetch =() => {
        if (this.state.flagId) {

            Promise.all([
                data.get(`${Project.api}projects/${this.props.projectId}/features/${this.state.flagId}`),
            ].concat(ProjectStore.getEnvs().map((v)=>(
                data.get(`${Project.api}environments/${v.api_key}/featurestates/?feature=${this.state.flagId}`)
            )))).then(([_flag,...rest])=>{
                const flag = _flag;
                const environmentResults = ProjectStore.getEnvs().map((env,i)=>{
                    const flags = {};
                    flags[flag.id] = rest[i].results[0]
                    return flags
                })
                 this.setState({
                     environmentResults,
                     flag,
                     isLoading: false
                 })
            })
        }
    }


    onSave = () => this.fetch()


    render() {
        return (
            <div>
                <h3>
                    Compare Feature Values
                </h3>
                <p>
                    Compare a feature's value across all of your environments. Select an environment to compare against others.
                </p>
                <Row>
                    <Row>
                        <div style={{ width: featureNameWidth }}>
                            <FlagSelect placeholder="Select a Feature..." projectId={this.props.projectId} onChange={(flagId, flag) => this.setState({ flag, isLoading:true, flagId })} value={this.state.flagId}/>
                        </div>
                    </Row>
                </Row>
                {this.state.flagId && (

                    <div>
                    <FeatureListProvider onSave={this.onSave} onError={this.onError}>
                        {({  }, {
                            environmentHasFlag,
                            toggleFlag,
                            editFlag,
                            removeFlag,
                        }) => {

                            const renderRow = (data,i) => {
                                const flagValues = this.state.environmentResults[i];
                                const compare = this.state.environmentResults[this.state.selectedIndex]
                                const flagA = flagValues[this.state.flagId]
                                const flagB = compare[this.state.flagId]
                                const fadeEnabled = flagA.enabled == flagB.enabled;
                                const fadeValue = flagB.feature_state_value == flagA.feature_state_value;
                                return (
                                    <Permission
                                        level="environment" permission={Utils.getManageFeaturePermission()}
                                        id={data.api_key}
                                    >
                                        {({ permission, isLoading }) => (

                                            <div className="list-item clickable mb-2">
                                                <Row className="relative">
                                                    <div style={{zIndex:1}}>
                                                        <Row>
                                                            <div
                                                                onMouseDown={(e) => {
                                                                    e.stopPropagation();
                                                                    this.setState({selectedIndex:i})
                                                                }}
                                                                className={`btn--radio ion ${this.state.selectedIndex === i ? 'ion-ios-radio-button-on' : 'ion-ios-radio-button-off'}`}
                                                            />
                                                            <strong>
                                                                {data.name}
                                                            </strong>
                                                        </Row>

                                                    </div>
                                                    <Row>
                                                        <FeatureRow
                                                            style={{
                                                                zIndex:0,
                                                                position: "absolute",
                                                                display: "flex",
                                                                justifyContent: "flex-end",
                                                                left: 0,
                                                                right: 0,
                                                            }}
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
                                                            editFlag={editFlag}
                                                            removeFlag={removeFlag}
                                                            projectFlag={this.state.flag}
                                                        />
                                                    </Row>

                                                </Row>

                                            </div>
                                        )}
                                    </Permission>
                                );
                            }
                            return (
                                <div>
                                    {this.state.isLoading && <div className={"text-center"}><Loader/></div>}
                                    {!this.state.isLoading && <div>
                                        <PanelSearch
                                            className={"mt-4"}
                                            title={
                                                (
                                                    <Row>
                                                        <span style={{ width: featureNameWidth }}>
                                                            Feature Values
                                                        </span>
                                                    </Row>
                                                )
                                            }
                                            items={ProjectStore.getEnvs()}
                                            renderRow={renderRow}
                                        />

                                    </div>}
                                </div>
                            )

                        }}
                    </FeatureListProvider>
                    </div>
                )}
            </div>
        );
    }
}

module.exports = hot(module)(ConfigProvider(CompareEnvironments));
