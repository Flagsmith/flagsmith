import React, { Component } from 'react';

const ConfirmToggleFeature = class extends Component {
    static displayName = 'ConfirmToggleFeature'

    constructor(props, context) {
        super(props, context);
        this.state = {
            name: props.name,
        };
    }

    close() {
        closeModal();
    }

    render() {
        const { environmentFlag, projectFlag, identity } = this.props;
        const isEnabled = !!(environmentFlag && environmentFlag.enabled);
        return (
            <ProjectProvider>
                {({ project }) => (
                    <div id="confirm-toggle-feature-modal">
                        <p>
                            This will
                            turn
                            {' '}
                            <strong>{Format.enumeration.get(projectFlag.name)}</strong>
                            {' '}
                            {isEnabled ? <span className="feature--off"><strong>"Off"</strong></span>
                                : <span className="feature--on"><strong>"On"</strong></span>}
                            {' '}
                            for
                            <br/>
                            <strong>{_.find(project.environments, { api_key: this.props.environmentId }).name}</strong>
                            {identity && (
                                <span>
                                    {' '}
                                    user
                                    {' '}
                                    <strong>{this.props.identityName}.</strong>
                                    {' Any segment overrides for this feature will now be ignored.'}
                                </span>
                            )}
                        </p>
                        <FormGroup className="text-right">
                            <Button
                              onClick={() => {
                                  this.close();
                                  this.props.cb(this.state.allEnvironments ? project.environments : [_.find(project.environments, { api_key: this.props.environmentId })]);
                              }} className="btn btn-primary" id="confirm-toggle-feature-btn"
                            >
                                Confirm changes
                            </Button>
                        </FormGroup>
                    </div>
                )}
            </ProjectProvider>
        );
    }
};

ConfirmToggleFeature.propTypes = {};

module.exports = ConfirmToggleFeature;
