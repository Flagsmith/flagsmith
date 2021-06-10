import React, { Component } from 'react';

const EnvironmentSelect = class extends Component {
  static displayName = 'EnvironmentSelect'

  constructor(props, context) {
      super(props, context);
      this.state = {};
  }

  render() {
      const { hasFeature } = this.props;

      return (
          <ProjectProvider id={this.props.projectId}>
              {({ isLoading, project }) => (
                  <div className={`fade ${isLoading ? '' : 'in'}`}>

                      {!isLoading && (
                      <ul id="env-list" className="project-list list-unstyled">
                          {project && project.environments && project.environments.map(environment => this.props.renderRow(environment,
                              () => {
                                  if (this.props.environmentId !== environment.api_key) {
                                      this.props.onChange && this.props.onChange(environment.api_key);
                                  }
                              }))
                }
                      </ul>
                      )}

                  </div>
              )}
          </ProjectProvider>
      );
  }
};

EnvironmentSelect.propTypes = {};

module.exports = ConfigProvider(EnvironmentSelect);
