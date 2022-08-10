import React from 'react';
import { Component } from 'react';
import _data from '../../../common/data/base/_data'
import ProjectStore from '../../../common/stores/project-store'
import { groupBy } from "lodash";
import TagValues from "../TagValues";
import SegmentOverrides from "../SegmentOverrides";
import withSegmentOverrides from "../../../common/providers/withSegmentOverrides";
import FeatureListStore from "../../../common/stores/feature-list-store";
import FlagSelect from "../FlagSelect";
import { ButtonLink } from "../base/forms/Button";
import InfoMessage from "../InfoMessage";
import SegmentStore from '../../../common/stores/segment-list-store'
class TheComponent extends Component {
    state = {
        isLoading: true
    }

    componentDidMount() {
        this.fetch()
    }

    fetch = () => {
        _data.get(`${Project.api}projects/${this.props.projectId}/segments/${this.props.id}/associated-features/`).then((v)=>{
            return Promise.all((v.results.map((result)=>{
                return _data.get(`${Project.api}projects/${this.props.projectId}/features/${result.feature}/`)
                    .then((feature)=>{
                        result.feature = feature
                    })
            }))).then(()=>{
                return groupBy(v.results,(e)=>{
                    const env = ProjectStore.getEnvs().find((v)=>v.id === e.environment)
                    e.env = env
                    return env && env.name
                })
            }).then((v)=>{
                if(v.undefined) {
                    delete v.undefined
                }
                const keys = Object.keys(v)
                _.each(Object.keys(v), (key)=>{
                    v[key] = _.sortBy(v[key], (val)=>{
                        return val.feature.name
                    })
                })
                const newItems = this.state.newItems || {}
                const selectedEnv = this.state.selectedEnv || ProjectStore.getEnvs()[0].name
                AppActions.getSegments(this.props.projectId, ProjectStore.getEnvs()[0].api_key);

                newItems[selectedEnv] = (newItems[selectedEnv]||[]).filter((newItem)=>{
                    const existingSegmentOverride = !!v[selectedEnv] && v[selectedEnv].find((s)=>newItem.feature.id === s.feature.id)
                    return !existingSegmentOverride
                })
                this.setState({isLoading: false, newItems, results:v, selectedEnv  })
            })
        })
    }

    addItem = (item)=>{
        const newItems = this.state.newItems || {}
        newItems[this.state.selectedEnv] = newItems[this.state.selectedEnv] || []
        newItems[this.state.selectedEnv].unshift(item)
        this.setState({
            newItems
        })
    }


