import React, { Component } from 'react';

const ConfirmRemoveFeature = class extends Component {
    static displayName = 'ConfirmRemoveFeature'

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
        const { projectFlag } = this.props;
        e.preventDefault();
        if (this.state.challenge == projectFlag.name) {
            this.close();
            this.props.cb();
        }
    };

    render() {
        const { projectFlag, identity } = this.props;
        return (
            <ProjectProvider>
                {() => (
                    <form id="confirm-remove-feature-modal" onSubmit={this.submit}>
                        {identity ? (
                            <p>
                                This will reset
                                {' '}
                                <strong>{projectFlag.name}</strong>
                                {' '}
                                for to the environment defaults
                                for the user
                                {' '}
                                <strong>{identity}</strong>
                            </p>
                        ) : (
                            <p>
                                This will remove
                                {' '}
                                <strong>{projectFlag.name}</strong>
                                {' '}
                                for
                                {' '}
                                <strong>
                                    all
                                    environments
                                </strong>
                                . You should ensure that you do not contain any references to this
                                feature in your applications before proceeding.

                            </p>
                        )}

                        <InputGroup
                          inputProps={{ name: 'confirm-feature-name', className: 'full-width' }}
                          title="Please type the feature name to confirm"
                          placeholder="feature_name"
                          onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                        />

                        <FormGroup className="text-right mt-2">
                            <Button
                              id="confirm-remove-feature-btn"
                              disabled={this.state.challenge != projectFlag.name}
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

ConfirmRemoveFeature.propTypes = {};

module.exports = ConfirmRemoveFeature;
