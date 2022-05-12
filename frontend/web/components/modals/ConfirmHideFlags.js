import React, { Component } from 'react';

const ConfirmHideFlags = class extends Component {
    static displayName = 'ConfirmHideFlags'

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
            <form onSubmit={this.submit}>
                <p>
                            This will <strong>{this.props.value ? 'show' : 'hide'}</strong> disabled flags
                    {' '}

                    {' '}
                            for
                    {' '}
                    <strong>
                                all
                                environments
                    </strong>
                    {' '}
                    within the project <strong>{project.name}</strong>
                            .

                </p>
                <InputGroup
                  data-test="js-project-name"
                  inputProps={{ className: 'full-width' }}
                  title="Please type the project name to confirm"
                  placeholder="Project name"
                  onChange={e => this.setState({ challenge: Utils.safeParseEventValue(e) })}
                />

                <FormGroup className="text-right">
                    <Button
                      data-test="js-confirm"
                      disabled={this.state.challenge != project.name}
                      className="btn btn-primary"
                    >
                        Confirm changes
                    </Button>
                </FormGroup>
            </form>
        );
    }
};

ConfirmHideFlags.propTypes = {};

module.exports = ConfirmHideFlags;
