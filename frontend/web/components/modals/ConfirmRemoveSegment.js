import React, { Component } from 'react';

const ConfirmRemoveSegment = class extends Component {
    static displayName = 'ConfirmRemoveSegment'

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
        const { segment } = this.props;
        e.preventDefault();
        if (this.state.challenge == segment.name) {
            this.close();
            this.props.cb();
        }
    };

    render() {
        const { segment } = this.props;
        return (
            <ProjectProvider>
                {() => (
                    <form id="confirm-remove-segment-modal" onSubmit={this.submit}>
                        <p>
                            This will remove
                            {' '}
                            <strong>{segment.name}</strong>
                            {' '}
                            for
                            {' '}
                            <strong>
                                all
                                environments
                            </strong>
                            . You should ensure that you do not contain any references to this
                            segment in your applications before proceeding.
                        </p>

                        <InputGroup
                          inputProps={{ name: 'confirm-segment-name', className: 'full-width' }}
                          title="Please type the segment name to confirm"
                          placeholder="segment_name"
                          onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                        />

                        <FormGroup className="text-right">
                            <Button
                              id="confirm-remove-segment-btn"
                              disabled={this.state.challenge != segment.name}
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

ConfirmRemoveSegment.propTypes = {};

module.exports = ConfirmRemoveSegment;
