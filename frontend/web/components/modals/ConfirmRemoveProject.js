import React, { Component } from 'react';

const ConfirmRemoveProject = class extends Component {
    static displayName = 'ConfirmRemoveProject'

    constructor(props, context) {
        super(props, context);
        this.state = {
            name: props.name,
        };
    }

    close() {
        closeModal();
    }

    submit = (e) => {
        const { project } = this.props;
        e.preventDefault();
        if (this.state.challenge == project.name) {
            this.close();
            this.props.cb();
        }
    };

    render() {
        const { project } = this.props;
        return (
            <ProjectProvider>
                {() => (
                    <form onSubmit={this.submit}>
                        <p>
                            This will remove
                            {' '}
                            <strong>{project.name}</strong>
                            {' '}
                            and
                            {' '}
                            <strong>
                                all
                                environments
                            </strong>
                            . You should ensure that you do not contain any references to this
                            project in your applications before proceeding.

                        </p>
                        <InputGroup
                          inputProps={{ className: 'full-width' }}
                          title="Please type the project name to confirm"
                          placeholder="Project name"
                          onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                        />

                        <FormGroup className="text-right">
                            <Button
                              disabled={this.state.challenge != project.name}
                              className="btn btn-primary"
                            >
                                Confirm changes

                            </Button>
                        </FormGroup>
                    </form>
                )}
            </ProjectProvider>
        );
    }
};

ConfirmRemoveProject.propTypes = {};

module.exports = ConfirmRemoveProject;
