import React from 'react';
import { Component } from 'react';
import _data from '../../../common/data/base/_data'
import ProjectStore from '../../../common/stores/project-store'
import { groupBy } from "lodash";
import TagValues from "../TagValues";
class TheComponent extends Component {
    state = {
        isLoading: true
    }

    componentDidMount() {
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
                this.setState({isLoading: false, results:v, selectedEnv: keys && keys.length && keys.sort()[0] })
            })
        })
    }

    render() {
        const results = this.state.results
        const hasResults = results && Object.keys(results).length
        const selectedResults = results && results[this.state.selectedEnv]
        return this.state.isLoading ? <div className="text-center">
            <Loader/>
        </div> : (
            <div>
                {!hasResults && <div>
                    There are no features using this segment
                </div>}
                {!!hasResults && (
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
                                 options={results && Object.keys(results).sort().map((v)=>({
                                     label:v,
                                     value:v
                                 }))}
                         />

                     </div>
                        <PanelSearch
                            search={this.state.search}
                            onChange={(search)=>this.setState({search})}
                            filterRow={(row,search)=>{
                                return row.feature.name.toLowerCase().includes(search.toLowerCase())
                            }}
                            className="no-pad" title="Associated Features"
                            items={selectedResults}
                            renderRow={(v)=>(
                                <div onClick={()=>{
                                    window.open(`${document.location.origin}/project/${this.props.projectId}/environment/${v.env.api_key}/features?feature=${v.feature.id}&tab=1`)
                                }} className="list-item py-3 clickable">
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

                                </div>
                            )}
                        />
                    </div>
                )}
            </div>
        )
    }
}

export default TheComponent
