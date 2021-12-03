import React, { Component } from 'react';
import Select from 'react-select';

const EnvironmentSelect = class extends Component {
    static displayName = 'EnvironmentSelect'

    constructor(props, context) {
        super(props, context);
        this.state = {};
    }

    render() {
        return (
            <ProjectProvider id={this.props.projectId}>
                {({ isLoading, project }) => {
                    const selectedEnv = this.props.value && _.find(project.environments, { api_key: this.props.value });
                    if (this.props.readOnly) {
                        return (
                            <div className="mb-2">
                                {selectedEnv && selectedEnv.name}
                            </div>
                        );
                    }
                    return (
                        <div>
                            <Select
                              onChange={env => this.props.onChange(env.value)}
                              options={project.environments && project.environments.map(env => ({ label: env.name, value: env.api_key })).filter(v => {
                                  return v.value !== this.props.ignoreAPIKey
                              })}
                              value={selectedEnv ? {
                                  label: selectedEnv.name,
                                  value: selectedEnv.api_key,
                              } : {
                                  label: 'Please select an environment',
                              }}
                            />
                        </div>
                    );
                }}
            </ProjectProvider>
        );
    }
};

EnvironmentSelect.propTypes = {};

module.exports = EnvironmentSelect;
