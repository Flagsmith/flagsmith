import React, { Component, PropTypes } from 'react';

const ConfirmRemoveTrait = class extends Component {
    static displayName = 'ConfirmRemoveTrait'

    static propTypes = {
        trait_key: propTypes.string,
    }

    state = {};

    close() {
        closeModal();
    }

    submit = (e) => {
        const { trait_key } = this.props;
        e.preventDefault();
        if (this.state.challenge === trait_key) {
            this.close();
            this.props.cb();
        }
    };

    render() {
        const { trait_key } = this.props;
        return (
            <ProjectProvider>
                {() => (
                    <form id="confirm-remove-trait-modal" onSubmit={this.submit}>
                        <p>
                            This will remove trait
                            {' '}
                            <strong>{trait_key}</strong>
                            {' '}
                            for
                            {' '}
                            <strong>
                            all
                            users
                            </strong>
                            .
                        </p>

                        <InputGroup
                          inputProps={{ name: 'confirm-trait-key', className: 'full-width' }}
                          title="Please type the trait ID to confirm"
                          placeholder="Trait ID"
                          onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                        />

                        <FormGroup className="text-right">
                            <Button
                              id="confirm-remove-trait-btn"
                              disabled={this.state.challenge !== trait_key}
                              className="btn btn-primary"
                            >
                                Confirm
                            </Button>
                        </FormGroup>
                    </form>
                )}
            </ProjectProvider>
        );
    }
};

module.exports = ConfirmRemoveTrait;
