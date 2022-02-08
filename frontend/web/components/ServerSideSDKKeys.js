import React from 'react';
import { Component } from 'react';
import _data from '../../common/data/base/_data'
import ProjectStore from '../../common/stores/project-store'
class CreateServerSideKeyModal extends Component {
    state = {}

    componentDidMount() {
        setTimeout(()=>{
            document.getElementById("jsTokenName").focus()
        },500)
    }

    onSubmit = (e)=>{
        Utils.preventDefault(e)
        if(this.state.name) {
            this.setState({
                isSaving:true
            })
            this.props.onSubmit(this.state.name)
        }
    }

    render() {
        return <div>
            <form onSubmit={this.onSubmit}>
                <div className="mb-2">
                    This will create a ServerSide SDK Key for the environment <strong>{ProjectStore.getEnvironment(this.props.environmentId).name }</strong>.
                </div>
                <InputGroup
                    title="Key Name"
                    placeholder="New Key"
                    className="mb-2"
                    id="jsTokenName"
                    inputProps={{
                        className: 'full-width modal-input',
                    }}
                    onChange={e => this.setState({ name: Utils.safeParseEventValue(e) })}
                />
                <div className="text-right">
                    <Button disabled={!this.state.name||this.state.isSaving} className="mb-2">Create</Button>
                </div>
            </form>

        </div>
    }
}

class ServerSideSDKKeys extends Component {
    state = {
        isLoading:true
    }
    static propTypes = {
        environmentId: propTypes.string.isRequired
    }
    componentDidMount() {
        this.fetch(this.props.environmentId)
    }
    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps.environmentId !== this.props.environmentId) {
             this.fetch(this.props.environmentId)
        }
    }
    createKey = ()=>{
        this.setState({isSaving:true})

        openModal("Create Serverside SDK Key", <CreateServerSideKeyModal environmentId={this.props.environmentId} onSubmit={(name)=>{
            _data.post(`${Project.api}environments/${this.props.environmentId}/api-keys/`,{name})
                .then(()=>this.fetch(this.props.environmentId))
                .finally(()=>{
                    closeModal()
                    this.setState({isSaving:false})
                })
        }
        }/>)
    }
    remove = (id,name)=>{

        openConfirm(<h3>Server Side SDK Key</h3>, <p>
            The key <strong>{name}</strong> will be permanently deleted, are you sure?
        </p>, () => {
            this.setState({isSaving:true})
            _data.delete(`${Project.api}environments/${this.props.environmentId}/api-keys/${id}`)
                .then(()=>this.fetch(this.props.environmentId))
                .finally(()=>{
                    this.setState({isSaving:false})
                })
        });
    }
    fetch = (environmentId)=>{
        this.setState({isLoading:true})
        return _data.get(`${Project.api}environments/${environmentId}/api-keys/`)
            .then((keys)=>{
                this.setState({keys,isLoading:false})
            }).catch((e)=>{
                this.setState({isLoading:false})
            })
    }

    render() {
        return (
            <div className={"mt-2"}>
                <div className="text-center">
                    <Button onClick={this.createKey} disabled={this.state.isSaving}>Create Server Side SDK Key</Button>
                </div>
                {this.state.isLoading && <div className="text-cetner"><Loader/></div> }
                {this.state.keys && !!this.state.keys.length && (
                    <PanelSearch
                        id="org-members-list"
                        title="Keys"
                        className="mt-5 no-pad"
                        items={this.state.keys}
                        filterRow={(item, search) => {
                            const strToSearch = `${item.name}`;
                            return strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1;
                        }}
                        renderRow={({ id, name }) => (
                            <div className="list-item">
                                <Row>
                                    <Flex>
                                        {name}
                                    </Flex>
                                    <button
                                        onClick={()=>this.remove(id,name)}
                                        disabled={this.state.isSaving}
                                        id="remove-feature"
                                        className="btn btn--with-icon"
                                    >
                                        <RemoveIcon/>
                                    </button>
                                </Row>
                            </div>
                        )}
                        />
                    )}
        </div>
        )
    }
}

export default ServerSideSDKKeys
