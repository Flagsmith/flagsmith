import React, { Component } from 'react';

const ConfirmRemoveEnvironment = class extends Component {
    static displayName = 'ConfirmRemoveEnvironment'

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
        const { environment } = this.props;
        e.preventDefault();
        if (this.state.challenge == environment.name) {
            this.close();
            this.props.cb();
        }
    };

    render() {
        const { environment } = this.props;
        return (
            <ProjectProvider>
                {() => (
                    <form onSubmit={this.submit}>
                        <p>
                            This will remove the environment
                            {' '}
                            <strong>{environment.name}</strong>
                            {' '}
                            from your project. You should ensure that you do not contain any references to this
                            environment in your applications before proceeding.

                        </p>
                        <InputGroup
                          inputProps={{ name: 'confirm-env-name', className: 'full-width' }}
                          title="Please type the environment name to confirm"
                          placeholder="Environment name"
                          onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                        />

                        <FormGroup className="text-right">
                            <Button
                              id="confirm-delete-env-btn"
                              disabled={this.state.challenge != environment.name}
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

ConfirmRemoveEnvironment.propTypes = {};

module.exports = ConfirmRemoveEnvironment;
