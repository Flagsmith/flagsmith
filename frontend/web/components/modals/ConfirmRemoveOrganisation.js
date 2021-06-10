import React, { Component } from 'react';

const ConfirmRemoveOrganisation = class extends Component {
    static displayName = 'ConfirmRemoveOrganisation'

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
        const { organisation } = this.props;
        e.preventDefault();
        if (this.state.challenge == organisation.name) {
            this.close();
            this.props.cb();
        }
    };

    render() {
        const { organisation } = this.props;
        return (
            <ProjectProvider>
                {() => (
                    <form onSubmit={this.submit}>
                        <p>
                            This will remove
                            {' '}
                            <strong>{organisation.name}</strong>
                            {' '}
                            and
                            {' '}
                            <strong>
                                all of it's
                                projects
                            </strong>
                            . You should ensure that you do not contain any references to this
                            organisation in your applications before proceeding.

                        </p>
                        <InputGroup
                          inputProps={{ name: 'confirm-org-name', className: 'full-width' }}
                          title="Please type the organisation name to confirm"
                          placeholder="Organisation name"
                          onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                        />

                        <FormGroup className="text-right">
                            <Button
                              id="confirm-del-org-btn"
                              disabled={this.state.challenge != organisation.name}
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

ConfirmRemoveOrganisation.propTypes = {};

module.exports = ConfirmRemoveOrganisation;