    render() {
        const results = this.state.results
        const newItems = this.state.newItems
        const hasResults = results && Object.keys(results).length
        const selectedNewResults = (newItems && newItems[this.state.selectedEnv] ) || []

        const selectedResults = selectedNewResults.concat((results && results[this.state.selectedEnv]) || [])
        const addOverride =
            <div style={{width:300}} className="p-2 ml-2">
                <WrappedSegmentOverrideAdd
                    onSave={this.fetch}
                    addItem={this.addItem}
                    selectedResults={selectedResults}
                    ignoreFlags={selectedResults && selectedResults.map((v)=>v.feature.id)}
                    id={this.props.id}
                    projectId={this.props.projectId}
                    environmentId={this.state.selectedEnv}
                />
            </div>

        return this.state.isLoading ? <div className="text-center">
            <Loader/>
        </div> : (
            <div className="mt-4">
                <InfoMessage>
                    This shows the list of segment overrides associated with this segment.
                </InfoMessage>
                    <div >

                     <div className="mt-4 mb-4" style={{width:250}}>
                         <Select
                             value={{
                             value: this.state.selectedEnv,
                             label: this.state.selectedEnv
                         }}
                                 onChange={(v)=>{
                                     this.setState({selectedEnv:v.value})
                                 }}
                                 options={ProjectStore.getEnvs().map((v)=>({
                                     label:v.name,
                                     value: v.name
                                 }))}
                         />

                     </div>
                        <PanelSearch
                            header={addOverride}
                            search={this.state.search}
                            onChange={(search)=>this.setState({search})}
                            filterRow={(row,search)=>{
                                return row.feature.name.toLowerCase().includes(search.toLowerCase())
                            }}
                            className="no-pad" title="Associated Features"
                            items={selectedResults}
                            renderNoResults={<Panel className="no-pad" title={"Associated Features"}>
                                {addOverride}
                                <div className="p-2 text-center">
                                    There are no segment overrides in this environment
                                </div>
                        </Panel>}
                            renderRow={(v)=>(
                                <div key={v.feature.id} className="m-3 mb-4">
                                <div onClick={()=>{
                                    // window.open(`${document.location.origin}/project/${this.props.projectId}/environment/${v.env.api_key}/features?feature=${v.feature.id}&tab=1`)
                                }} className="list-item panel panel-without-heading py-3 clickable">
                                    <div>
                                        <strong>
                                            {v.feature.name}
                                        </strong>
                                    </div>
                                    <div className="list-item-footer faint">
                                        <Row>
                                            <div>
                                                Created {moment(v.feature.created_date).format('Do MMM YYYY HH:mma')}{' - '}
                                                {v.feature.description || 'No description'}
                                            </div>
                                        </Row>
                                    </div>

                                    <WrappedSegmentOverrides
                                        onSave={this.fetch}
                                        projectFlag={v.feature}
                                        newSegmentOverrides={v.newSegmentOverrides}
                                        onRemove={()=>{
                                            if(v.newSegmentOverrides) {
                                                newItems[this.state.selectedEnv] = newItems[this.state.selectedEnv].filter((x) => {
                                                    return x !== v
                                                })
                                                this.setState({
                                                    newItems
                                                })
                                            }
                                        }}
                                        id={this.props.id}
                                        projectId={this.props.projectId}
                                        environmentId={v.env.api_key}
                                    />

                                </div>
                                </div>
                            )}
                        />
                    </div>
            </div>
        )
    }
}



class UncontrolledSegmentOverrides extends Component  {

    constructor(props) {
        super(props);
        this.state = {
            value: this.props.value
        }
    }
    onChange = (value)=>{
        this.setState({value})
        this.props.onChange(value)
    }
    render() {

        return  <SegmentOverrides
            {...this.props}
            onChange={this.onChange}
            value={this.state.value}
        />;
    }
}

export default

class SegmentOverridesInner extends Component {
    state = {}

    componentDidMount() {
        ES6Component(this)
    }

    openPriorities = () => {
        const {projectFlag, id, originalSegmentOverrides, segmentOverrides, projectId,updateSegments,segments, ignoreFlags, environmentId} = this.props;
        const arrayMoveMutate = (array, from, to) => {
            array.splice(to < 0 ? array.length + to : to, 0, array.splice(from, 1)[0]);
        };
        const arrayMove = (array, from, to) => {
            array = array.slice();
            arrayMoveMutate(array, from, to);
            return array;
        };
        const overrides =  originalSegmentOverrides.filter((v)=>{
            return v.segment!==segmentOverrides[0].segment;
        }).concat([segmentOverrides[0]])
        openModal2("Edit Segment Override Priorities", (
            <div>
                <UncontrolledSegmentOverrides
                    feature={projectFlag.id}
                    segments={SegmentStore.model}
                    readOnly
                    projectId={projectId}
                    multivariateOptions={_.cloneDeep(projectFlag.multivariate_options)}
                    environmentId={environmentId}
                    value={arrayMove(overrides, overrides.length-1,overrides[overrides.length-1].priority)}
                    controlValue={projectFlag.feature_state_value}
                    onChange={updateSegments}
                />
                <div className="text-right">
                    <Button onClick={()=>{closeModal2()}}>
                        Done
                    </Button>
                </div>
            </div>
        ))
    }

