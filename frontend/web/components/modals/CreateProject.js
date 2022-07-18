import React, { Component } from 'react';
import InfoMessage from "../InfoMessage";
import PaymentModal from "./Payment";

const CreateProject = class extends Component {
    static displayName = 'CreateProject'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    close = (id) => {
        closeModal();
        this.props.onSave(id);
    }

    componentDidMount = () => {
        this.focusTimeout = setTimeout(() => {
            this.input.focus();
            this.focusTimeout = null;
        }, 500);
    };

    componentWillUnmount() {
        if (this.focusTimeout) {
            clearTimeout(this.focusTimeout);
        }
    }

    render() {
        const { name } = this.state;
        return (
            <OrganisationProvider onSave={this.close}>
                {({ isLoading, isSaving, projects, createProject, error }) => {
                    const hasProject = !!projects && !!projects.length
                    const canCreate = !!Utils.getPlansPermission("CREATE_ADDITIONAL_PROJECT")
                    const disableCreate = !canCreate && hasProject;

                    return (
                        <div>

                            {disableCreate && (
                                <InfoMessage>
                                    View and manage multiple projects in your organisation with the <a
                                    href="#" onClick={() => {
                                    openModal('Payment plans', <PaymentModal
                                        viewOnly={false}
                                    />, null, { large: true });
                                }}
                                >
                                    Startup plan
                                </a>
                                </InfoMessage>
                            )}
                            <form
                                style={{opacity:disableCreate?0.5:1}}
                                data-test="create-project-modal"
                                id="create-project-modal" onSubmit={(e) => {
                                if(disableCreate) {
                                    return
                                }
                                e.preventDefault();
                                !isSaving && name && createProject(name);
                            }}
                            >

                                <InputGroup
                                    ref={e => this.input = e}
                                    data-test="projectName"
                                    disabled={disableCreate}
                                    inputProps={{ name: 'projectName', className: 'full-width' }}
                                    onChange={e => this.setState({ name: Utils.safeParseEventValue(e) })}
                                    isValid={name && name.length}
                                    type="text" title="Project Name*"
                                    placeholder="My Product Name"
                                />
                                {error && <Error error={error}/>}
                                <div className="text-right">
                                    <Button data-test="create-project-btn" className="mt-3" id="create-project-btn" disabled={isSaving || !name}>
                                        {isSaving ? 'Creating' : 'Create Project'}
                                    </Button>
                                </div>
                            </form>
                        </div>

                    )
                }}

            </OrganisationProvider>
        );
    }
};

CreateProject.propTypes = {};

module.exports = CreateProject;
