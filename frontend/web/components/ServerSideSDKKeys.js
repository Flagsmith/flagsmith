import React from 'react';
import { Component } from 'react';
import _data from '../../common/data/base/_data';
import ProjectStore from '../../common/stores/project-store';
import Token from './Token';

class CreateServerSideKeyModal extends Component {
    state = {}

    componentDidMount() {
        setTimeout(() => {
            document.getElementById('jsTokenName').focus();
        }, 500);
    }

    onSubmit = (e) => {
        Utils.preventDefault(e);
        if (this.state.name) {
            this.setState({
                isSaving: true,
            });
            this.props.onSubmit(this.state.name);
        }
    }

    render() {
        return (
            <div>
                <form onSubmit={this.onSubmit}>
                    <div className="mb-2">
                        This will create a Server-side Environment Key for the environment <strong>{ProjectStore.getEnvironment(this.props.environmentId).name}</strong>.
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
                        <Button disabled={!this.state.name || this.state.isSaving} className="mb-2">Create</Button>
                    </div>
                </form>

            </div>
        );
    }
}

class ServerSideSDKKeys extends Component {
    state = {
        isLoading: true,
    }

    static propTypes = {
        environmentId: propTypes.string.isRequired,
    }

    componentDidMount() {
        this.fetch(this.props.environmentId);
    }

    componentDidUpdate(prevProps, prevState, snapshot) {
        if (prevProps.environmentId !== this.props.environmentId) {
            this.fetch(this.props.environmentId);
        }
    }

    createKey = () => {
        openModal('Create Server-side Environment Keys', <CreateServerSideKeyModal
            environmentId={this.props.environmentId} onSubmit={(name) => {
                _data.post(`${Project.api}environments/${this.props.environmentId}/api-keys/`, { name })
                    .then(() => this.fetch(this.props.environmentId))
                    .finally(() => {
                        closeModal();
                    });
            }
            }
        />);
    }

    remove = (id, name) => {
        openConfirm(<h3>Delete Server-side Environment Keys</h3>, <p>
            The key <strong>{name}</strong> will be permanently deleted, are you sure?
        </p>, () => {
            this.setState({ isSaving: true });
            _data.delete(`${Project.api}environments/${this.props.environmentId}/api-keys/${id}`)
                .then(() => this.fetch(this.props.environmentId))
                .finally(() => {
                    this.setState({ isSaving: false });
                });
        });
    }

    fetch = (environmentId) => {
        this.setState({ isLoading: true });
        return _data.get(`${Project.api}environments/${environmentId}/api-keys/`)
            .then((keys) => {
                this.setState({ keys, isLoading: false });
            }).catch((e) => {
                this.setState({ isLoading: false });
            });
    }

    render() {
        return (
            <FormGroup className="m-y-3">
                <Row className="mb-3" space>
                    <div className="col-md-8 pl-0">
                        <h3 className="m-b-0">Server-side Environment Keys</h3>
                        <p>Flags can be evaluated locally within your own Server environments using
                        our <a href="https://docs.flagsmith.com/clients/overview" target="__blank">Server-side Environment Keys</a>.</p>
                        <p>Server-side SDKs should be initialised with a Server-side Environment Key.</p>
                    </div>
                    <div className="col-md-4 pr-0">
                        <Button onClick={this.createKey} className="float-right" disabled={this.state.isSaving}>Create Server-side Environment Key</Button>
                    </div>
                </Row>
                {this.state.isLoading && <div className="text-center"><Loader /></div>}
                {this.state.keys && !!this.state.keys.length && (
                    <PanelSearch
                        id="org-members-list"
                        title="Server-side Environment Keys"
                        className="no-pad"
                        items={this.state.keys}
                        filterRow={(item, search) => {
                            const strToSearch = `${item.name}`;
                            return strToSearch.toLowerCase().indexOf(search.toLowerCase()) !== -1;
                        }}
                        renderRow={({ id, name, key }) => (
                            <div className="list-item">
                                <Row>
                                    <Flex>
                                        {name}
                                    </Flex>
                                    <Token style={{ width: 280 }} token={key} />
                                    <button
                                        onClick={() => this.remove(id, name)}
                                        disabled={this.state.isSaving}
                                        id="remove-feature"
                                        className="btn btn--with-icon"
                                    >
                                        <RemoveIcon />
                                    </button>
                                </Row>
                            </div>
                        )}
                    />
                )}
            </FormGroup>
        );
    }
}

export default ServerSideSDKKeys;
