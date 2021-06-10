import React, { Component } from 'react';

const CreateAuditWebhook = class extends Component {
    static displayName = 'CreateAuditWebhook'

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
        const { url } = this.props;
        e.preventDefault();
        if (this.state.challenge == url) {
            this.close();
            this.props.cb();
        }
    };

    render() {
        const { url } = this.props;
        return (
            <form id="confirm-remove-feature-modal" onSubmit={this.submit}>
                <p>
                            This will remove
                    {' '}
                    <strong>{url}</strong>
                    {' '}for the organisation{' '}
                    <strong>
                        {AccountStore.getOrganisation().name}
                    </strong>
                            . You should ensure that you do not contain any references to this
                            webhook in your applications before proceeding.
                </p>

                <InputGroup
                  inputProps={{ name: 'confirm-feature-name', className: 'full-width' }}
                  title="Please type the webhook url to confirm"
                  placeholder="webhook url"
                  onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                />

                <FormGroup className="text-right">
                    <Button
                      id="confirm-remove-feature-btn"
                      disabled={this.state.challenge != url}
                      className="btn btn-primary"
                    >
                                Confirm changes

                    </Button>
                </FormGroup>
            </form>
        );
    }
};

CreateAuditWebhook.propTypes = {};

module.exports = CreateAuditWebhook;