    render() {

        const {projectFlag, id, segmentOverrides, projectId,updateSegments,segments,originalSegmentOverrides, ignoreFlags, environmentId} = this.props;


            return (
                <FeatureListProvider>
                    {({}, {editFlagSegments, isSaving})=> {

                        const save = ()=> {
                            FeatureListStore.isSaving = true;
                            FeatureListStore.trigger('change');
                            !isSaving && editFlagSegments(projectId, environmentId, projectFlag, projectFlag, { }, segmentOverrides, ()=>{
                                toast("Segment override saved")
                                this.setState({isSaving: false})
                                this.props.onSave()
                            });
                            this.setState({isSaving: true})

                        }
                        const segmentOverride = segmentOverrides && segmentOverrides.filter((v)=> {
                                return v.segment === id
                            }
                        )
                        if (!segmentOverrides) return  null
                        return (
                            <div>
                                {originalSegmentOverrides.length >1 && (
                                    <div style={{width:150}}>
                                    <Tooltip title={(
                                        <div className="chip mt-2">
                                            Priority: {segmentOverride && segmentOverride[0].priority+1} of {originalSegmentOverrides.length}

                                                <a href="#" className="font-weight-bold" className="ml-2" onClick={this.openPriorities}>
                                                    Edit
                                                </a>
                                        </div>

                                    )}>
                                        If a user belongs to more than 1 segment, overrides are determined by this priority.
                                    </Tooltip>
                                    </div>

                                )}



                                <SegmentOverrides
                                    feature={projectFlag.id}
                                    id={id}
                                    name={" "}
                                    projectId={projectId}
                                    onRemove={this.props.onRemove}
                                    multivariateOptions={_.cloneDeep(projectFlag.multivariate_options)}
                                    environmentId={environmentId}

                                    value={ segmentOverride}
                                    controlValue={projectFlag.feature_state_value}
                                    onChange={updateSegments}
                                />
                                <div className="text-right">
                                    <Button disabled={this.state.isSaving} onClick={save}>
                                        {this.state.isSaving? "Saving": "Save"}
                                    </Button>
                                </div>

                            </div>

                        )
                    }}
                </FeatureListProvider>


            )
    }
}

class SegmentOverridesInnerAdd extends Component {
    state = {}

    componentDidMount() {
        ES6Component(this)
    }

    render() {

        const {projectFlag, id, segmentOverrides, projectId, ignoreFlags, environmentId} = this.props;

        const value = segmentOverrides && segmentOverrides.filter((v)=> {
                return v.segment === id
            }
        )

        const addValue = (featureId, feature)=>{
            const env = ProjectStore.getEnvs().find((v)=>v.name === environmentId)
            const item = {
                env,
                environment: environmentId,
                feature,
                isNew: true,
                newSegmentOverrides: [
                    {
                        feature: featureId,
                        segment: id,
                        environment: env.id,
                        priority: 999,
                        feature_segment_value: {
                            enabled: false,
                            feature: featureId,
                            environment: env.id,
                            feature_segment: null,
                            feature_state_value: Utils.valueToFeatureState(''),
                        },
                    }
                ]
            }
            this.props.addItem(item);
            // const newValue = ;
            // updateSegments(segmentOverrides.concat([newValue]))
        }

            return (
                <FeatureListProvider>
                    {({}, {editFlagSegments, isSaving})=> {

                        const save = ()=> {
                            FeatureListStore.isSaving = true;
                            FeatureListStore.trigger('change');
                            !isSaving && editFlagSegments(projectId, environmentId, projectFlag, projectFlag, { }, segmentOverrides, ()=>{
                                toast("Segment override saved")
                                this.setState({isSaving: false})
                                this.props.onSave()
                            });
                            this.setState({isSaving: true})

                        }

                        return (
                            <div className="mt-2">
                               <FlagSelect placeholder="Create a Segment Override..." projectId={projectId} ignore={ignoreFlags} onChange={addValue}/>

                            </div>

                        )
                    }}
                </FeatureListProvider>


            )
    }
}

const WrappedSegmentOverrides  = withSegmentOverrides(SegmentOverridesInner)

const WrappedSegmentOverrideAdd  = withSegmentOverrides(SegmentOverridesInnerAdd)


module.exports = ConfigProvider(TheComponent);
